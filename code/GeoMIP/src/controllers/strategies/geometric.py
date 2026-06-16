"""Estrategia geométrico-topológica para el análisis de irreducibilidad sistémica.

Implementa ``GeometricSIA``, que extiende la clase base ``SIA`` con un algoritmo
de recorrido por niveles de distancia Hamming sobre el hipercubo de estados.

El flujo principal es:

1. Construir la tabla de transiciones (``_build_tabla``) usando broadcasting
   NumPy vectorizado nivel por nivel sobre el espacio de estados ``2^D``.
2. Identificar candidatos a partición mínima (``identificar_particiones_optimas``)
   recorriendo la primera mitad de niveles Hamming.
3. Evaluar la EMD real de cada candidato (``_distribucion_bipartida``) usando
   índices precomputados (OPT-G1) para evitar materializar NCubes intermedios.
4. Retornar la bipartición con menor pérdida como objeto ``Solution``.

Typical usage example::

    gestor = Manager(...)
    estrategia = GeometricSIA(gestor)
    solucion = estrategia.aplicar_estrategia(condicion, alcance, mecanismo, tpm)
"""

from __future__ import annotations

import time

import numpy as np

from src.constants.base import (
    ACTUAL,
    EFECTO,
    NET_LABEL,
    TYPE_TAG,
)
from src.constants.models import (
    GEOMETRIC_ANALYSIS_TAG,
    GEOMETRIC_LABEL,
    GEOMETRIC_STRAREGY_TAG,
)
from src.controllers.manager import Manager
from src.funcs.base import ABECEDARY, emd_efecto
from src.funcs.format import fmt_biparte_q
from src.middlewares.profile import profile, profiler_manager
from src.middlewares.slogger import SafeLogger
from src.models.base.sia import SIA
from src.models.core.solution import Solution

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Escala aplicada a cada nivel k: 1 / 2^k
_ESCALA_NIVEL: float = 2.0

#: Tipo de datos para la tabla de transiciones (precisión reducida, OPT-E1).
#: La EMD final se evalúa aparte con precisión completa.
_DTYPE_TABLA: np.dtype = np.dtype(np.float32)

#: Tipo de datos para el vector de niveles Hamming (ahorra memoria vs int64).
_DTYPE_NIVELES: np.dtype = np.dtype(np.int8)

# Constantes para el algoritmo de popcount (Hamming weight) vectorizado
_POPCOUNT_M1 = np.int64(0x5555555555555555)
_POPCOUNT_M2 = np.int64(0x3333333333333333)
_POPCOUNT_M4 = np.int64(0x0F0F0F0F0F0F0F0F)
_POPCOUNT_H01 = np.int64(0x0101010101010101)
_POPCOUNT_SHIFT = np.int64(56)


class GeometricSIA(SIA):
    """Estrategia geométrico-topológica para SIA (System Irreducibility Analysis).

    Recorre el hipercubo de estados por niveles de distancia Hamming desde el
    estado final hacia el estado inicial, acumulando costos de transición en
    ``_tabla``.  Los candidatos a MIP (Minimum Information Partition) se
    identifican por mínimo costo acumulado y se validan con EMD real.

    Attributes:
        etiquetas: Par ``(minúsculas, MAYÚSCULAS)`` del abecedario para etiquetar
            nodos en la representación de particiones.
        logger: Logger seguro con tag ``GEOMETRIC_STRAREGY_TAG``.
        vertices: Conjunto de vértices ``(tiempo, índice)`` del subsistema activo.
        memoria_particiones: Caché de particiones evaluadas; mapea la clave de
            bipartición a ``(emd, distribucion_particion)``.

    Example::

        gestor = Manager(estado_inicial="101", pagina=0)
        sia = GeometricSIA(gestor)
        sol = sia.aplicar_estrategia("111", "101", "011", tpm)
        print(sol.perdida, sol.particion)
    """

    def __init__(self, gestor: Manager) -> None:
        super().__init__(gestor)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(gestor.estado_inicial)}{gestor.pagina}"
        )
        self.etiquetas: list[tuple[str, ...]] = [
            tuple(s.lower() for s in ABECEDARY),
            ABECEDARY,
        ]
        self.logger = SafeLogger(GEOMETRIC_STRAREGY_TAG)
        self.vertices: set[tuple[int, int]]
        self.memoria_particiones: dict[
            tuple[int, int], tuple[float, float]
        ] = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @profile(context={TYPE_TAG: GEOMETRIC_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray,  # COMENTAR PARA UN SOLO ESTADO INICIAL
    ) -> Solution:
        """Ejecuta el algoritmo geométrico-topológico y retorna la solución MIP.

        El algoritmo recorre el hipercubo de estados nivel por nivel (distancia
        Hamming desde el estado final hacia el inicial), construye ``_tabla``
        con costos acumulados y evalúa candidatos con EMD real.

        Flujo detallado:

        1. Preparar el subsistema condicionado (``sia_preparar_subsistema``).
        2. Construir (o reutilizar desde caché) ``_flat_T`` y ``_tabla``.
        3. Identificar candidatos de partición óptima.
        4. Evaluar EMD de cada candidato; detener si ``emd == 0``.
        5. Retornar el candidato con menor pérdida como ``Solution``.

        Note:
            Decorado con ``@profile``: registra tiempos en
            ``review/profiling/`` como HTML de pyinstrument.

        Args:
            condicion: Cadena binaria que indica qué dimensiones condicionar
                (``"1"`` = activa, ``"0"`` = marginalizar).
            alcance: Cadena binaria que selecciona elementos futuros (NCubes).
            mecanismo: Cadena binaria que selecciona elementos presentes (dims).
            tpm: Matriz de transición de probabilidades completa ``(2^N, N)``.
                Comentar esta línea y la línea equivalente en
                ``sia_preparar_subsistema`` para modo de un solo estado inicial.

        Returns:
            Objeto ``Solution`` con la bipartición MIP, su pérdida (EMD),
            distribuciones del subsistema y de la partición, y tiempo total.

        Example::

            sol = sia.aplicar_estrategia("111", "101", "011", tpm)
            assert sol.perdida >= 0.0
        """
        # COMENTAR la siguiente línea para modo de un solo estado inicial
        self.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm)
        # DESCOMENTAR la siguiente línea para modo de un solo estado inicial
        # self.sia_preparar_subsistema(condicion, alcance, mecanismo)

        futuro = tuple(
            (EFECTO, efecto)
            for efecto in self.sia_subsistema.indices_ncubos
        )
        presente = tuple(
            (ACTUAL, actual)
            for actual in self.sia_subsistema.dims_ncubos
        )

        self._subsistema_key = (condicion, alcance, mecanismo)
        _cache_valida = (
            hasattr(self, "_flat_cache_key")
            and self._flat_cache_key == self._subsistema_key
        )
        if not _cache_valida:
            self._flat_cache_key = self._subsistema_key
            # Una sola orientación en memoria (OPT-E1): (2^D_dims, D_ncubos)
            # C-contigua, consumida por filas en _build_tabla.
            # La vista transpuesta (D_ncubos, 2^D_dims) se expone como
            # propiedad ``_flat_data_matrix``.
            ncubos = self.sia_subsistema.ncubos
            self._flat_T = np.empty(
                (ncubos[0].data.size, len(ncubos)),
                dtype=ncubos[0].data.dtype,
            )
            for i, nc in enumerate(ncubos):
                self._flat_T[:, i] = nc.data.ravel()
            self._preparar_indices_bipartida()

        self.vertices = set(presente + futuro)
        dims = self.sia_subsistema.dims_ncubos
        self.estado_inicial = self.sia_subsistema.estado_inicial[dims]
        self.estado_final = 1 - self.estado_inicial
        mip = self.find_mip()
        fmt_mip = fmt_biparte_q(list(mip), self.nodes_complement(mip))

        return Solution(
            estrategia=GEOMETRIC_LABEL,
            perdida=self.memoria_particiones[mip][0],
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=self.memoria_particiones[mip][1],
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_mip,
        )

    def nodes_complement(
        self, nodes: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """Retorna el complemento de ``nodes`` respecto a ``self.vertices``.

        Args:
            nodes: Lista de vértices ``(tiempo, índice)`` que forman un lado
                de la bipartición.

        Returns:
            Lista de vértices que pertenecen al lado complementario.

        Example::

            comp = sia.nodes_complement([(1, 0), (0, 1)])
        """
        return list(set(self.vertices) - set(nodes))

    # ------------------------------------------------------------------
    # Propiedad de datos aplanados
    # ------------------------------------------------------------------

    @property
    def _flat_data_matrix(self) -> np.ndarray:
        """Vista ``(D_ncubos, 2^D_dims)`` sobre ``_flat_T``, sin copia (OPT-E1).

        Returns:
            Arreglo 2-D con los datos de todos los NCubes como filas.
        """
        return self._flat_T.T

    # ------------------------------------------------------------------
    # Métodos de búsqueda MIP
    # ------------------------------------------------------------------

    def find_mip(self) -> tuple[tuple[int, int], ...]:
        """Encuentra la bipartición mínima usando el enfoque geométrico-topológico.

        Construye (o reutiliza) la tabla de costos acumulados ``_tabla``,
        genera candidatos con ``identificar_particiones_optimas`` y evalúa
        la EMD real de cada uno.  Se detiene anticipadamente si ``emd == 0``.

        Returns:
            Clave canónica de la bipartición MIP en ``memoria_particiones``.

        Example::

            mip_key = sia.find_mip()
            emd, dist = sia.memoria_particiones[mip_key]
        """
        self.sia_logger.critic("empieza.")
        self.memoria_particiones = {}
        estado_inicial = self.estado_inicial
        estado_final = self.estado_final
        self.idx_ncubos = list(
            range(len(self.sia_subsistema.indices_ncubos))
        )
        D = len(estado_inicial)
        self._D = D
        ini_int = self._estado_a_int(estado_inicial.tolist())
        self._ini_int = ini_int

        _tabla_valida = (
            hasattr(self, "_tabla_key")
            and self._tabla_key == self._subsistema_key
        )
        if not _tabla_valida:
            self._tabla_key = self._subsistema_key
            self._build_tabla(estado_final)

        candidatos = self.identificar_particiones_optimas()
        for _, (presentes, futuros) in enumerate(candidatos):
            presentes = self.sia_subsistema.dims_ncubos[presentes]
            futuros = self.sia_subsistema.indices_ncubos[futuros]
            key: tuple[tuple[int, int], ...] = tuple(
                [(ACTUAL, nodo) for nodo in presentes]
                + [(EFECTO, nodo) for nodo in futuros]
            )
            if key in self.memoria_particiones:
                continue
            dist = self._distribucion_bipartida(futuros, presentes)
            emd = emd_efecto(dist, self.sia_dists_marginales)
            self.memoria_particiones[key] = (emd, dist)
            if emd == 0.0:
                break

        return min(
            self.memoria_particiones,
            key=lambda k: self.memoria_particiones[k][0],
        )

    # ------------------------------------------------------------------
    # Construcción de la tabla de costos Hamming
    # ------------------------------------------------------------------

    def _build_tabla(self, estado_final: np.ndarray) -> None:
        """Construye ``_tabla`` con broadcasting NumPy, nivel por nivel.

        Reemplaza el bucle de ``2^D`` llamadas Python individuales con
        operaciones vectorizadas sobre arrays enteros.  Para cada nivel ``k``
        del BFS procesa todos los ``C(D, k)`` estados simultáneamente.

        La tabla ``_tabla[s]`` almacena el costo acumulado normalizado del
        estado ``s`` respecto al estado inicial, ponderado por ``1 / 2^k``.

        Note:
            Solo se persiste el nivel por estado (N bytes en ``_levels``) en
            lugar de un diccionario de arrays por nivel (8N bytes) — OPT-E1.
            ``_tabla`` usa ``float32`` porque solo guía la selección de
            candidatos; la EMD final se evalúa con precisión completa.

        Args:
            estado_final: Vector de bits del estado objetivo (complemento del
                estado inicial).

        # TODO(refactor): considerar dividir en subfunciones
        """
        D = self._D
        ini_int = self._ini_int
        fin_int = self._estado_a_int(estado_final.tolist())
        flat_T = self._flat_T        # (N, D_ncubos) C-contigua (OPT-E1)
        D_ncubos = flat_T.shape[1]
        N = 1 << D

        ini_row = flat_T[ini_int].copy()   # (D_ncubos,)

        self._tabla = np.zeros((N, D_ncubos), dtype=_DTYPE_TABLA)

        # Nivel de cada estado = popcount(s XOR ini, solo bits fin-direction)
        all_states = np.arange(N, dtype=np.int64)
        fin_mask = int(ini_int ^ fin_int)  # bits que difieren entre ini y fin
        flipped = (
            (all_states ^ np.int64(ini_int)) & np.int64(fin_mask)
        )

        # Popcount vectorizado (Hamming weight para int64)
        n = flipped.copy()
        n -= (n >> np.int64(1)) & _POPCOUNT_M1
        n = (n & _POPCOUNT_M2) + ((n >> np.int64(2)) & _POPCOUNT_M2)
        n = (n + (n >> np.int64(4))) & _POPCOUNT_M4
        levels = (n * _POPCOUNT_H01) >> _POPCOUNT_SHIFT

        # Bits que deben cambiar de ini hacia fin
        fin_bits = [i for i in range(D) if (fin_mask >> i) & 1]
        max_level = len(fin_bits)

        self._levels = levels.astype(_DTYPE_NIVELES)
        self._max_level = max_level

        for nivel in range(1, max_level + 1):
            S_k = all_states[levels == nivel]   # estados en este nivel

            # Diferencia absoluta vs ini para todos los estados del nivel
            self._tabla[S_k] = np.abs(
                flat_T[S_k] - ini_row
            )  # (|S_k|, D_ncubos)

            # Acumular costos de predecesores
            if nivel > 1:
                for i in fin_bits:
                    bit_ini_i = (ini_int >> i) & 1
                    mask = (
                        (S_k >> np.int64(i)) & np.int64(1)
                    ) != bit_ini_i
                    if mask.any():
                        preds = S_k[mask] ^ np.int64(1 << i)
                        self._tabla[S_k[mask]] += self._tabla[preds]

            self._tabla[S_k] *= 1.0 / (_ESCALA_NIVEL ** nivel)

    # ------------------------------------------------------------------
    # Identificación de candidatos a MIP
    # ------------------------------------------------------------------

    def identificar_particiones_optimas(self) -> list[list[list[int]]]:
        """Identifica candidatos a MIP con operaciones NumPy vectorizadas.

        Recorre la primera mitad de niveles Hamming.  Para cada nivel selecciona
        el estado con menor costo total ``sum(min(actual, complementario))`` y
        deriva presentes/futuros del estado óptimo.

        Returns:
            Lista de candidatos ``[[presentes], [futuros]]`` en índices de
            posición dentro de ``dims_ncubos`` e ``indices_ncubos``.

        Example::

            candidatos = sia.identificar_particiones_optimas()
            for presentes, futuros in candidatos:
                ...
        """
        ini_int = self._ini_int
        D = self._D
        n_vars = len(self.idx_ncubos)
        candidatos: list[list[list[int]]] = []

        # Candidatos iniciales: excluir una variable futura a la vez
        presentes_comun = list(range(D))
        for idx in range(n_vars):
            futuros = [i for i in range(n_vars) if i != idx]
            candidatos.append([presentes_comun, futuros])

        niveles_totales = self._max_level + 1   # incluye nivel 0
        es_par = niveles_totales % 2 == 0
        mitad = (
            niveles_totales // 2
            if es_par
            else (niveles_totales // 2) + 1
        )
        mask_all_bits = np.int64((1 << D) - 1)
        ini_bits = np.array(
            [(ini_int >> i) & 1 for i in range(D)], dtype=np.int64
        )

        for nivel in range(1, mitad):
            S = np.nonzero(
                self._levels == nivel
            )[0].astype(np.int64)
            if not len(S):
                continue

            actual = self._tabla[S]                   # (|S|, n_vars)
            comps = S ^ mask_all_bits                 # estados complementarios
            complementario = self._tabla[comps]       # (|S|, n_vars)

            # Costo total = suma de min(actual, comp) para cada NCube
            min_costs = np.minimum(actual, complementario)  # (|S|, n_vars)
            total_costs = min_costs.sum(axis=1)              # (|S|,)

            best_idx = int(np.argmin(total_costs))
            best_state = int(S[best_idx])
            best_actual = actual[best_idx]       # (n_vars,)
            best_comp = complementario[best_idx] # (n_vars,)

            # presentes: bits de best_state que coinciden con ini_int
            best_bits = np.array(
                [(best_state >> i) & 1 for i in range(D)],
                dtype=np.int64,
            )
            presentes_nivel = np.where(
                ini_bits == best_bits
            )[0].tolist()

            # futuros: NCubes donde costo actual <= costo complementario
            futuros_nivel = np.where(
                best_actual <= best_comp
            )[0].tolist()

            candidatos.append([presentes_nivel, futuros_nivel])

        return candidatos

    # ------------------------------------------------------------------
    # Evaluación de distribución de una bipartición
    # ------------------------------------------------------------------

    def _preparar_indices_bipartida(self) -> None:
        """Precalcula índices y máscaras de bits para ``_distribucion_bipartida``.

        Para cada NCube guarda: dims en orden de eje (little-endian), el valor
        del estado inicial por eje y la máscara de bits de cada dim.
        Evita reconstruir sets y realizar lookups en el bucle interno de cada
        evaluación de candidato (OPT-G1).

        Note:
            Debe llamarse una vez por subsistema, después de poblar ``_flat_T``.
        """
        subsistema = self.sia_subsistema
        estado_inicial = subsistema.estado_inicial
        self._bip_estado_eje: list[np.ndarray] = []
        self._bip_bits_eje: list[np.ndarray] = []
        for ncubo in subsistema.ncubos:
            dims_rev = ncubo.dims[::-1].astype(np.int64)
            self._bip_estado_eje.append(
                estado_inicial[dims_rev].astype(np.int64)
            )
            self._bip_bits_eje.append(np.int64(1) << dims_rev)

    def _distribucion_bipartida(
        self,
        alcance: np.ndarray,
        mecanismo: np.ndarray,
    ) -> np.ndarray:
        """Calcula la distribución marginal de la bipartición sin materializar NCubes.

        En lugar de:
            ``media sobre 2^D elementos → seleccionar 1 valor``
        hace:
            ``fijar ejes mantenidos → media sobre solo 2^|marg| elementos``

        Para ``D=20`` con ``|marg|=10`` esto implica ``2^10 = 1K`` vs
        ``2^20 = 1M`` operaciones: ~1000x más rápido por NCube.

        La pertenencia de cada eje al mecanismo se decide con AND de máscaras
        de bits precomputadas (``_preparar_indices_bipartida``), sin sets
        (OPT-G1).

        Args:
            alcance: Índices de los NCubes que pertenecen al alcance activo.
            mecanismo: Índices de las dims que pertenecen al mecanismo activo.

        Returns:
            Vector ``float32`` de longitud ``len(ncubos)`` con la distribución
            marginal de la bipartición.

        Example::

            dist = sia._distribucion_bipartida(
                np.array([0, 2]), np.array([1])
            )
        """
        subsistema = self.sia_subsistema
        alcance_set = {int(x) for x in alcance}
        mec_mask = np.int64(0)
        for d in mecanismo:
            mec_mask |= np.int64(1) << np.int64(int(d))

        ncubos = subsistema.ncubos
        distribuciones = np.empty(len(ncubos), dtype=np.float32)

        for i, ncubo in enumerate(ncubos):
            en_mecanismo = (self._bip_bits_eje[i] & mec_mask) != 0
            fijar = (
                en_mecanismo
                if ncubo.indice in alcance_set
                else ~en_mecanismo
            )

            idx: list = [slice(None)] * len(fijar)
            estado_eje = self._bip_estado_eje[i]
            for k in np.nonzero(fijar)[0]:
                idx[k] = int(estado_eje[k])

            sub_data = ncubo.data[tuple(idx)]
            distribuciones[i] = 1.0 - float(np.mean(sub_data))

        return distribuciones

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _estado_a_int(self, estado: list[int]) -> int:
        """Convierte una lista de bits (little-endian) a entero.

        Args:
            estado: Lista de bits ``[b0, b1, …, bD-1]`` en orden little-endian.

        Returns:
            Entero equivalente: ``sum(b_i * 2^i)``.

        Example::

            assert sia._estado_a_int([1, 0, 1]) == 5
        """
        return sum(b << i for i, b in enumerate(estado))

    def hamming(self, a: list[int], b: list[int]) -> int:
        """Calcula la distancia Hamming entre dos vectores de bits.

        Args:
            a: Primer vector de bits.
            b: Segundo vector de bits (misma longitud que ``a``).

        Returns:
            Número de posiciones donde ``a`` y ``b`` difieren.

        Example::

            assert sia.hamming([1, 0, 1], [0, 0, 1]) == 1
        """
        return sum(x != y for x, y in zip(a, b))
