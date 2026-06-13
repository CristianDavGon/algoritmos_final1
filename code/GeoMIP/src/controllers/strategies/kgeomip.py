"""KGeoMIP: extensión a k-particiones de GeoMIP mediante refinamiento divisivo E4.

Algoritmo: divisivo top-down anclado en GeoMIP (k=2 exacto por construcción),
guiado por la matriz de similitud S derivada de T, confirmado por EMD.

Complejidad: O(n²·2ⁿ) en tiempo, O(n²) en espacio adicional.
Regresión: KGeoMIP(k=2) ≡ GeoMIP exactamente (D4-01, anclaje en Fase 2 del pseudocódigo).
Monotonicidad: φ(k+1) ≥ φ(k) por construcción (anidación divisiva — §1.5 y §4.4 del diseño).

Optimización D4-06 (2026-06-09):
    - ΔΦ incremental exacto: como emd_efecto = Σ_d |·|, Φ(Π) se descompone
      aditivamente por parte; el heap ordena por el incremento real de Φ.
    - Raíz consistente con el modelo k: la proyección del ancla GeoMIP se
      contrasta con el mejor corte directo bajo el mismo modelo.
    - Cachés: marginales por máscara de bits y solución GeoMIP k=2 por clave.
"""

import heapq
import time
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from src.constants.base import EFECTO, FLOAT_ZERO
from src.controllers.manager import Manager
from src.controllers.strategies.geometric import GeometricSIA
from src.controllers.strategies.kgeomip_cortes import (
    _UMBRAL_ENUMERACION,
    _calcular_phi_total,
    _candidatos_por_afinidad,
)
from src.funcs.format import fmt_biparte_q
from src.middlewares.slogger import SafeLogger
from src.models.base.sia import SIA
from src.models.core.solution import Solution


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class KGeoMIP(SIA):
    """k-partición geométrica por refinamiento divisivo E4.

    Hereda de SIA (recibe Manager, como GeometricSIA — DEC-02).
    Firma característica: matriz de similitud S derivada de T (una vez por sistema).
    Reutiliza toda la maquinaria de GeoMIP sin duplicar código (regla dura).

    `estrategia_corte` (D4-05, OPT-K1) controla cómo `_mejor_corte` elige la
    bipartición de cada bloque dentro de E4 (k ≥ 3):
        - "auto" (default): exhaustivo si el bloque es pequeño
          (2^(|P|−1) − 1 ≤ `_UMBRAL_ENUMERACION`), guiado_S si es grande.
          Preserva la exactitud por bloque donde el exhaustivo es viable y
          escala sin explosión exponencial donde no.
        - "exhaustivo": enumera todas las biparticiones, EMD decide.
        - "guiado_S": S propone candidatos por afinidad cruzada, EMD confirma.
    """

    _MAX_CANDIDATOS_GUIADOS = 20

    def __init__(self, gestor: Manager) -> None:
        super().__init__(gestor)
        self._geomip = GeometricSIA(gestor)
        self.logger = SafeLogger("KGeoMIP")
        self._S: Optional[np.ndarray] = None
        self._subsistema_key: Optional[tuple] = None
        self._dm_orig: Optional[NDArray[np.float32]] = None
        self._sol_k2: Optional[Solution] = None
        self._marg_cache: dict[int, NDArray[np.float64]] = {}
        self._costo_cache: dict[frozenset[int], float] = {}
        self._flat_nd: Optional[np.ndarray] = None
        self._dm_orig64: Optional[NDArray[np.float64]] = None
        self.estrategia_corte: str = "auto"

    def aplicar_estrategia(  # type: ignore[override]
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray,
        k: int = 2,
        variante: str = "E4",
        estrategia_corte: str = "auto",
    ) -> Solution:
        """Halla la k-partición de mínima información integrada.

        GeoMIP (ancla k=2) corre una sola vez por clave (condicion, alcance,
        mecanismo); los barridos k=1..5 sobre la misma clave reutilizan la
        solución y los cachés (D4-02/D4-06).

        Args:
            condicion: Condiciones de fondo (bits 0 = condicionar).
            alcance: Alcance del subsistema.
            mecanismo: Mecanismo del subsistema.
            tpm: Matriz de probabilidad de transición (pre-cargada).
            k: Número de partes deseadas (1 ≤ k ≤ 5).
            variante: "E4" (recomendada) o "A" (baseline aglomerativo).
            estrategia_corte: "auto" (exhaustivo en bloques pequeños,
                guiado_S en bloques grandes — OPT-K1), "exhaustivo" (enumera
                todas las biparticiones de cada bloque) o "guiado_S" (S
                propone candidatos por afinidad cruzada, EMD confirma el
                mejor). Solo afecta a E4 para k ≥ 3 (D4-05).
        """
        t0 = time.time()
        nombre = f"KGeoMIP(k={k},{variante})"
        self.estrategia_corte = estrategia_corte

        # Anclaje k=2: delegar EXACTAMENTE a GeoMIP (D4-01); una vez por clave
        clave = (condicion, alcance, mecanismo)
        if clave != self._subsistema_key or self._sol_k2 is None:
            self._sol_k2 = self._geomip.aplicar_estrategia(
                condicion, alcance, mecanismo, tpm
            )
            self._subsistema_key = clave
            self._S = None
            self._marg_cache = {}
            self._costo_cache = {}
            self._flat_nd = None
            self._dm_orig64 = None
        sol_k2 = self._sol_k2

        self.sia_subsistema = self._geomip.sia_subsistema
        self.sia_dists_marginales = self._geomip.sia_dists_marginales
        self.sia_tiempo_inicio = t0

        dm_orig = self._geomip.sia_dists_marginales
        self._dm_orig = dm_orig
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
        if self._S is None:
            self._S = self._construir_S(D)

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
        S = np.zeros((D_nc, D_nc), dtype=np.float64)

        # S[i, j] = Σ_s tabla[s, i] · [bit j de s ≠ bit j de ini] — un producto
        # matricial por chunk de estados (OPT-K3), en vez de D escaneos
        # booleanos completos. La memoria temporal queda acotada por chunk.
        bits_j = np.arange(D_nc, dtype=np.int64)
        ini_bits = (np.int64(ini_int) >> bits_j) & np.int64(1)
        chunk = min(N, 1 << 16)
        for inicio in range(0, N, chunk):
            fin = min(inicio + chunk, N)
            estados = np.arange(inicio, fin, dtype=np.int64)
            difiere = (((estados[:, None] >> bits_j) & np.int64(1)) != ini_bits)
            S += tabla[inicio:fin].T.astype(np.float64) @ difiere.astype(np.float64)

        return (S + S.T) / 2.0

    # ------------------------------------------------------------------
    # ΔΦ incremental exacto vía marginales por máscara (D4-06)
    # ------------------------------------------------------------------

    def _vista_flat_nd(self) -> np.ndarray:
        """Vista (sin copia) de `_flat_T` con forma (2, ..., 2, n_ncubos).

        El eje D−1−j corresponde al bit j del estado (layout little-endian de
        las filas de `_flat_T`); el último eje es el ncubo. Permite
        marginalizar fijando ejes por indexación básica en O(2^(D−|mask|)) en
        lugar de escanear los 2^D estados con una máscara booleana (OPT-K2).

        Returns:
            Vista n-dimensional sobre los datos aplanados de GeoMIP.
        """
        if self._flat_nd is None:
            flat_T = self._geomip._flat_T
            D = len(self.sia_subsistema.dims_ncubos)
            self._flat_nd = flat_T.reshape(*([2] * D), flat_T.shape[1])
        return self._flat_nd

    def _marginales_mascara(self, mask: int) -> NDArray[np.float64]:
        """Vector de marginales de todos los ncubos manteniendo los dims de `mask`.

        marg[d] = 1 − E[flat[d, s] : s ≡ estado_inicial sobre los bits de mask].
        Equivale a `NCube.marginalizar(dims fuera de mask)` + selección del
        subestado inicial, pero por indexación directa sobre la vista n-dim
        (costo O(2^(D−|mask|)) por miss — OPT-K2) y cacheado por máscara
        (los cortes repiten máscaras entre candidatos).

        Args:
            mask: Máscara de bits sobre posiciones locales de dims_ncubos.

        Returns:
            Vector (n_ncubos,) de probabilidades marginales OFF.
        """
        marg = self._marg_cache.get(mask)
        if marg is None:
            vista = self._vista_flat_nd()
            D = vista.ndim - 1
            n_nc = vista.shape[-1]
            ini_int = self._geomip._ini_int
            idx: list = [slice(None)] * (D + 1)
            for j in range(D):
                if (mask >> j) & 1:
                    idx[D - 1 - j] = (ini_int >> j) & 1
            sub = vista[tuple(idx)]
            marg = 1.0 - sub.reshape(-1, n_nc).mean(axis=0, dtype=np.float64)
            self._marg_cache[mask] = marg
        return marg

    def _costo_parte(self, Q: frozenset[int]) -> float:
        """Contribución exacta de la parte Q a Φ: Σ_{d∈Q} |dm_orig[d] − marg_d(Q)|.

        Cacheado por parte (OPT-K2): `_delta_phi_corte` repite las mismas
        partes entre candidatos y entradas del heap de E4.

        Args:
            Q: Parte (frozenset de índices locales de ncubos).

        Returns:
            Costo aditivo de Q bajo la métrica emd_efecto del proyecto.
        """
        if not Q:
            return 0.0
        costo = self._costo_cache.get(Q)
        if costo is not None:
            return costo
        n_dims = len(self.sia_subsistema.dims_ncubos)
        mask = 0
        for d in Q:
            if d < n_dims:
                mask |= 1 << d
        marg = self._marginales_mascara(mask)
        if self._dm_orig64 is None:
            self._dm_orig64 = np.asarray(self._dm_orig, dtype=np.float64)
        idx = sorted(Q)
        costo = float(np.sum(np.abs(self._dm_orig64[idx] - marg[idx])))
        self._costo_cache[Q] = costo
        return costo

    def _delta_phi_corte(self, A: frozenset[int], B: frozenset[int]) -> float:
        """ΔΦ exacto de cortar P = A ∪ B en (A, B).

        Como emd_efecto = Σ_d |·|, Φ(Π) se descompone aditivamente por parte:
        ΔΦ = costo(A) + costo(B) − costo(P). El heap de E4 ordena por este
        incremento real (criterio de corte marginal mínimo, DEC-12/DEC-14).

        Args:
            A: Lado A del corte.
            B: Lado B del corte.

        Returns:
            Incremento exacto de Φ al aplicar el corte.
        """
        return self._costo_parte(A) + self._costo_parte(B) - self._costo_parte(A | B)

    # ------------------------------------------------------------------
    # MejorCorte: S propone candidatos, EMD confirma (§5 del diseño, D4-05)
    # ------------------------------------------------------------------

    def _mejor_corte(
        self,
        P: frozenset[int],
        S: np.ndarray,
    ) -> tuple[frozenset[int], frozenset[int], float]:
        """Despacha a la estrategia de corte configurada (D4-05, OPT-K1).

        En modo "auto" el despacho es por tamaño de bloque: exhaustivo si
        2^(|P|−1) − 1 ≤ `_UMBRAL_ENUMERACION` (resultado idéntico al modo
        exhaustivo), guiado_S en caso contrario (escala sin explosión).

        Args:
            P: Frozenset de índices locales del bloque.
            S: Matriz de similitud D×D.

        Returns:
            (A, B, delta_phi): Mejor bipartición según la estrategia activa y su ΔΦ.
        """
        if self.estrategia_corte == "guiado_S":
            return self._mejor_corte_guiado_por_S(P, S)
        if self.estrategia_corte == "exhaustivo":
            return self._mejor_corte_exhaustivo(P, S)
        # "auto": exacto donde es barato, guiado donde explota
        if len(P) <= 1 or (1 << (len(P) - 1)) - 1 <= _UMBRAL_ENUMERACION:
            return self._mejor_corte_exhaustivo(P, S)
        return self._mejor_corte_guiado_por_S(P, S)

    def _mejor_corte_exhaustivo(
        self,
        P: frozenset[int],
        S: np.ndarray,
    ) -> tuple[frozenset[int], frozenset[int], float]:
        """Bipartición de mínimo ΔΦ del bloque P por enumeración completa.

        Enumera todas 2^(|P|-1) - 1 biparticiones (forma canónica: primer elemento
        en A) y selecciona la de menor incremento real de Φ. No utiliza S.

        Args:
            P: Frozenset de índices locales del bloque.
            S: Matriz de similitud D×D (sin uso; presente por compatibilidad
                de firma con `_mejor_corte_guiado_por_S`).

        Returns:
            (A, B, delta_phi): Mejor bipartición y su ΔΦ.
        """
        P_sorted = sorted(P)
        m = len(P_sorted)

        if m <= 1:
            return P, frozenset(), 0.0

        mejor_dphi = float("inf")
        mejor_A: frozenset[int] = frozenset()
        mejor_B: frozenset[int] = frozenset()

        for mask in range(1, (1 << (m - 1))):
            A = frozenset(P_sorted[i] for i in range(m) if (mask >> i) & 1)
            B = P - A
            if not A or not B:
                continue
            val = self._delta_phi_corte(A, B)
            if val < mejor_dphi:
                mejor_dphi = val
                mejor_A = A
                mejor_B = B

        return mejor_A, mejor_B, mejor_dphi

    def _mejor_corte_guiado_por_S(
        self,
        P: frozenset[int],
        S: np.ndarray,
    ) -> tuple[frozenset[int], frozenset[int], float]:
        """Bipartición de P guiada por S: S propone candidatos, EMD confirma.

        Genera como máximo `_MAX_CANDIDATOS_GUIADOS` candidatos ordenados por
        afinidad cruzada en S (`_candidatos_por_afinidad`) y evalúa el ΔΦ real
        solo sobre ellos. Para |P| pequeño (2^(|P|-1) - 1 ≤ _MAX_CANDIDATOS_GUIADOS)
        coincide exactamente con `_mejor_corte_exhaustivo`.

        Args:
            P: Frozenset de índices locales del bloque.
            S: Matriz de similitud D×D (guía de candidatos).

        Returns:
            (A, B, delta_phi): Mejor bipartición entre los candidatos y su ΔΦ.
        """
        if len(P) <= 1:
            return P, frozenset(), 0.0

        mejor_dphi = float("inf")
        mejor_A: frozenset[int] = frozenset()
        mejor_B: frozenset[int] = frozenset()

        for A, B in _candidatos_por_afinidad(P, S, self._MAX_CANDIDATOS_GUIADOS):
            val = self._delta_phi_corte(A, B)
            if val < mejor_dphi:
                mejor_dphi, mejor_A, mejor_B = val, A, B

        return mejor_A, mejor_B, mejor_dphi

    # ------------------------------------------------------------------
    # Refinamiento divisivo E4 (§2.5-2.6 del diseño)
    # ------------------------------------------------------------------

    def _refinar_e4(self, D: int, k: int) -> list[frozenset[int]]:
        """Refinamiento E4: ancla k=2 en GeoMIP, luego MinHeap por ΔΦ.

        Garantía de monotonicidad: cada nivel refina el anterior (anidación).
        Garantía de regresión: k=2 retorna la solución de GeoMIP (vía
        `aplicar_estrategia`, antes de llegar aquí). Para k ≥ 3 el corte raíz
        usa la proyección del ancla GeoMIP **solo si** es competitiva bajo el
        modelo k (D4-06): la proyección descarta el lado presente de la
        bipartición de GeoMIP y puede dejar el óptimo fuera del alcance del
        refinamiento divisivo; en ese caso gana el mejor corte directo
        (empate → ancla GeoMIP, D4-03).

        Args:
            D: Número de dimensiones del subsistema.
            k: Número de partes objetivo (k ≥ 3 para llegar aquí).

        Returns:
            Lista de k frozensets de índices locales.
        """
        S = self._S
        V = frozenset(range(D))

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
            Pa = frozenset(range(D // 2)) if D > 1 else V

        Pb = V - Pa

        if Pa and Pb:
            # Raíz consistente con el modelo k (D4-06)
            A_alt, B_alt, dphi_alt = self._mejor_corte(V, S)
            if B_alt and dphi_alt < self._delta_phi_corte(Pa, Pb) - 1e-12:
                Pa, Pb = A_alt, B_alt
        else:
            # Bipartición GeoMIP trivial: arrancar con partición completa y splitear todo
            Pa, Pb = V, frozenset()

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
