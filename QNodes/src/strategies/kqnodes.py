"""KQNodes: extensión a k-particiones de QNodes por refinamiento greedy.

Implementa la búsqueda de la k-partición de mínima información integrada
usando refinamiento iterativo greedy sobre bloques de dimensiones.

Algoritmo principal:
    Bipartición iterativa con criterio C4 (corte marginal mínimo) o C1
    (tamaño máximo de bloque). En cada paso se selecciona el bloque
    candidato y se subdivide con el oracle Queyranne restringido al bloque.

Complejidades:
    - Tiempo: O(k·D³) en total (≤ 2k-1 llamadas a ``qnodes`` para C4).
    - Espacio: O(k·D²) para los cachés de oracle por bloque.

Regresión garantizada:
    ``KQNodes(k=2)`` replica exactamente los resultados de ``QNodes``
    (DB-03.1). Para k=2 se usa ``_winner_k2`` que duplica ``QNodes.winner``
    sin importar de ``qnodes.py`` directamente (la importación de
    ``oracle`` y ``qnodes`` al nivel de módulo se mantiene por diseño
    intencional de reutilización).

Typical usage example::

    estrategia = KQNodes(tpm)
    solucion = estrategia.aplicar_estrategia(
        estado_inicial="100",
        condicion="111",
        alcance="110",
        mecanismo="101",
        k=3,
        criterio="C4",
    )
    print(solucion.perdida)
"""

from __future__ import annotations

import heapq
import time
from typing import Callable

import numpy as np

from src.constants.base import FLOAT_ZERO, INFTY_POS
from src.funcs.format import fmt_biparticion_q as fmt_basic
from src.funcs.iit import emd_efecto, seleccionar_estado
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.core.system import System
from src.strategies.qnodes import oracle, qnodes

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Criterio de refinamiento por corte marginal mínimo.
_CRITERIO_C4: str = "C4"

#: Criterio de refinamiento por tamaño máximo de bloque.
_CRITERIO_C1: str = "C1"

#: Representación de partición vacía.
_PARTICION_VACIA: str = "∅"  # ∅


# ---------------------------------------------------------------------------
# Oracle restringido con caché local
# ---------------------------------------------------------------------------

def _oracle_restringido(
    bloque: frozenset[int],
    N: int,
    D_global: int,
    data_nd: np.ndarray,
    pivot_idx: tuple[int, ...],
    pivot_vals: np.ndarray,
) -> tuple[Callable[[int], float], int]:
    """Construye un oracle Queyranne restringido al bloque con caché local.

    El caché se reinicia por cada bloque (caché LOCAL), de modo que los
    bloques distintos no comparten entradas. Dentro del bloque, el
    complemento de cada máscara se almacena gratis (simetría).

    El índice local de cada dimensión en el bloque se corresponde con
    su posición en ``sorted(bloque)``.

    Args:
        bloque: Conjunto de índices globales de dimensión ``{0..D-1}``
            que forman el bloque Pi a subdividir.
        N: Número de nodos (ncubos) del subsistema.
        D_global: Número total de dimensiones del subsistema.
        data_nd: TPM en formato nd-array de forma ``(N, 2, ..., 2)``.
        pivot_idx: Estado pivote en orden LIL_ENDIAN (D_global entradas,
            índice ``[D-1 .. 0]``).
        pivot_vals: Distribución marginal del pivote, forma ``(N,)``.

    Returns:
        Tupla ``(f_local, full_mask_local)`` donde:

        - ``f_local(mask_local) -> float``: oracle restringido al bloque.
        - ``full_mask_local``: máscara con los ``|bloque|`` bits activos.

    Example::

        f_loc, mask = _oracle_restringido(
            frozenset({0, 2}), N=3, D_global=4,
            data_nd=arr, pivot_idx=pivot, pivot_vals=vals,
        )
        phi = f_loc(0b01)
    """
    indices_gl = sorted(bloque)
    m = len(indices_gl)
    full_mask_local = (1 << m) - 1

    _means_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    def __means(
        mask_local: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        if mask_local in _means_cache:
            return _means_cache[mask_local]
        comp_local = full_mask_local ^ mask_local

        slc_a: list = [slice(None)]
        slc_b: list = [slice(None)]
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
        return float(
            np.minimum(
                np.abs(mean_b - pivot_vals),
                np.abs(mean_a - pivot_vals),
            ).sum()
        )

    return f_local, full_mask_local


def _qnodes_sobre_bloque(
    bloque: frozenset[int],
    N: int,
    D_global: int,
    data_nd: np.ndarray,
    pivot_idx: tuple[int, ...],
    pivot_vals: np.ndarray,
) -> tuple[frozenset[int], frozenset[int], float]:
    """Ejecuta QNodes sobre un bloque con oracle restringido y caché local.

    Traduce la máscara de bits local de vuelta a índices globales de
    dimensión para que la partición resultante sea coherente con el
    subsistema completo.

    Args:
        bloque: Conjunto de índices globales de dimensión que forman el
            bloque a subdividir.
        N: Número de nodos (ncubos) del subsistema.
        D_global: Número total de dimensiones del subsistema.
        data_nd: TPM nd-array de forma ``(N, 2, ..., 2)``.
        pivot_idx: Estado pivote en orden LIL_ENDIAN.
        pivot_vals: Distribución marginal del pivote, forma ``(N,)``.

    Returns:
        Tupla ``(A, B, phi_local)`` donde:

        - ``A``: subconjunto de índices globales asignados al lado A.
        - ``B``: subconjunto restante (``bloque - A``).
        - ``phi_local``: costo del mejor corte interno del bloque.

    Example::

        A, B, phi = _qnodes_sobre_bloque(
            frozenset({0, 1, 2}), N, D, arr, pivot, vals
        )
    """
    indices_gl = sorted(bloque)
    m = len(indices_gl)
    if m <= 1:
        return bloque, frozenset(), 0.0

    f_local, full_mask_local = _oracle_restringido(
        bloque, N, D_global, data_nd, pivot_idx, pivot_vals
    )
    phi_local, best_mask_local = qnodes(m, f_local, full_mask_local)

    a_set = frozenset(
        indices_gl[r] for r in range(m) if (best_mask_local >> r) & 1
    )
    b_set = bloque - a_set
    return a_set, b_set, phi_local


# ---------------------------------------------------------------------------
# Cálculo de Φ* (una sola vez al final)
# ---------------------------------------------------------------------------

def _calcular_phi_total(
    particion: list[frozenset[int]],
    sistema: System,
) -> float:
    """Calcula Φ* = EMD(p(s_{t+1}), ⊗_Pi p_{Pi}) para k ≥ 3.

    Para cada dimensión ``d`` en la parte ``Pi``:

    - Se marginaliza el ncubo ``d`` eliminando las dimensiones fuera de
      ``Pi``.
    - El valor reconstruido es ``p(s_{t+1}[d]|Pi)``.

    Las dimensiones sin ncubo correspondiente (D > N) se tratan como
    singletons (todas las dims son "no-Pi").

    Args:
        particion: Lista de partes, cada una como conjunto de índices
            de dimensión ``{0..D-1}``.
        sistema: Subsistema completo con ncubos y estado inicial.

    Returns:
        Valor escalar de Φ* (EMD entre la distribución original y la
        distribución reconstruida por producto tensorial de partes).

    Example::

        phi = _calcular_phi_total(
            [frozenset({0, 1}), frozenset({2})], sistema
        )
    """
    dm_original = sistema.distribucion_marginal()
    todas_dims = list(sistema.dims_ncubos)
    N = len(sistema.ncubos)
    dist_recons = np.empty(N, dtype=np.float32)

    cubiertos: set[int] = set()
    for parte in particion:
        pi_global = {
            todas_dims[d] for d in parte if d < len(todas_dims)
        }
        non_pi_global = np.array(
            [g for g in todas_dims if g not in pi_global],
            dtype=np.int8,
        )
        for d in parte:
            if d >= N:
                continue  # salvaguarda: dim sin ncubo correspondiente
            cubiertos.add(d)
            ncubo = sistema.ncubos[d]
            marg = (
                ncubo.marginalizar(non_pi_global)
                if non_pi_global.size
                else ncubo
            )
            if marg.dims.size:
                pivot = seleccionar_estado(
                    np.array(
                        [sistema.estado_inicial[g] for g in marg.dims],
                        dtype=np.int8,
                    )
                )
                dist_recons[d] = float(marg.data[tuple(pivot)])
            else:
                dist_recons[d] = float(marg.data)

    # Ncubos no cubiertos (N > D_part): singleton
    for d in range(N):
        if d in cubiertos:
            continue
        ncubo = sistema.ncubos[d]
        non_all = np.array(todas_dims, dtype=np.int8)
        marg = ncubo.marginalizar(non_all)
        if marg.dims.size:
            dist_recons[d] = float(
                marg.data[
                    tuple(
                        seleccionar_estado(
                            np.array(
                                [
                                    sistema.estado_inicial[g]
                                    for g in marg.dims
                                ],
                                dtype=np.int8,
                            )
                        )
                    )
                ]
            )
        else:
            dist_recons[d] = float(marg.data)

    return emd_efecto(dm_original, dist_recons)


# ---------------------------------------------------------------------------
# Clase principal KQNodes
# ---------------------------------------------------------------------------

class KQNodes(SIA):
    """k-partición submodular por refinamiento iterativo greedy.

    Extiende :class:`~src.models.base.sia.SIA` con soporte para
    k-particiones (k ≥ 2) usando el criterio C4 (corte marginal mínimo)
    o C1 (bloque de tamaño máximo).

    Reutiliza :func:`~src.strategies.qnodes.oracle` y
    :func:`~src.strategies.qnodes.qnodes` de ``qnodes.py`` sin duplicar
    código (importación de módulo intencional).

    Regresión: ``KQNodes(k=2)`` ≡ ``QNodes`` exactamente (DB-03.1).

    Attributes:
        sistema: Subsistema preparado por ``sia_preparar_subsistema``.
        distribucion: Distribución marginal original del subsistema.
        nombre: Nombre de la estrategia con k y criterio,
            p. ej. ``"KQNodes(k=3,C4)"``.

    Example::

        estrategia = KQNodes(tpm)
        sol = estrategia.aplicar_estrategia(
            "100", "111", "110", "101", k=3
        )
        print(sol.perdida)
    """

    def aplicar_estrategia(  # type: ignore[override]
        self,
        estado_inicial: str,
        condicion: str,
        alcance: str,
        mecanismo: str,
        k: int = 2,
        criterio: str = _CRITERIO_C4,
    ) -> Solution:
        """Prepara el subsistema y halla la k-partición óptima.

        Para ``k=2`` replica exactamente ``QNodes.winner`` (regresión
        DB-03.1). Para ``k≥3`` usa refinamiento iterativo greedy con el
        criterio indicado.

        Args:
            estado_inicial: Estado inicial del sistema en binario,
                p. ej. ``"100"``.
            condicion: Condiciones de fondo; bit ``'1'`` = nodo activo.
            alcance: Elementos futuros del subsistema;
                bit ``'1'`` = incluir.
            mecanismo: Elementos presentes del subsistema;
                bit ``'1'`` = incluir.
            k: Número de partes deseadas (2 ≤ k ≤ 5).
            criterio: ``"C4"`` (corte mínimo, por defecto) o
                ``"C1"`` (tamaño máximo de bloque).

        Returns:
            Objeto :class:`~src.models.core.solution.Solution` con la
            k-partición de mínima información integrada.

        Raises:
            ValueError: No se lanza explícitamente; valores de ``k``
                fuera de rango producen particiones degeneradas.

        Example::

            sol = KQNodes(tpm).aplicar_estrategia(
                "100", "111", "110", "101", k=3, criterio="C4"
            )
            assert sol.perdida >= 0.0
        """
        self.sia_preparar_subsistema(
            estado_inicial, condicion, alcance, mecanismo
        )
        self.sistema = self.sia_subsistema
        self.distribucion = self.sia_dists_marginales
        self.nombre = (
            f"{self.__class__.__name__}(k={k},{criterio})"
        )
        return self._resolver(k, criterio)

    def _resolver(self, k: int, criterio: str) -> Solution:
        """Orquesta la búsqueda de k-partición y construye Solution.

        Args:
            k: Número de partes deseadas.
            criterio: Criterio de refinamiento (``"C4"`` o ``"C1"``).

        Returns:
            Objeto :class:`~src.models.core.solution.Solution`
            con la partición óptima.

        Example::

            sol = estrategia._resolver(k=3, criterio="C4")
        """
        t0 = time.perf_counter()
        dm_original = self.distribucion
        sistema = self.sistema

        if (
            not sistema.indices_ncubos.size
            or not sistema.dims_ncubos.size
        ):
            return Solution(
                estrategia=self.nombre,
                perdida=FLOAT_ZERO,
                distribucion_subsistema=dm_original,
                distribucion_particion=dm_original,
                particion=_PARTICION_VACIA,
                tiempo_total=time.perf_counter() - t0,
                quiere_hablar=False,
            )

        if k == 2:
            # Replicación exacta de QNodes para garantizar regresión DB-03.1
            alcance_w, mec_w = self._winner_k2(sistema)
            arr_alc = np.array(list(alcance_w), dtype=np.int8)
            arr_mec = np.array(list(mec_w), dtype=np.int8)
            dm_part = (
                sistema.bipartir(arr_alc, arr_mec)
                .distribucion_marginal()
            )
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
        self,
        sistema: System,
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Replica ``QNodes.winner`` para garantía de regresión k=2.

        Duplica la lógica de ``QNodes.winner`` intencionalmente para
        evitar acoplamiento de herencia y asegurar que cualquier cambio
        en ``QNodes`` no rompa la regresión de ``KQNodes(k=2)``.

        Args:
            sistema: Subsistema sobre el que se ejecuta el algoritmo.

        Returns:
            Tupla ``(alcance, mecanismo)`` de la bipartición ganadora.

        Example::

            alc, mec = estrategia._winner_k2(subsistema)
        """
        D = len(sistema.dims_ncubos)
        N = len(sistema.ncubos)
        data_nd = np.stack([c.data for c in sistema.ncubos])
        pivot_idx = tuple(
            int(sistema.estado_inicial[dim])
            for dim in sistema.dims_ncubos
        )
        pivot_vals = data_nd[(slice(None),) + pivot_idx[::-1]]

        all_mean = data_nd.reshape(N, -1).mean(axis=1)
        conc_costs = np.abs(all_mean - pivot_vals)
        conc_idx = int(np.argmin(conc_costs))
        c_conc = float(conc_costs[conc_idx])

        if D <= 1:
            return (sistema.ncubos[conc_idx].indice,), ()

        full_mask = (1 << D) - 1
        f, means_fn = oracle(
            N, D, data_nd, pivot_idx, pivot_vals, full_mask
        )
        best_val, best_mask_a = qnodes(D, f, full_mask)

        if c_conc <= best_val:
            return (sistema.ncubos[conc_idx].indice,), ()

        mean_a, mean_b = means_fn(best_mask_a)
        node_in_a = (
            np.abs(mean_b - pivot_vals)
            <= np.abs(mean_a - pivot_vals)
        )
        alc = tuple(
            c.indice
            for i, c in enumerate(sistema.ncubos)
            if node_in_a[i]
        )
        mec = tuple(
            sistema.dims_ncubos[d]
            for d in range(D)
            if (best_mask_a >> d) & 1
        )
        return alc, mec

    # ------------------------------------------------------------------
    # Búsqueda de k-partición (k ≥ 3)
    # ------------------------------------------------------------------

    def _buscar_particion(
        self,
        k: int,
        criterio: str,
    ) -> list[frozenset[int]]:
        """Construye la k-partición inicial y delega en el criterio.

        Limita la partición a ``min(N, D)`` para manejar casos donde
        ``D > N`` (dims sin ncubo) o ``N > D`` (ncubos sin dim asignada).

        Args:
            k: Número de partes deseadas.
            criterio: ``"C4"`` (MinHeap por φ_local) o
                ``"C1"`` (bloque de mayor tamaño).

        Returns:
            Lista de ``frozenset`` con índices de dimensión por parte.

        Example::

            particion = estrategia._buscar_particion(k=3, criterio="C4")
        """
        sistema = self.sistema
        N = len(sistema.ncubos)
        D = len(sistema.dims_ncubos)
        data_nd = np.stack([c.data for c in sistema.ncubos])
        pivot_idx = tuple(
            int(sistema.estado_inicial[dim])
            for dim in sistema.dims_ncubos
        )
        pivot_vals = data_nd[(slice(None),) + pivot_idx[::-1]]

        # D > N: índices d ≥ N no tienen ncubo correspondiente.
        # D < N: los ncubos extra se dejan sin partir.
        d_part = min(N, D)
        v = frozenset(range(d_part))
        if k <= 1 or d_part <= 1:
            return [v]

        if criterio == _CRITERIO_C4:
            return self._refinar_c4(
                v, k, N, D, data_nd, pivot_idx, pivot_vals
            )
        return self._refinar_c1(
            v, k, N, D, data_nd, pivot_idx, pivot_vals
        )

    def _refinar_c4(
        self,
        v: frozenset[int],
        k: int,
        N: int,
        D: int,
        data_nd: np.ndarray,
        pivot_idx: tuple,
        pivot_vals: np.ndarray,
    ) -> list[frozenset[int]]:
        """Refinamiento C4: MinHeap por φ_local. ≤ 2k-1 llamadas a qnodes.

        En cada paso extrae del heap el bloque de menor φ_local (más
        fácil de cortar) y lo subdivide. Los hijos con tamaño ≥ 2 se
        reingresan al heap con su propio φ_local precalculado.

        Args:
            v: Conjunto inicial de todas las dimensiones a particionar.
            k: Número de partes deseadas.
            N: Número de nodos del subsistema.
            D: Número total de dimensiones del subsistema.
            data_nd: TPM nd-array de forma ``(N, 2, ..., 2)``.
            pivot_idx: Estado pivote LIL_ENDIAN.
            pivot_vals: Distribución marginal del pivote, forma ``(N,)``.

        Returns:
            Lista de ``frozenset`` con la k-partición resultante.

        Example::

            partes = estrategia._refinar_c4(
                frozenset({0,1,2}), k=3, N=3, D=3, ...
            )
        """
        a0, b0, phi0 = _qnodes_sobre_bloque(
            v, N, D, data_nd, pivot_idx, pivot_vals
        )
        _id = 0
        heap: list = [(phi0, -len(v), _id, v, a0, b0)]
        particion: list[frozenset[int]] = [v]

        for _ in range(k - 1):
            if not heap:
                break
            phi_sel, _, _, p_sel, a_sel, b_sel = heapq.heappop(heap)
            particion.remove(p_sel)
            if a_sel:
                particion.append(a_sel)
            if b_sel:
                particion.append(b_sel)

            for hijo in (a_sel, b_sel):
                if len(hijo) >= 2:
                    _id += 1
                    ah, bh, phi_h = _qnodes_sobre_bloque(
                        hijo, N, D, data_nd, pivot_idx, pivot_vals
                    )
                    heapq.heappush(
                        heap, (phi_h, -len(hijo), _id, hijo, ah, bh)
                    )

        return particion

    def _refinar_c1(
        self,
        v: frozenset[int],
        k: int,
        N: int,
        D: int,
        data_nd: np.ndarray,
        pivot_idx: tuple,
        pivot_vals: np.ndarray,
    ) -> list[frozenset[int]]:
        """Refinamiento C1: tamaño máximo. k-1 llamadas a qnodes.

        En cada paso selecciona el bloque de mayor cardinalidad (con
        desempate por índice mínimo) y lo subdivide.

        Args:
            v: Conjunto inicial de todas las dimensiones a particionar.
            k: Número de partes deseadas.
            N: Número de nodos del subsistema.
            D: Número total de dimensiones del subsistema.
            data_nd: TPM nd-array de forma ``(N, 2, ..., 2)``.
            pivot_idx: Estado pivote LIL_ENDIAN.
            pivot_vals: Distribución marginal del pivote, forma ``(N,)``.

        Returns:
            Lista de ``frozenset`` con la k-partición resultante.

        Example::

            partes = estrategia._refinar_c1(
                frozenset({0,1,2}), k=3, N=3, D=3, ...
            )
        """
        particion: list[frozenset[int]] = [v]
        for _ in range(k - 1):
            p_sel = max(
                (p for p in particion if len(p) >= 2),
                key=lambda p: (len(p), -min(p)),
                default=None,
            )
            if p_sel is None:
                break
            a_sel, b_sel, _ = _qnodes_sobre_bloque(
                p_sel, N, D, data_nd, pivot_idx, pivot_vals
            )
            particion.remove(p_sel)
            if a_sel:
                particion.append(a_sel)
            if b_sel:
                particion.append(b_sel)
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
        """Formatea una bipartición (k=2) como texto legible.

        Args:
            alcance: Índices de ncubos del lado primario.
            mec: Dimensiones del mecanismo del lado primario.
            sistema: Subsistema del que se extraen todos los índices.

        Returns:
            Representación textual de la bipartición.

        Example::

            texto = estrategia._fmt_biparticion((0,), (1,), sistema)
        """
        all_indices = list(sistema.indices_ncubos)
        all_dims = list(sistema.dims_ncubos)
        prim = (
            [(1, idx) for idx in alcance]
            + [(0, dim) for dim in mec]
        )
        dual = (
            [(1, idx) for idx in all_indices if idx not in alcance]
            + [(0, dim) for dim in all_dims if dim not in mec]
        )
        return fmt_basic(prim, dual).strip()

    def _fmt_particion_k(
        self,
        particion: list[frozenset[int]],
    ) -> str:
        """Formatea una k-partición (k ≥ 3) como texto legible.

        Cada parte se representa con sus índices de ncubo separados por
        ``" | "`` entre partes.

        Args:
            particion: Lista de partes con índices de dimensión.

        Returns:
            Representación textual de la k-partición,
            p. ej. ``"A | B | C"``.

        Example::

            texto = estrategia._fmt_particion_k(
                [frozenset({0}), frozenset({1, 2})]
            )
        """
        sistema = self.sistema
        indices = list(sistema.indices_ncubos)
        partes_txt: list[str] = []
        for parte in particion:
            alc = [
                indices[d]
                for d in sorted(parte)
                if d < len(indices)
            ]
            prim = [(1, idx) for idx in alc]
            partes_txt.append(fmt_basic(prim, []).strip())
        return " | ".join(partes_txt)
