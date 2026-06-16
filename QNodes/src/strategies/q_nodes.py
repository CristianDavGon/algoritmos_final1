"""Implementación alternativa de QNodes con profiling integrado.

Variante del algoritmo Queyranne que opera directamente sobre vértices
``(tiempo, índice)`` sin precómputo del oracle. Emplea memoización
explícita (``memoria_delta``, ``memoria_grupo_candidato``) para evitar
re-evaluaciones costosas de EMD.

Diferencias respecto a ``qnodes.py``:

- Trabaja sobre vértices ``(t, idx)`` en lugar de máscaras de bits.
- La función submodular se evalúa como diferencia de EMDs:
  ``Δ = EMD(omega ∪ delta) - EMD(delta)``.
- Incluye sesión de profiling via ``gestor_perfilado``.
- Decorador ``@profile`` activo en ``algorithm``.

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
from typing import Union

import numpy as np

from src.constants.base import (
    ACTUAL,
    COLS_IDX,
    EFFECT,
    INFTY_POS,
    INT_ZERO,
    LAST_IDX,
    NET_LABEL,
    TYPE_TAG,
)
from src.constants.models import (
    QNODES_ANALYSIS_TAG,
    QNODES_LABEL,
    QNODES_STRAREGY_TAG,
)
from src.funcs.format import fmt_biparticion_q
from src.funcs.iit import ABECEDARY, emd_efecto
from src.middlewares.profile import gestor_perfilado, profile
from src.middlewares.slogger import SafeLogger
from src.models.base.application import aplicacion
from src.models.base.sia import SIA
from src.models.core.solution import Solution

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Valor de EMD local inicial usado como centinela antes de la primera
#: iteración. Se elige suficientemente grande para ser superado siempre.
_EMD_LOCAL_CENTINELA: float = 1e5

# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------


class QNodes(SIA):
    """Análisis de MIP via algoritmo Queyranne sobre vértices (t, idx).

    Implementa la versión alternativa del algoritmo Queyranne con:

    - Memoización de EMDs individuales (``memoria_delta``).
    - Memoización de EMDs de grupos candidatos
      (``memoria_grupo_candidato``).
    - Sesión de profiling automática al instanciar.
    - Decorador ``@profile`` activo en el método ``algorithm``.

    Attributes:
        m: Número de elementos en el alcance (futuros).
        n: Número de elementos en el mecanismo (presentes).
        tiempos: Tupla ``(array_presente, array_futuro)`` de ceros
            que representan los estados por tiempo.
        etiquetas: Lista de tuplas con etiquetas minúsculas y mayúsculas
            del abecedario, una por dimensión.
        vertices: Conjunto de todos los vértices ``(tiempo, índice)``
            del subsistema activo.
        memoria_delta: Caché de ``(emd, dist_marginal)`` por clave de
            delta individual.
        memoria_grupo_candidato: Caché de ``(emd, dist_marginal)`` por
            clave de grupo candidato (bipartición completa).
        indices_alcance: Índices de ncubos en el alcance activo.
        indices_mecanismo: Índices de dimensiones en el mecanismo activo.
        logger: Logger configurado con la etiqueta de la estrategia.

    Example::

        estrategia = QNodes(tpm)
        sol = estrategia.aplicar_estrategia("10", "11", "10", "11")
        print(sol.perdida)
    """

    def __init__(self, tpm: np.ndarray) -> None:
        super().__init__(tpm)
        gestor_perfilado.start_session(
            f"{NET_LABEL}"
            f"{len(tpm[COLS_IDX])}"
            f"{aplicacion.pagina_red_muestra}"
        )
        self.m: int
        self.n: int
        self.tiempos: tuple[np.ndarray, np.ndarray]
        self.etiquetas: list[tuple] = [
            tuple(s.lower() for s in ABECEDARY),
            ABECEDARY,
        ]
        self.vertices: set[tuple]
        self.clave_submodular: list[list] = [[], []]
        self.memoria_delta: dict = {}
        self.memoria_grupo_candidato: dict = {}

        self.indices_alcance: np.ndarray
        self.indices_mecanismo: np.ndarray

        self.logger = SafeLogger(QNODES_STRAREGY_TAG)

    def aplicar_estrategia(
        self,
        estado_inicial: str,
        condicion: str,
        alcance: str,
        mecanismo: str,
    ) -> Solution:
        """Prepara el subsistema y ejecuta el algoritmo Queyranne.

        Construye los vértices ``(tiempo, índice)`` a partir del
        subsistema preparado y delega en ``algorithm`` para encontrar
        la bipartición óptima. El resultado se toma de
        ``memoria_grupo_candidato`` con la clave de menor EMD.

        Args:
            estado_inicial: Estado inicial del sistema en binario,
                p. ej. ``"100"``.
            condicion: Condiciones de fondo; bit ``'1'`` = nodo activo.
            alcance: Elementos futuros del subsistema;
                bit ``'1'`` = incluir.
            mecanismo: Elementos presentes del subsistema;
                bit ``'1'`` = incluir.

        Returns:
            Objeto :class:`~src.models.core.solution.Solution` con la
            bipartición de mínima pérdida encontrada.

        Example::

            sol = QNodes(tpm).aplicar_estrategia(
                "100", "111", "110", "101"
            )
            assert sol.perdida >= 0.0
        """
        self.sia_preparar_subsistema(
            estado_inicial, condicion, alcance, mecanismo
        )

        # Vértices futuros: (EFFECT=1, idx) — p. ej. A=1, B=2, C=3
        futuro = tuple(
            (EFFECT, idx_efecto)
            for idx_efecto in self.sia_subsistema.indices_ncubos
        )
        # Vértices presentes: (ACTUAL=0, idx) — p. ej. a=0, c=2
        presente = tuple(
            (ACTUAL, idx_actual)
            for idx_actual in self.sia_subsistema.dims_ncubos
        )

        self.m = self.sia_subsistema.indices_ncubos.size
        self.n = self.sia_subsistema.dims_ncubos.size

        self.indices_alcance = self.sia_subsistema.indices_ncubos
        self.indices_mecanismo = self.sia_subsistema.dims_ncubos

        self.tiempos = (
            np.zeros(self.n, dtype=np.int8),
            np.zeros(self.m, dtype=np.int8),
        )

        vertices = list(presente + futuro)
        self.vertices = set(presente + futuro)
        mip = self.algorithm(vertices)

        fmt_mip = fmt_biparticion_q(list(mip), self.nodes_complement(mip))
        perdida_mip, dist_marginal_mip = self.memoria_grupo_candidato[mip]

        return Solution(
            estrategia=QNODES_LABEL,
            perdida=perdida_mip,
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=dist_marginal_mip,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_mip,
        )

    @profile(context={TYPE_TAG: QNODES_ANALYSIS_TAG})
    def algorithm(
        self,
        vertices: list[tuple[int, int]],
    ) -> tuple[tuple[int, int], ...]:
        """Algoritmo Queyranne para bipartición de mínima pérdida.

        Encuentra la bipartición del conjunto de vértices que minimiza
        la función submodular de EMD, usando refinamiento incremental
        greedy (Maximum Adjacency Ordering adaptado a vértices).

        El proceso se estructura en **fases > ciclos > iteraciones**:

        - **Fase** (índice ``i``): una iteración del loop exterior que
          produce una bipartición candidata y contrae el par colgante.
        - **Ciclo** (índice ``j``): agrega un elemento delta a omega
          seleccionando el de menor diferencia de EMD.
        - **Iteración** (índice ``k``): evalúa cada delta candidato
          contra el omega acumulado.

        Optimizaciones:

        - ``memoria_delta``: caché de EMD por clave de delta individual.
        - ``memoria_grupo_candidato``: caché de EMD por clave de grupo
          (bipartición completa).
        - Retorno anticipado si la EMD del delta es cero.

        Decorador ``@profile`` activo; los resultados de profiling se
        almacenan en ``review/profiling/``.

        Args:
            vertices: Lista de vértices ``(tiempo, índice)`` donde
                ``tiempo=0`` corresponde al presente (t₀) y
                ``tiempo=1`` al futuro (t₁).

        Returns:
            Clave de la bipartición óptima en ``memoria_grupo_candidato``
            (tupla de vértices del lado primario).

        Raises:
            KeyError: Si la clave ganadora no está en
                ``memoria_grupo_candidato`` (no debería ocurrir en
                condiciones normales).

        Example::

            mip = estrategia.algorithm(vertices)
            emd, dist = estrategia.memoria_grupo_candidato[mip]
        """
        # TODO(refactor): considerar dividir en subfunciones dado que
        # este método supera 40 líneas de lógica real.
        indice_emd = INT_ZERO

        for i in range(len(vertices) - 1):
            omegas_ciclo = [vertices[0]]
            deltas_ciclo = vertices[1:]

            emd_particion_candidata = INFTY_POS
            dist_particion_candidata = None

            for j in range(len(deltas_ciclo) - 1):
                emd_local: float = _EMD_LOCAL_CENTINELA
                indice_mip: int

                for k in range(len(deltas_ciclo)):
                    emd_union, emd_delta, dist_marginal_delta = (
                        self.funcion_submodular(
                            deltas_ciclo[k], omegas_ciclo
                        )
                    )
                    emd_iteracion = emd_union - emd_delta

                    if emd_iteracion < emd_local:
                        if emd_delta == INT_ZERO:
                            clave = (
                                tuple(deltas_ciclo[k])
                                if isinstance(deltas_ciclo[k], list)
                                else (deltas_ciclo[k],)
                            )
                            self.memoria_grupo_candidato[clave] = (
                                emd_delta,
                                dist_marginal_delta,
                            )
                            return clave

                        emd_local = emd_iteracion
                        indice_mip = k
                        emd_particion_candidata = emd_delta
                        dist_particion_candidata = dist_marginal_delta

                omegas_ciclo.append(deltas_ciclo[indice_mip])
                deltas_ciclo.pop(indice_mip)

            self.memoria_grupo_candidato[
                tuple(
                    deltas_ciclo[LAST_IDX]
                    if isinstance(deltas_ciclo[LAST_IDX], list)
                    else deltas_ciclo
                )
            ] = emd_particion_candidata, dist_particion_candidata

            par_candidato = (
                [omegas_ciclo[LAST_IDX]]
                if isinstance(omegas_ciclo[LAST_IDX], tuple)
                else omegas_ciclo[LAST_IDX]
            ) + (
                deltas_ciclo[LAST_IDX]
                if isinstance(deltas_ciclo[LAST_IDX], list)
                else deltas_ciclo
            )

            omegas_ciclo.pop()
            omegas_ciclo.append(par_candidato)

            vertices = omegas_ciclo

        return min(
            self.memoria_grupo_candidato,
            key=lambda k: self.memoria_grupo_candidato[k][indice_emd],
        )

    def funcion_submodular(
        self,
        deltas: Union[tuple, list[tuple]],
        omegas: list[Union[tuple, list[tuple]]],
    ) -> tuple[float, float, np.ndarray]:
        """Evalúa la diferencia de EMD entre delta individual y su unión con omega.

        Realiza dos evaluaciones:

        1. **Delta individual**: calcula ``EMD(delta)`` con caché en
           ``memoria_delta``.
        2. **Unión**: calcula ``EMD(omega ∪ delta)`` sin caché (depende
           del estado actual de omega).

        Args:
            deltas: Vértice individual ``(tiempo, índice)`` o lista de
                vértices que forman un grupo candidato.
            omegas: Lista de nodos ya agrupados; puede contener tuplas
                individuales o listas de tuplas (pares candidatos).

        Returns:
            Tupla ``(emd_union, emd_delta, dist_marginal_delta)`` donde:

            - ``emd_union``: EMD de la bipartición ``omega ∪ delta``.
            - ``emd_delta``: EMD del delta individual.
            - ``dist_marginal_delta``: distribución marginal del delta,
              usada para almacenamiento externo en el caller.

        Example::

            emd_u, emd_d, dist = estrategia.funcion_submodular(
                deltas=(1, 0),
                omegas=[(0, 1), (0, 2)],
            )
        """
        vector_delta_marginal: np.ndarray | None = None
        self.clave_submodular = [[], []]

        # --- Evaluación individual del delta ---
        clave_delta_actual, clave_delta_efecto = self.definir_clave(deltas)
        clave_delta = (
            tuple(clave_delta_actual),
            tuple(clave_delta_efecto),
        )

        idxs_alcance_delta = self.clave_submodular[EFFECT]
        dims_mecanismo_delta = self.clave_submodular[ACTUAL]

        if clave_delta not in self.memoria_delta:
            particion_delta = self.sia_subsistema.bipartir(
                np.array(idxs_alcance_delta, dtype=np.int8),
                np.array(dims_mecanismo_delta, dtype=np.int8),
            )
            vector_delta_marginal = (
                particion_delta.distribucion_marginal()
            )
            emd_delta = emd_efecto(
                vector_delta_marginal, self.sia_dists_marginales
            )
            self.memoria_delta[clave_delta] = (
                emd_delta,
                vector_delta_marginal,
            )
        else:
            emd_delta, vector_delta_marginal = (
                self.memoria_delta[clave_delta]
            )

        # --- Evaluación combinada (omega ∪ delta) ---
        for omega in omegas:
            self.definir_clave(omega)

        idxs_alcance_union = self.clave_submodular[EFFECT]
        dims_mecanismo_union = self.clave_submodular[ACTUAL]

        particion_union = self.sia_subsistema.bipartir(
            np.array(idxs_alcance_union, dtype=np.int8),
            np.array(dims_mecanismo_union, dtype=np.int8),
        )
        vector_union_marginal = particion_union.distribucion_marginal()
        emd_union = emd_efecto(
            vector_union_marginal, self.sia_dists_marginales
        )

        return emd_union, emd_delta, vector_delta_marginal

    def definir_clave(
        self,
        conjunto: Union[tuple[int, int], list[tuple[int, int]]],
    ) -> list[list[int]]:
        """Actualiza ``clave_submodular`` con los índices del conjunto dado.

        Acumula los índices de ``conjunto`` separados por tiempo en
        ``clave_submodular[ACTUAL]`` y ``clave_submodular[EFFECT]``,
        manteniéndolos ordenados.

        Args:
            conjunto: Vértice individual ``(tiempo, índice)`` o lista de
                vértices ``[(tiempo, índice), ...]``.

        Returns:
            La lista ``clave_submodular`` actualizada:
            ``[lista_actual, lista_efecto]``.

        Example::

            estrategia.clave_submodular = [[], []]
            estrategia.definir_clave((0, 2))
            # clave_submodular == [[2], []]
        """
        if isinstance(conjunto, tuple):
            tiempo, indice = conjunto
            self.clave_submodular[tiempo].append(indice)
        else:
            for tiempo, indice in conjunto:
                self.clave_submodular[tiempo].append(indice)
        self.clave_submodular[ACTUAL].sort()
        self.clave_submodular[EFFECT].sort()
        return self.clave_submodular

    def nodes_complement(
        self,
        nodes: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Devuelve los vértices del subsistema que no están en ``nodes``.

        Args:
            nodes: Lista de vértices a excluir del conjunto completo.

        Returns:
            Lista con los vértices de ``self.vertices`` que no aparecen
            en ``nodes``.

        Example::

            complemento = estrategia.nodes_complement([(0, 1)])
        """
        return list(set(self.vertices) - set(nodes))
