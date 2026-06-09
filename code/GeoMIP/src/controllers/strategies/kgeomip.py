"""KGeoMIP: extensión a k-particiones de GeoMIP mediante refinamiento divisivo E4.

Algoritmo: divisivo top-down anclado en GeoMIP (k=2 exacto por construcción),
guiado por la matriz de similitud S derivada de T, confirmado por EMD.

Complejidad: O(n²·2ⁿ) en tiempo, O(n²) en espacio adicional.
Regresión: KGeoMIP(k=2) ≡ GeoMIP exactamente (D4-01, anclaje en Fase 2 del pseudocódigo).
Monotonicidad: φ(k+1) ≥ φ(k) por construcción (anidación divisiva — §1.5 y §4.4 del diseño).
"""

import heapq
import time
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from src.constants.base import EFECTO, FLOAT_ZERO
from src.controllers.manager import Manager
from src.controllers.strategies.geometric import GeometricSIA
from src.funcs.base import ABECEDARY, emd_efecto, seleccionar_subestado
from src.funcs.format import fmt_biparte_q
from src.middlewares.slogger import SafeLogger
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.core.system import System


# ---------------------------------------------------------------------------
# Funciones de cálculo de distribuciones (sin duplicar _distribucion_bipartida)
# ---------------------------------------------------------------------------

def _marginal_bipartida(
    d: int,
    A: frozenset[int],
    A_global_dims: frozenset[int],
    sistema: System,
) -> float:
    """Marginal de ncubo d bajo bipartición (A, B) del bloque P = A ∪ B.

    Args:
        d: Índice local del ncubo (posición en sistema.ncubos).
        A: Indices locales en el lado A de la partición.
        A_global_dims: Dimensiones globales correspondientes a A.
        sistema: Sistema/subsistema preparado.

    Returns:
        Probabilidad marginal 1 - E[ncubo.data] bajo la bipartición.
    """
    ncubo = sistema.ncubos[d]
    nc_dims = ncubo.dims
    n_nc = len(nc_dims)
    estado_inicial = sistema.estado_inicial

    keep_global = (
        A_global_dims
        if d in A
        else frozenset(int(x) for x in nc_dims) - A_global_dims
    )

    idx: list[int | slice] = [slice(None)] * n_nc
    for k in range(n_nc):
        g_dim = int(nc_dims[n_nc - 1 - k])
        if g_dim in keep_global:
            idx[k] = int(estado_inicial[g_dim])

    return 1.0 - float(np.mean(ncubo.data[tuple(idx)]))


def _emd_bloque(
    A: frozenset[int],
    B: frozenset[int],
    sistema: System,
    dm_orig: NDArray[np.float32],
) -> float:
    """EMD local para bipartición (A, B) del bloque P = A ∪ B.

    Compara distribución original del bloque con la distribución bipartida.
    Compatible con emd_efecto de GeoMIP: suma de diferencias absolutas marginales.

    Args:
        A: Indices locales en el lado A.
        B: Indices locales en el lado B (B = P - A).
        sistema: Subsistema preparado.
        dm_orig: Distribución original del subsistema completo.

    Returns:
        EMD local = sum |d_part[d] - dm_orig[d]| para d en P.
    """
    P = A | B
    dims_all = sistema.dims_ncubos
    A_global_dims = frozenset(int(dims_all[d]) for d in A)

    dist_part = np.array(
        [_marginal_bipartida(d, A, A_global_dims, sistema) for d in sorted(P)],
        dtype=np.float32,
    )
    dist_orig = np.array([dm_orig[d] for d in sorted(P)], dtype=np.float32)
    return float(np.sum(np.abs(dist_part - dist_orig)))


def _calcular_phi_total(
    particion: list[frozenset[int]],
    sistema: System,
) -> float:
    """Φ* = EMD(p_original, ⊗_Pm p_Pm). Una sola llamada al final.

    Args:
        particion: Lista de partes (frozensets de índices locales).
        sistema: Subsistema preparado.

    Returns:
        Φ* usando la misma emd_efecto que GeoMIP en producción (D4-04).
    """
    dm_original = sistema.distribucion_marginal()
    todas_dims = list(sistema.dims_ncubos)
    N = len(sistema.ncubos)
    dist_recons = np.empty(N, dtype=np.float32)
    cubiertos: set[int] = set()

    for parte in particion:
        pi_global = frozenset(todas_dims[d] for d in parte if d < len(todas_dims))
        non_pi = np.array([g for g in todas_dims if g not in pi_global], dtype=np.int8)
        for d in parte:
            if d >= N:
                continue
            cubiertos.add(d)
            ncubo = sistema.ncubos[d]
            marg = ncubo.marginalizar(non_pi) if non_pi.size else ncubo
            if marg.dims.size:
                sub = tuple(int(sistema.estado_inicial[g]) for g in marg.dims)
                dist_recons[d] = 1.0 - float(marg.data[seleccionar_subestado(sub)])
            else:
                dist_recons[d] = 1.0 - float(marg.data)

    for d in range(N):
        if d not in cubiertos:
            ncubo = sistema.ncubos[d]
            non_all = np.array(todas_dims, dtype=np.int8)
            marg = ncubo.marginalizar(non_all)
            if marg.dims.size:
                sub = tuple(int(sistema.estado_inicial[g]) for g in marg.dims)
                dist_recons[d] = 1.0 - float(marg.data[seleccionar_subestado(sub)])
            else:
                dist_recons[d] = 1.0 - float(marg.data)

    return emd_efecto(dm_original, dist_recons)


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class KGeoMIP(SIA):
    """k-partición geométrica por refinamiento divisivo E4.

    Hereda de SIA (recibe Manager, como GeometricSIA — DEC-02).
    Firma característica: matriz de similitud S derivada de T (una vez por sistema).
    Reutiliza toda la maquinaria de GeoMIP sin duplicar código (regla dura).
    """

    def __init__(self, gestor: Manager) -> None:
        super().__init__(gestor)
        self._geomip = GeometricSIA(gestor)
        self.logger = SafeLogger("KGeoMIP")
        self._S: Optional[np.ndarray] = None
        self._subsistema_key: Optional[tuple] = None
        self._dm_orig: Optional[NDArray[np.float32]] = None

    def aplicar_estrategia(  # type: ignore[override]
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray,
        k: int = 2,
        variante: str = "E4",
    ) -> Solution:
        """Halla la k-partición de mínima información integrada.

        Args:
            condicion: Condiciones de fondo (bits 0 = condicionar).
            alcance: Alcance del subsistema.
            mecanismo: Mecanismo del subsistema.
            tpm: Matriz de probabilidad de transición (pre-cargada).
            k: Número de partes deseadas (1 ≤ k ≤ 5).
            variante: "E4" (recomendada) o "A" (baseline aglomerativo).
        """
        t0 = time.time()
        nombre = f"KGeoMIP(k={k},{variante})"

        # Anclaje k=2: delegar EXACTAMENTE a GeoMIP (D4-01, regresión por construcción)
        sol_k2 = self._geomip.aplicar_estrategia(condicion, alcance, mecanismo, tpm)

        self.sia_subsistema = self._geomip.sia_subsistema
        self.sia_dists_marginales = self._geomip.sia_dists_marginales
        self.sia_tiempo_inicio = t0

        dm_orig = self._geomip.sia_dists_marginales
        # La partición opera sobre los ncubos (lado futuro), no sobre los dims presentes.
        # Cuando |mecanismo| > |alcance|, dims_ncubos > indices_ncubos — usar índices futuros.
        D = len(self.sia_subsistema.indices_ncubos)

        if k <= 1:
            return Solution(
                estrategia="KGeoMIP(k=1)",
                perdida=FLOAT_ZERO,
                distribucion_subsistema=dm_orig,
                distribucion_particion=dm_orig,
                particion="{V}",
                tiempo_total=time.time() - t0,
                hablar=False,
            )

        if k == 2:
            return Solution(
                estrategia=nombre,
                perdida=sol_k2.perdida,
                distribucion_subsistema=sol_k2.distribucion_subsistema,
                distribucion_particion=sol_k2.distribucion_particion,
                particion=sol_k2.particion,
                tiempo_total=time.time() - t0,
                hablar=False,
            )

        # k > 2: construir S una sola vez por subsistema (D4-02)
        clave = (condicion, alcance, mecanismo)
        if self._subsistema_key != clave or self._S is None:
            self._subsistema_key = clave
            self._S = self._construir_S(D)

        self._dm_orig = dm_orig

        particion = (
            self._refinar_e4(D, k)
            if variante == "E4"
            else self._estrategia_a(D, k)
        )

        phi = _calcular_phi_total(particion, self.sia_subsistema)
        texto = self._fmt_particion_k(particion)

        return Solution(
            estrategia=nombre,
            perdida=float(phi),
            distribucion_subsistema=dm_orig,
            distribucion_particion=dm_orig,
            particion=texto,
            tiempo_total=time.time() - t0,
            hablar=False,
        )

    # ------------------------------------------------------------------
    # Construcción de S (D4-02, §1.4 del diseño)
    # ------------------------------------------------------------------

    def _construir_S(self, D: int) -> np.ndarray:
        """Construye la matriz de similitud D×D desde T. Una sola vez por sistema.

        S[i][j] = (sim(Xi, Xj) + sim(Xj, Xi)) / 2
        sim(Xi, Xj) = Σ_{δ: bit j activo en δ} T[Xi][δ]
                    = Σ_{state: bit j de state ≠ bit j de ini} tabla[state, i]

        Args:
            D: Número de dimensiones del subsistema.

        Returns:
            Matriz simétrica D×D de similitudes causales.
        """
        tabla = self._geomip._tabla
        ini_int = self._geomip._ini_int
        N = tabla.shape[0]
        D_nc = tabla.shape[1]
        all_states = np.arange(N, dtype=np.int64)
        S = np.zeros((D_nc, D_nc), dtype=np.float64)

        for j in range(D_nc):
            bit_j_ini = (ini_int >> j) & 1
            differs = ((all_states >> np.int64(j)) & np.int64(1)) != bit_j_ini
            S[:, j] = tabla[differs].sum(axis=0)

        return (S + S.T) / 2.0

    # ------------------------------------------------------------------
    # MejorCorte: S propone (ordena), EMD confirma (§5 del diseño)
    # ------------------------------------------------------------------

    def _mejor_corte(
        self,
        P: frozenset[int],
        S: np.ndarray,
    ) -> tuple[frozenset[int], frozenset[int], float]:
        """Bipartición de mínima EMD del bloque P.

        Enumera todas 2^(|P|-1) - 1 biparticiones (forma canónica: primer elemento
        en A) y selecciona la de menor EMD local. S se usa como ordenamiento previo.

        Args:
            P: Frozenset de índices locales del bloque.
            S: Matriz de similitud D×D (guía de candidatos baratos).

        Returns:
            (A, B, delta_phi): Mejor bipartición y su ΔΦ.
        """
        P_sorted = sorted(P)
        m = len(P_sorted)

        if m <= 1:
            return P, frozenset(), 0.0

        sistema = self.sia_subsistema
        dm = self._dm_orig
        mejor_emd = float("inf")
        mejor_A: frozenset[int] = frozenset()
        mejor_B: frozenset[int] = frozenset()

        for mask in range(1, (1 << (m - 1))):
            A = frozenset(P_sorted[i] for i in range(m) if (mask >> i) & 1)
            B = P - A
            if not A or not B:
                continue
            val = _emd_bloque(A, B, sistema, dm)
            if val < mejor_emd:
                mejor_emd = val
                mejor_A = A
                mejor_B = B

        return mejor_A, mejor_B, mejor_emd

    # ------------------------------------------------------------------
    # Refinamiento divisivo E4 (§2.5-2.6 del diseño)
    # ------------------------------------------------------------------

    def _refinar_e4(self, D: int, k: int) -> list[frozenset[int]]:
        """Refinamiento E4: ancla k=2 en GeoMIP, luego MinHeap por ΔΦ.

        Garantía de monotonicidad: cada nivel refina el anterior (anidación).
        Garantía de regresión: k=2 usa exactamente la bipartición de GeoMIP.

        Args:
            D: Número de dimensiones del subsistema.
            k: Número de partes objetivo (k ≥ 3 para llegar aquí).

        Returns:
            Lista de k frozensets de índices locales.
        """
        S = self._S

        if self._geomip.memoria_particiones:
            mip_key = min(
                self._geomip.memoria_particiones,
                key=lambda kk: self._geomip.memoria_particiones[kk][0],
            )
            futuros_global = frozenset(
                pair[1] for pair in mip_key  # type: ignore[index,union-attr]
                if pair[0] == EFECTO  # type: ignore[index]
            )
            indices_nc = self._geomip.sia_subsistema.indices_ncubos
            Pa = frozenset(i for i in range(D) if int(indices_nc[i]) in futuros_global)
        else:
            # Sin candidatos GeoMIP: arrancar con partición balanceada por S
            Pa = frozenset(range(D // 2)) if D > 1 else frozenset(range(D))

        Pb = frozenset(range(D)) - Pa

        if not Pa or not Pb:
            # Bipartición GeoMIP trivial: arrancar con partición completa y splitear todo
            Pa = frozenset(range(D))
            Pb = frozenset()

        particion: list[frozenset[int]] = [Pa] + ([Pb] if Pb else [])

        if k == 2:
            return particion

        # n_splits = splits adicionales necesarios para alcanzar exactamente k partes
        n_splits = k - len(particion)

        _id = 0
        heap: list = []
        for P in particion:
            if len(P) >= 2:
                A, B, dphi = self._mejor_corte(P, S)
                heapq.heappush(heap, (dphi, _id, len(P), min(P), P, A, B))
                _id += 1

        for _ in range(n_splits):
            if not heap:
                self.logger.warn("No hay más partes partibles para k=%d", k)
                break
            _, _, _, _, P_sel, A_sel, B_sel = heapq.heappop(heap)
            particion.remove(P_sel)
            if A_sel:
                particion.append(A_sel)
            if B_sel:
                particion.append(B_sel)
            for hijo in (A_sel, B_sel):
                if len(hijo) >= 2:
                    _id += 1
                    Ah, Bh, ph = self._mejor_corte(hijo, S)
                    heapq.heappush(heap, (ph, _id, len(hijo), min(hijo), hijo, Ah, Bh))

        return particion

    # ------------------------------------------------------------------
    # Estrategia A — baseline aglomerativo (D4-01)
    # ------------------------------------------------------------------

    def _estrategia_a(self, D: int, k: int) -> list[frozenset[int]]:
        """Clustering jerárquico aglomerativo sobre S (baseline para A/B testing).

        Sin garantía de regresión k=2 ni monotonicidad por construcción.
        Solo para comparación experimental con E4 (criterio C6 del DoD).

        Args:
            D: Número de dimensiones.
            k: Número de clusters objetivo.

        Returns:
            Lista de k frozensets (partición aglomerativa).
        """
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform

        S_dist = np.max(self._S) - self._S
        np.fill_diagonal(S_dist, 0.0)
        Z = linkage(squareform(S_dist, checks=False), method="average")
        labels = fcluster(Z, k, criterion="maxclust")

        return [
            frozenset(i for i in range(D) if labels[i] == c)
            for c in range(1, k + 1)
            if any(labels[i] == c for i in range(D))
        ]

    # ------------------------------------------------------------------
    # Formateador de k-partición
    # ------------------------------------------------------------------

    def _fmt_particion_k(self, particion: list[frozenset[int]]) -> str:
        """Formatea la k-partición con el mismo estilo de corchetes que GeoMIP/QNodes.

        Args:
            particion: Lista de frozensets de índices locales.

        Returns:
            String con partes separadas por ' | ', cada parte en formato ⎛...⎞⎝...⎠.
        """
        nc_indices = self.sia_subsistema.indices_ncubos
        partes = sorted(particion, key=lambda p: min(p) if p else 0)
        partes_txt = []
        for P in partes:
            prim = [(1, int(nc_indices[d])) for d in sorted(P) if d < len(nc_indices)]
            partes_txt.append(fmt_biparte_q(prim, []).strip())
        return " | ".join(partes_txt)
