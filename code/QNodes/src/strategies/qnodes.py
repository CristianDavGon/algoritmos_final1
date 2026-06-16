"""Estrategia Queyranne: MIP via minimización de función submodular simétrica.

Implementa el algoritmo de Queyranne (Math. Prog. 1998): dada una función
simétrica f: 2^V → R, encuentra la bipartición de mínimo valor en
O(|V|³) evaluaciones al oracle, reemplazando la búsqueda exhaustiva
O(2^(D-1)) de la estrategia analítica.

Complejidad: O(D³·N) vs O(2^(D-1)·N) de la estrategia analítica.
El oracle se evalúa de forma lazy (con caché): solo O(D³) máscaras
distintas en lugar de los 2^D del precómputo completo. Speedup
teórico aproximado 2^D/D³.

Correctitud: garantizada si f es submodular. Empíricamente ~97-100 %
exacta para funciones análogas no-submodulares (Kitazono et al.,
Entropy 2018). El pre-pass de singletons cubre el caso más común de
falla no-submodular.

Typical usage example::

    estrategia = QNodes(tpm)
    solucion = estrategia.aplicar_estrategia(
        estado_inicial="100",
        condicion="111",
        alcance="110",
        mecanismo="101",
    )
    print(solucion.perdida)
"""

from __future__ import annotations

import time
from typing import Callable

import numpy as np

from src.constants.base import FLOAT_ZERO, INFTY_POS
from src.funcs.format import fmt_biparticion_q as fmt_basic
from src.funcs.iit import emd_efecto
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.core.system import System

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Valor centinela usado para inicializar la búsqueda del mínimo.
_SENTINEL_INF: float = float("inf")


# ---------------------------------------------------------------------------
# Oracle lazy con caché
# ---------------------------------------------------------------------------

def oracle(
    N: int,
    D: int,
    data_nd: np.ndarray,
    pivot_idx: tuple[int, ...],
    pivot_vals: np.ndarray,
    full_mask: int,
) -> tuple[Callable[[int], float], Callable[[int], tuple]]:
    """Crea un oracle lazy con caché para f(mask_a) y means(mask_a).

    La función ``f`` calcula:

    .. code-block:: text

        f(mask_a) = Σ_i min(|mean_B(i) - pivot_i|, |mean_A(i) - pivot_i|)

    donde:

    - ``mean_A`` = promedio sobre las dims libres de A (B fijo en pivot)
      → costo de NO estar en alcance.
    - ``mean_B`` = promedio sobre las dims libres de B (A fijo en pivot)
      → costo de estar en alcance.

    Solo se evalúan los O(D³) masks solicitados durante el MAO.

    Args:
        N: Número de nodos (ncubos) del subsistema.
        D: Número de dimensiones del subsistema.
        data_nd: TPM en formato nd-array de forma ``(N, 2, ..., 2)``.
        pivot_idx: Estado pivote en orden LIL_ENDIAN (D entradas,
            índice ``[D-1 .. 0]``).
        pivot_vals: Distribución marginal del pivote, forma ``(N,)``.
        full_mask: Máscara de bits con los D bits activos,
            ``(1 << D) - 1``.

    Returns:
        Tupla ``(f, means)`` donde:

        - ``f(mask_a) -> float``: valor del oracle para la partición
          representada por ``mask_a``.
        - ``means(mask_a) -> (mean_a, mean_b)``: promedios del lado A
          y del lado B para ``mask_a``.

    Example::

        f, means = oracle(N, D, data_nd, pivot_idx, pivot_vals, full_mask)
        valor = f(0b0101)
        mean_a, mean_b = means(0b0101)
    """
    _means_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def __compute_means(
        mask_a: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        if mask_a in _means_cache:
            return _means_cache[mask_a]
        mask_b = full_mask ^ mask_a
        slc_a = tuple(
            [slice(None)]
            + [
                slice(None) if (mask_a >> (D - 1 - d)) & 1
                else pivot_idx[D - 1 - d]
                for d in range(D)
            ]
        )
        slc_b = tuple(
            [slice(None)]
            + [
                slice(None) if (mask_b >> (D - 1 - d)) & 1
                else pivot_idx[D - 1 - d]
                for d in range(D)
            ]
        )
        mean_a = data_nd[tuple(slc_a)].reshape(N, -1).mean(axis=1)
        mean_b = data_nd[tuple(slc_b)].reshape(N, -1).mean(axis=1)
        _means_cache[mask_a] = (mean_a, mean_b)
        _means_cache[mask_b] = (mean_b, mean_a)  # complemento gratis
        return mean_a, mean_b

    def f(mask_a: int) -> float:
        if mask_a == 0 or mask_a == full_mask:
            return 0.0
        mean_a, mean_b = __compute_means(mask_a)
        cost_alcance = np.abs(mean_b - pivot_vals)
        cost_no_alcance = np.abs(mean_a - pivot_vals)
        return float(np.minimum(cost_alcance, cost_no_alcance).sum())

    def means(mask_a: int) -> tuple[np.ndarray, np.ndarray]:
        return __compute_means(mask_a)

    return f, means


# ---------------------------------------------------------------------------
# Algoritmo de Queyranne (MAO)
# ---------------------------------------------------------------------------

def qnodes(
    D: int,
    f: Callable[[int], float],
    full_mask: int,
) -> tuple[float, int]:
    """Minimiza f(mask_a) via Maximum Adjacency Ordering (Queyranne 1998).

    Pre-pass: verifica todos los singletons ``f({d})`` para cada dimensión
    ``d``. Esto cubre el caso más común de falla en funciones
    no-submodulares y añade solo O(D) llamadas adicionales al oracle.

    Loop principal: D-1 iteraciones de MAO, O(D²) llamadas por iteración,
    para un total de O(D³) llamadas al oracle.

    Args:
        D: Número de dimensiones (variables) del subsistema.
        f: Oracle callable ``f(mask_a) -> float``.
        full_mask: Máscara de bits con los D bits activos,
            ``(1 << D) - 1``.

    Returns:
        Tupla ``(best_val, best_mask_a)`` donde ``best_val`` es el valor
        mínimo encontrado y ``best_mask_a`` es la máscara de bits del lado
        ganador de la bipartición.

    Example::

        best_val, best_mask = qnodes(D=3, f=mi_oracle, full_mask=0b111)
        print(f"φ mínimo: {best_val}, máscara: {best_mask:03b}")
    """
    V: list[int] = [1 << d for d in range(D)]

    # Pre-pass: singletons (salvaguarda para funciones no-submodulares)
    best_val: float = _SENTINEL_INF
    best_mask_a: int = V[0]
    for singleton in V:
        val = f(singleton)
        if val < best_val:
            best_val = val
            best_mask_a = singleton

    # TODO(refactor): considerar dividir en subfunciones si D crece mucho
    while len(V) > 1:
        # --- Maximum Adjacency Ordering ---
        # key[v] = f(A_acumulado ∪ {v}) para v aún no en A
        remaining = list(V)
        a_mask = 0
        key: dict[int, float] = {v: f(v) for v in remaining}
        order: list[tuple[int, float]] = []

        while remaining:
            u = max(remaining, key=lambda v: key[v])  # noqa: B023
            curr_key = key[u]
            remaining.remove(u)
            order.append((u, curr_key))
            a_mask |= u
            for w in remaining:
                key[w] = f(a_mask | w)

        # Par colgante: pendant_val = s_key = f(V \ {t}) = f({t}) por simetría
        s_node, s_key = order[-2]
        t_node, _t_key = order[-1]
        pendant_val = s_key

        if pendant_val < best_val:
            best_val = pendant_val
            best_mask_a = t_node

        # Contraer s y t en un supernodo
        V.remove(s_node)
        V.remove(t_node)
        V.append(s_node | t_node)

    return best_val, best_mask_a


# ---------------------------------------------------------------------------
# Clase principal QNodes
# ---------------------------------------------------------------------------

# @perfilar  — decorador de profiling; ver src/middlewares/profile.py
class QNodes(SIA):
    """MIP via Queyranne by nodes con oracle lazy.

    Complejidad O(D³·N) vs O(2^(D-1)·N) de la estrategia analítica.

    Attributes:
        sistema: Subsistema activo preparado por ``sia_preparar_subsistema``.
        distribucion: Distribución marginal original del subsistema.
        nombre: Nombre de la estrategia (``QNodes``).

    Example::

        estrategia = QNodes(tpm)
        sol = estrategia.aplicar_estrategia("100", "111", "110", "101")
        print(sol.perdida, sol.particion)
    """

    def aplicar_estrategia(
        self,
        estado_inicial: str,
        condicion: str,
        alcance: str,
        mecanismo: str,
    ) -> Solution:
        """Prepara el subsistema y ejecuta la búsqueda de MIP.

        Args:
            estado_inicial: Estado inicial del sistema en binario,
                p. ej. ``"100"``.
            condicion: Condiciones de fondo; bit ``'1'`` = nodo activo.
            alcance: Elementos futuros del subsistema; bit ``'1'`` = incluir.
            mecanismo: Elementos presentes del subsistema;
                bit ``'1'`` = incluir.

        Returns:
            Objeto :class:`~src.models.core.solution.Solution` con la
            bipartición de mínima pérdida encontrada.

        Example::

            sol = QNodes(tpm).aplicar_estrategia("10", "11", "10", "11")
            assert sol.perdida >= 0.0
        """
        self.sia_preparar_subsistema(
            estado_inicial, condicion, alcance, mecanismo
        )
        self.sistema = self.sia_subsistema
        self.distribucion = self.sia_dists_marginales
        self.nombre = self.__class__.__name__
        return self.resolver()

    def winner(
        self,
        sistema: System,
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Determina la bipartición ganadora via oracle lazy y MAO.

        Args:
            sistema: Subsistema sobre el que se ejecuta el algoritmo.

        Returns:
            Tupla ``(alcance, mecanismo)`` donde ``alcance`` contiene los
            índices de ncubos del lado A y ``mecanismo`` las dimensiones
            del corte.

        Example::

            alcance, mecanismo = estrategia.winner(subsistema)
        """
        D = len(sistema.dims_ncubos)
        N = len(sistema.ncubos)

        data_nd = np.stack([c.data for c in sistema.ncubos])
        pivot_idx = tuple(
            int(sistema.estado_inicial[dim])
            for dim in sistema.dims_ncubos
        )
        pivot_vals = data_nd[(slice(None),) + pivot_idx[::-1]]  # (N,)

        # Baseline de concentración
        all_mean = data_nd.reshape(N, -1).mean(axis=1)
        conc_costs = np.abs(all_mean - pivot_vals)
        conc_idx = int(np.argmin(conc_costs))
        c_conc = float(conc_costs[conc_idx])

        if D <= 1:
            return (sistema.ncubos[conc_idx].indice,), ()

        full_mask = (1 << D) - 1

        # Oracle lazy con caché — solo evalúa los O(D³) masks del MAO
        f, means = oracle(
            N, D, data_nd, pivot_idx, pivot_vals, full_mask
        )
        best_val, best_mask_a = qnodes(D, f, full_mask)

        if c_conc <= best_val:
            return (sistema.ncubos[conc_idx].indice,), ()

        # Nodo i va a alcance si cost_alcance ≤ cost_no_alcance
        mean_a, mean_b = means(best_mask_a)
        node_in_a = (
            np.abs(mean_b - pivot_vals) <= np.abs(mean_a - pivot_vals)
        )

        alcance_out = tuple(
            c.indice
            for i, c in enumerate(sistema.ncubos)
            if node_in_a[i]
        )
        mecanismo_out = tuple(
            sistema.dims_ncubos[d]
            for d in range(D)
            if (best_mask_a >> d) & 1
        )
        return alcance_out, mecanismo_out

    def resolver(self) -> Solution:
        """Ejecuta la bipartición y construye el objeto Solution.

        Returns:
            Objeto :class:`~src.models.core.solution.Solution` con la
            pérdida, distribuciones y representación textual de la
            partición óptima.

        Example::

            sol = estrategia.resolver()
            print(sol.tiempo_total)
        """
        dm_original = self.distribucion
        t0 = time.perf_counter()

        if (
            not self.sistema.indices_ncubos.size
            or not self.sistema.dims_ncubos.size
        ):
            return Solution(
                estrategia=self.nombre.capitalize(),
                perdida=FLOAT_ZERO,
                distribucion_subsistema=dm_original,
                distribucion_particion=dm_original,
                particion=fmt_basic([], []).strip(),
                tiempo_total=time.perf_counter() - t0,
                quiere_hablar=False,
            )

        alcance, mecanismo = self.winner(self.sistema)
        particion_sistema = self.sistema.bipartir(alcance, mecanismo)
        dm = particion_sistema.distribucion_marginal()
        perdida = emd_efecto(dm, dm_original)

        tiempo = time.perf_counter() - t0
        all_indices = list(self.sistema.indices_ncubos)
        all_dims = list(self.sistema.dims_ncubos)
        prim = (
            [(1, idx) for idx in alcance]
            + [(0, dim) for dim in mecanismo]
        )
        dual = (
            [(1, idx) for idx in all_indices if idx not in alcance]
            + [(0, dim) for dim in all_dims if dim not in mecanismo]
        )
        texto_particion = fmt_basic(prim, dual)

        return Solution(
            estrategia=self.nombre.capitalize(),
            perdida=(
                float(perdida) if perdida != INFTY_POS else FLOAT_ZERO
            ),
            distribucion_subsistema=dm_original,
            distribucion_particion=dm,
            particion=texto_particion.strip(),
            tiempo_total=tiempo,
            quiere_hablar=False,
        )
