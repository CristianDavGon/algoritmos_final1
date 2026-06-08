"""KQNodes: extensión a k-particiones de QNodes mediante refinamiento iterativo greedy.

Algoritmo: bipartición iterativa con criterio C4 (corte marginal mínimo).
Complejidad: O(k·D³) en tiempo, O(k·D²) en espacio.
Regresión: KQNodes(k=2) ≡ QNodes exactamente (DB-03.1).
"""

import heapq
import time
from typing import Callable

import numpy as np

from src.constants.base import FLOAT_ZERO, INFTY_POS
from src.funcs.iit import emd_efecto, seleccionar_estado
from src.funcs.format import fmt_biparticion_q as fmt_basic
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.core.system import System
from src.strategies.qnodes import oracle, qnodes


# ---------------------------------------------------------------------------
# Oracle restringido con caché local (DB-D3-02)
# ---------------------------------------------------------------------------

def _oracle_restringido(
    bloque: frozenset[int],
    N: int,
    D_global: int,
    data_nd: np.ndarray,
    pivot_idx: tuple[int, ...],
    pivot_vals: np.ndarray,
) -> tuple[Callable[[int], float], int]:
    """Oracle restringido al bloque con caché LOCAL (se reinicia por bloque).

    Args:
        bloque: Índices globales locales {0..D-1} que forman el bloque Pi.
        N: Número de nodos del sistema.
        D_global: Dimensiones totales del subsistema.
        data_nd: TPM nd-array (N, 2, ..., 2).
        pivot_idx: Estado pivote en orden LIL_ENDIAN (D entradas, índice=[dim_D-1..dim_0]).
        pivot_vals: Distribución marginal del pivote (tamaño N).

    Returns:
        (f_local, full_mask_local): función oracle y máscara completa del bloque.
    """
    indices_gl = sorted(bloque)
    m = len(indices_gl)
    full_mask_local = (1 << m) - 1

    _means_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def __means(mask_local: int) -> tuple[np.ndarray, np.ndarray]:
        if mask_local in _means_cache:
            return _means_cache[mask_local]
        comp_local = full_mask_local ^ mask_local

        # Construir slices: dims en bloque según máscara local, resto fijo en pivot
        # pivot_idx está en orden [D-1 .. 0] (LIL_ENDIAN dentro de data_nd)
        slc_a: list[slice | int] = [slice(None)]
        slc_b: list[slice | int] = [slice(None)]
        local_bit = 0
        for d in range(D_global):
            piv_ax = pivot_idx[D_global - 1 - d]  # eje LIL_ENDIAN
            if d in bloque:
                in_a = bool((mask_local >> local_bit) & 1)
                in_b = bool((comp_local >> local_bit) & 1)
                slc_a.append(slice(None) if in_a else piv_ax)
                slc_b.append(slice(None) if in_b else piv_ax)
                local_bit += 1
            else:
                slc_a.append(piv_ax)
                slc_b.append(piv_ax)

        mean_a = data_nd[tuple(slc_a)].reshape(N, -1).mean(axis=1)
        mean_b = data_nd[tuple(slc_b)].reshape(N, -1).mean(axis=1)
        _means_cache[mask_local] = (mean_a, mean_b)
        _means_cache[comp_local] = (mean_b, mean_a)
        return mean_a, mean_b

    def f_local(mask_local: int) -> float:
        if mask_local == 0 or mask_local == full_mask_local:
            return 0.0
        mean_a, mean_b = __means(mask_local)
        return float(np.minimum(np.abs(mean_b - pivot_vals), np.abs(mean_a - pivot_vals)).sum())

    return f_local, full_mask_local


def _qnodes_sobre_bloque(
    bloque: frozenset[int],
    N: int,
    D_global: int,
    data_nd: np.ndarray,
    pivot_idx: tuple[int, ...],
    pivot_vals: np.ndarray,
) -> tuple[frozenset[int], frozenset[int], float]:
    """Ejecuta QNodes sobre el bloque con oracle restringido y caché local.

    Returns:
        (A, B, phi_local): bipartición óptima (dim indices locales) y su costo.
    """
    indices_gl = sorted(bloque)
    m = len(indices_gl)
    if m <= 1:
        return bloque, frozenset(), 0.0

    f_local, full_mask_local = _oracle_restringido(
        bloque, N, D_global, data_nd, pivot_idx, pivot_vals
    )
    phi_local, best_mask_local = qnodes(m, f_local, full_mask_local)

    A = frozenset(indices_gl[r] for r in range(m) if (best_mask_local >> r) & 1)
    B = bloque - A
    return A, B, phi_local


# ---------------------------------------------------------------------------
# Cálculo de Φ* (una sola vez al final)
# ---------------------------------------------------------------------------

def _calcular_phi_total(
    particion: list[frozenset[int]],
    sistema: System,
) -> float:
    """Φ* = EMD(p(s_{t+1}), ⊗_{Pi} p_{Pi}). Una sola llamada al final.

    Para cada nodo d en parte Pi: su valor reconstruido = marginal de ncubos[d]
    sobre los dims de la parte Pi (NCube.marginalizar elimina dims fuera de Pi).
    Cuando N > D_part los ncubos sin parte asignada se tratan como singletons.
    """
    dm_original = sistema.distribucion_marginal()
    todas_dims = list(sistema.dims_ncubos)  # global dim indices ordenados
    N = len(sistema.ncubos)
    dist_recons = np.empty(N, dtype=np.float32)

    # Índices de ncubos cubiertos por la partición (d < N siempre por _buscar_particion)
    cubiertos: set[int] = set()
    for parte in particion:
        pi_global = {todas_dims[d] for d in parte if d < len(todas_dims)}
        non_pi_global = np.array(
            [g for g in todas_dims if g not in pi_global], dtype=np.int8
        )
        for d in parte:
            if d >= N:
                continue  # salvaguarda: dim sin ncubo correspondiente
            cubiertos.add(d)
            ncubo = sistema.ncubos[d]
            marg = ncubo.marginalizar(non_pi_global) if non_pi_global.size else ncubo
            if marg.dims.size:
                pivot = seleccionar_estado(
                    np.array([sistema.estado_inicial[g] for g in marg.dims], dtype=np.int8)
                )
                dist_recons[d] = float(marg.data[tuple(pivot)])
            else:
                dist_recons[d] = float(marg.data)

    # Ncubos no cubiertos (N > D_part): singleton — todas las dims son "non_pi"
    for d in range(N):
        if d in cubiertos:
            continue
        ncubo = sistema.ncubos[d]
        non_all = np.array(todas_dims, dtype=np.int8)
        marg = ncubo.marginalizar(non_all)
        dist_recons[d] = float(marg.data) if not marg.dims.size else float(
            marg.data[tuple(seleccionar_estado(
                np.array([sistema.estado_inicial[g] for g in marg.dims], dtype=np.int8)
            ))]
        )

    return emd_efecto(dm_original, dist_recons)


# ---------------------------------------------------------------------------
# Clase principal KQNodes
# ---------------------------------------------------------------------------

class KQNodes(SIA):
    """k-partición submodular por refinamiento iterativo greedy con criterio C4.

    Criterio C4 (corte marginal mínimo): en cada paso selecciona la parte
    cuyo mejor corte interno tiene el menor costo (φ_local mínimo).
    Reutiliza oracle() y qnodes() de qnodes.py sin duplicar código.
    """

    def aplicar_estrategia(  # type: ignore[override]
        self,
        estado_inicial: str,
        condicion: str,
        alcance: str,
        mecanismo: str,
        k: int = 2,
        criterio: str = "C4",
    ) -> Solution:
        """Halla la k-partición de mínima información integrada.

        Args:
            estado_inicial: Estado inicial del sistema.
            condicion: Condiciones de fondo.
            alcance: Alcance del subsistema.
            mecanismo: Mecanismo del subsistema.
            k: Número de partes deseadas (2 ≤ k ≤ 5).
            criterio: "C4" (corte mínimo) o "C1" (tamaño máximo).
        """
        self.sia_preparar_subsistema(estado_inicial, condicion, alcance, mecanismo)
        self.sistema = self.sia_subsistema
        self.distribucion = self.sia_dists_marginales
        self.nombre = f"{self.__class__.__name__}(k={k},{criterio})"
        return self._resolver(k, criterio)

    def _resolver(self, k: int, criterio: str) -> Solution:
        t0 = time.perf_counter()
        dm_original = self.distribucion
        sistema = self.sistema

        if not sistema.indices_ncubos.size or not sistema.dims_ncubos.size:
            return Solution(
                estrategia=self.nombre,
                perdida=FLOAT_ZERO,
                distribucion_subsistema=dm_original,
                distribucion_particion=dm_original,
                particion="∅",
                tiempo_total=time.perf_counter() - t0,
                quiere_hablar=False,
            )

        if k == 2:
            # Replicación exacta de QNodes para garantizar regresión DB-03.1
            alcance_w, mec_w = self._winner_k2(sistema)
            arr_alc = np.array(list(alcance_w), dtype=np.int8)
            arr_mec = np.array(list(mec_w), dtype=np.int8)
            dm_part = sistema.bipartir(arr_alc, arr_mec).distribucion_marginal()
            phi = emd_efecto(dm_part, dm_original)
            texto = self._fmt_biparticion(alcance_w, mec_w, sistema)
        else:
            particion = self._buscar_particion(k, criterio)
            phi = _calcular_phi_total(particion, sistema)
            texto = self._fmt_particion_k(particion)

        return Solution(
            estrategia=self.nombre,
            perdida=float(phi),
            distribucion_subsistema=dm_original,
            distribucion_particion=dm_original,
            particion=texto,
            tiempo_total=time.perf_counter() - t0,
            quiere_hablar=False,
        )

    # ------------------------------------------------------------------
    # Winner k=2 (replicación de QNodes.winner para regresión exacta)
    # ------------------------------------------------------------------

    def _winner_k2(
        self, sistema: System
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Replicación de QNodes.winner() para garantía de regresión k=2."""
        D = len(sistema.dims_ncubos)
        N = len(sistema.ncubos)
        data_nd = np.stack([c.data for c in sistema.ncubos])
        pivot_idx = tuple(int(sistema.estado_inicial[dim]) for dim in sistema.dims_ncubos)
        pivot_vals = data_nd[(slice(None),) + pivot_idx[::-1]]

        all_mean = data_nd.reshape(N, -1).mean(axis=1)
        conc_costs = np.abs(all_mean - pivot_vals)
        conc_idx = int(np.argmin(conc_costs))
        C_conc = float(conc_costs[conc_idx])

        if D <= 1:
            return (sistema.ncubos[conc_idx].indice,), ()

        full_mask = (1 << D) - 1
        f, means_fn = oracle(N, D, data_nd, pivot_idx, pivot_vals, full_mask)
        best_val, best_mask_a = qnodes(D, f, full_mask)

        if C_conc <= best_val:
            return (sistema.ncubos[conc_idx].indice,), ()

        mean_a, mean_b = means_fn(best_mask_a)
        node_in_a = np.abs(mean_b - pivot_vals) <= np.abs(mean_a - pivot_vals)
        alc = tuple(c.indice for i, c in enumerate(sistema.ncubos) if node_in_a[i])
        mec = tuple(sistema.dims_ncubos[d] for d in range(D) if (best_mask_a >> d) & 1)
        return alc, mec

    # ------------------------------------------------------------------
    # Búsqueda de k-partición (k ≥ 3)
    # ------------------------------------------------------------------

    def _buscar_particion(self, k: int, criterio: str) -> list[frozenset[int]]:
        sistema = self.sistema
        N = len(sistema.ncubos)
        D = len(sistema.dims_ncubos)
        data_nd = np.stack([c.data for c in sistema.ncubos])
        pivot_idx = tuple(int(sistema.estado_inicial[dim]) for dim in sistema.dims_ncubos)
        pivot_vals = data_nd[(slice(None),) + pivot_idx[::-1]]

        # Limitar la partición a min(N,D): cuando D>N, índices d>=N no tienen
        # ncubo correspondiente; cuando D<N, los ncubos extra se dejan sin partir.
        D_part = min(N, D)
        V = frozenset(range(D_part))
        if k <= 1 or D_part <= 1:
            return [V]

        if criterio == "C4":
            return self._refinar_c4(V, k, N, D, data_nd, pivot_idx, pivot_vals)
        return self._refinar_c1(V, k, N, D, data_nd, pivot_idx, pivot_vals)

    def _refinar_c4(
        self, V: frozenset[int], k: int,
        N: int, D: int, data_nd: np.ndarray,
        pivot_idx: tuple, pivot_vals: np.ndarray,
    ) -> list[frozenset[int]]:
        """Criterio C4: MinHeap por φ_local. ≤ 2k-1 llamadas a qnodes."""
        A0, B0, phi0 = _qnodes_sobre_bloque(V, N, D, data_nd, pivot_idx, pivot_vals)
        _id = 0
        heap: list = [(phi0, -len(V), _id, V, A0, B0)]
        particion: list[frozenset[int]] = [V]

        for _ in range(k - 1):
            if not heap:
                break
            phi_sel, _, _, P_sel, A_sel, B_sel = heapq.heappop(heap)
            particion.remove(P_sel)
            if A_sel:
                particion.append(A_sel)
            if B_sel:
                particion.append(B_sel)

            for hijo in (A_sel, B_sel):
                if len(hijo) >= 2:
                    _id += 1
                    Ah, Bh, phi_h = _qnodes_sobre_bloque(
                        hijo, N, D, data_nd, pivot_idx, pivot_vals
                    )
                    heapq.heappush(heap, (phi_h, -len(hijo), _id, hijo, Ah, Bh))

        return particion

    def _refinar_c1(
        self, V: frozenset[int], k: int,
        N: int, D: int, data_nd: np.ndarray,
        pivot_idx: tuple, pivot_vals: np.ndarray,
    ) -> list[frozenset[int]]:
        """Criterio C1: tamaño máximo. k-1 llamadas a qnodes."""
        particion: list[frozenset[int]] = [V]
        for _ in range(k - 1):
            P_sel = max(
                (p for p in particion if len(p) >= 2),
                key=lambda p: (len(p), -min(p)),
                default=None,
            )
            if P_sel is None:
                break
            A_sel, B_sel, _ = _qnodes_sobre_bloque(
                P_sel, N, D, data_nd, pivot_idx, pivot_vals
            )
            particion.remove(P_sel)
            if A_sel:
                particion.append(A_sel)
            if B_sel:
                particion.append(B_sel)
        return particion

    # ------------------------------------------------------------------
    # Formateadores
    # ------------------------------------------------------------------

    def _fmt_biparticion(
        self,
        alcance: tuple[int, ...],
        mec: tuple[int, ...],
        sistema: System,
    ) -> str:
        all_indices = list(sistema.indices_ncubos)
        all_dims = list(sistema.dims_ncubos)
        prim = [(1, idx) for idx in alcance] + [(0, dim) for dim in mec]
        dual = [(1, idx) for idx in all_indices if idx not in alcance] + [
            (0, dim) for dim in all_dims if dim not in mec
        ]
        return fmt_basic(prim, dual).strip()

    def _fmt_particion_k(self, particion: list[frozenset[int]]) -> str:
        sistema = self.sistema
        indices = list(sistema.indices_ncubos)
        partes_txt = []
        for parte in particion:
            alc = [indices[d] for d in sorted(parte) if d < len(indices)]
            prim = [(1, idx) for idx in alc]
            partes_txt.append(fmt_basic(prim, []).strip())
        return " | ".join(partes_txt)
