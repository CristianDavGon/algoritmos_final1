from src.constants.base import NET_LABEL
from src.funcs.base import ABECEDARY
from src.middlewares.slogger import SafeLogger
from src.funcs.base import emd_efecto
from src.models.base.sia import SIA
from src.constants.base import (
    ACTUAL,
    EFECTO,
    TYPE_TAG,
)
from src.constants.models import (
    GEOMETRIC_ANALYSIS_TAG,
    GEOMETRIC_LABEL,
    GEOMETRIC_STRAREGY_TAG,
)
from src.controllers.manager import Manager
from src.funcs.format import fmt_biparte_q
from src.middlewares.profile import profiler_manager, profile
from src.models.core.solution import Solution
import numpy as np
import time
from typing import List, Dict

class GeometricSIA(SIA):
    def __init__(self, gestor: Manager):
        super().__init__(gestor)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(gestor.estado_inicial)}{gestor.pagina}"
        )
        self.etiquetas = [tuple(s.lower() for s in ABECEDARY), ABECEDARY]
        self.logger = SafeLogger(GEOMETRIC_STRAREGY_TAG)
        self.vertices: set[tuple]
        self.memoria_particiones: dict[tuple[int, int], tuple[float, float]] = {}

    @profile(context={TYPE_TAG: GEOMETRIC_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray #! COMENTAR PARA UN SOLO ESTADO INICIAL
    ):
        """ vamos a hacer que vaya desde el estado inicial hasta el final, bit a bit diferente, llenando la tabla primero para distancias hamming 1 hasta n, con n la cantidad de bits que cambian del estado inicial al final. para esto podemos usar una tabla de transiciones, donde cada fila es un estado y cada columna es un bit. la tabla de transiciones se llena con los estados que se pueden alcanzar desde el estado inicial, y luego se va llenando la tabla de distancias hamming. para esto vamos a usar una lista de listas, donde cada lista es una fila de la tabla de transiciones. la primera fila es el estado inicial, y las siguientes filas son los estados alcanzables desde el estado inicial. la última fila es el estado final.
        paso a paso
        1. cargar la matriz, pasar a ncubos
        2. condicionar
        3. obtener los bits que cambian entre el estado inicial y el final
        4. obener vecinos del estado final que van hacia el estado inicial y calcular el costo de la transicion.
        5. para cada vecino, obtener los vecinos que van hacia el estado inicial y calcular el costo de la transicion.
        6. repetir hasta llegar al estado inicial.


        nota: intentar llenar la tabla desde el estado final hacia atras, pues al contrario habra dependencia de los valores de la tabla de los estados que van en camino hacia el estado final
        """
        self.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm) #! COMENTAR PARA UN SOLO ESTADO INICIAL
        # self.sia_preparar_subsistema(condicion, alcance, mecanismo) #! DESCOMENTAR PARA UN SOLO ESTADO INICIAL

        futuro = tuple(
            (EFECTO, efecto) for efecto in self.sia_subsistema.indices_ncubos
        )
        presente = tuple(
            (ACTUAL, actual) for actual in self.sia_subsistema.dims_ncubos
        )

        self._subsistema_key = (condicion, alcance, mecanismo)
        if not (hasattr(self, '_flat_cache_key') and self._flat_cache_key == self._subsistema_key):
            self._flat_cache_key = self._subsistema_key
            self._flat_data_matrix = np.stack(
                [nc.data.ravel() for nc in self.sia_subsistema.ncubos]
            )  # shape: (D_ncubos, 2^D_dims)

        self.vertices = set(presente + futuro)
        dims = self.sia_subsistema.dims_ncubos
        self.estado_inicial = self.sia_subsistema.estado_inicial[dims]
        self.estado_final = 1 - self.estado_inicial
        mip = self.find_mip()
        # print(mip)
        fmt_mip = fmt_biparte_q(list(mip), self.nodes_complement(mip))

        return Solution(
            estrategia= GEOMETRIC_LABEL,
            perdida=self.memoria_particiones[mip][0],
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=self.memoria_particiones[mip][1],
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_mip,
        )
    
    def nodes_complement(self, nodes: list[tuple[int, int]]):
        return list(set(self.vertices) - set(nodes))
    
    def _estado_a_int(self, estado: list) -> int:
        return sum(b << i for i, b in enumerate(estado))

    def find_mip(self):
        """Encuentra la bipartición óptima usando el enfoque geométrico-topológico."""
        self.sia_logger.critic("empieza.")
        self.memoria_particiones = {}
        estado_inicial = self.estado_inicial
        estado_final = self.estado_final
        self.idx_ncubos = list(range(len(self.sia_subsistema.indices_ncubos)))
        D = len(estado_inicial)
        self._D = D
        ini_int = self._estado_a_int(estado_inicial.tolist())
        self._ini_int = ini_int
        if not (hasattr(self, '_tabla_key') and self._tabla_key == self._subsistema_key):
            self._tabla_key = self._subsistema_key
            self._build_tabla(estado_final)
        candidatos = self.identificar_particiones_optimas()
        for _, (presentes, futuros) in enumerate(candidatos):
            presentes = self.sia_subsistema.dims_ncubos[presentes]
            futuros = self.sia_subsistema.indices_ncubos[futuros]
            dist = self._distribucion_bipartida(futuros, presentes)
            emd = emd_efecto(dist, self.sia_dists_marginales)
            key = tuple([(0, nodo) for nodo in presentes] + [(1, nodo) for nodo in futuros])
            self.memoria_particiones[key] = (emd, dist)
            if emd == 0.0:
                break
        return min(
            self.memoria_particiones, key=lambda k: self.memoria_particiones[k][0]
        )

    def _distribucion_bipartida(self, alcance: np.ndarray, mecanismo: np.ndarray) -> np.ndarray:
        """
        Computes distribucion_marginal(bipartir(alcance, mecanismo)) directly,
        without materializing intermediate NCube objects.

        Instead of: mean over 2^D elements → select 1 value
        Does:        fix kept axes → mean over only 2^|marg| elements

        For D=20 with |marg|=10, this is 2^10=1K vs 2^20=1M: ~1000x faster per NCube
        (the full 8MB NCube array fits in L3 cache, so scatter reads are fast).
        """
        subsistema = self.sia_subsistema
        estado_inicial = subsistema.estado_inicial
        alcance_set = set(int(x) for x in alcance)
        mecanismo_set = set(int(x) for x in mecanismo)

        ncubos = subsistema.ncubos
        distribuciones = np.empty(len(ncubos), dtype=np.float32)

        for i, ncubo in enumerate(ncubos):
            dims = ncubo.dims
            dims_set = set(int(d) for d in dims)
            n = len(dims)

            if ncubo.indice in alcance_set:
                keep_set = dims_set & mecanismo_set
            else:
                keep_set = dims_set - mecanismo_set

            # axis k in data corresponds to dims[n-1-k] (little-endian layout)
            idx = [slice(None)] * n
            for k in range(n):
                d = int(dims[n - 1 - k])
                if d in keep_set:
                    idx[k] = int(estado_inicial[d])

            sub_data = ncubo.data[tuple(idx)]
            distribuciones[i] = 1.0 - float(np.mean(sub_data))

        return distribuciones

    def _build_tabla(self, estado_final: np.ndarray) -> None:
        """
        Construye _tabla completa usando broadcasting numpy nivel por nivel,
        reemplazando el loop de 2^D llamadas Python individuales.

        Para cada nivel k del BFS, procesa todos los C(D,k) estados
        simultáneamente con operaciones vectorizadas sobre arrays enteros.
        """
        D = self._D
        ini_int = self._ini_int
        fin_int = self._estado_a_int(estado_final.tolist())
        D_ncubos = self._flat_data_matrix.shape[0]
        N = 2 ** D

        # Transponer flat_data_matrix para acceso por fila (contiguo en C-order)
        # _flat_data_matrix: (D_ncubos, N) → flat_T: (N, D_ncubos)
        flat_T = np.ascontiguousarray(self._flat_data_matrix.T)
        ini_row = flat_T[ini_int].copy()  # (D_ncubos,)

        self._tabla = np.zeros((N, D_ncubos), dtype=np.float64)

        # Asignar nivel a cada estado: nivel(s) = popcount(s XOR ini, solo bits fin-direction)
        all_states = np.arange(N, dtype=np.int64)
        fin_mask = int(ini_int ^ fin_int)  # bits que difieren entre ini y fin
        flipped = (all_states ^ np.int64(ini_int)) & np.int64(fin_mask)

        # Popcount vectorizado (algoritmo de Hamming weight para int64)
        n = flipped.copy()
        n -= (n >> np.int64(1)) & np.int64(0x5555555555555555)
        n = (n & np.int64(0x3333333333333333)) + ((n >> np.int64(2)) & np.int64(0x3333333333333333))
        n = (n + (n >> np.int64(4))) & np.int64(0x0F0F0F0F0F0F0F0F)
        levels = (n * np.int64(0x0101010101010101)) >> np.int64(56)

        # Bits que deben cambiar de ini hacia fin
        fin_bits = [i for i in range(D) if (fin_mask >> i) & 1]
        max_level = len(fin_bits)

        self.caminos: Dict[int, np.ndarray] = {0: np.array([ini_int], dtype=np.int64)}

        for nivel in range(1, max_level + 1):
            S_k = all_states[levels == nivel]  # todos los estados en este nivel
            self.caminos[nivel] = S_k

            # Diferencia absoluta vs ini para todos los estados del nivel a la vez
            self._tabla[S_k] = np.abs(flat_T[S_k] - ini_row)  # (|S_k|, D_ncubos)

            # Acumular costos de predecesores (un pase numpy por bit de fin-direction)
            if nivel > 1:
                for i in fin_bits:
                    bit_ini_i = (ini_int >> i) & 1
                    mask = ((S_k >> np.int64(i)) & np.int64(1)) != bit_ini_i
                    if mask.any():
                        preds = S_k[mask] ^ np.int64(1 << i)
                        self._tabla[S_k[mask]] += self._tabla[preds]

            self._tabla[S_k] *= 1.0 / (2 ** nivel)

    def identificar_particiones_optimas(self) -> list:
        """Identifica las particiones óptimas usando operaciones numpy vectorizadas."""
        ini_int = self._ini_int
        D = self._D
        fin_int = self._estado_a_int(self.estado_final.tolist())
        n_vars = len(self.idx_ncubos)
        candidatos = []

        # Candidatos iniciales: excluir una variable futura a la vez
        presentes_comun = list(range(D))
        for idx in range(n_vars):
            futuros = [i for i in range(n_vars) if i != idx]
            candidatos.append([presentes_comun, futuros])

        es_par = len(self.caminos) % 2 == 0
        mitad = len(self.caminos) // 2 if es_par else (len(self.caminos) // 2) + 1
        mask_all_bits = np.int64((1 << D) - 1)
        ini_bits = np.array([(ini_int >> i) & 1 for i in range(D)], dtype=np.int64)

        for nivel in range(1, mitad):
            S = self.caminos[nivel]  # numpy array de enteros de estado
            if not len(S):
                continue

            actual = self._tabla[S]               # (|S|, n_vars)
            comps = S ^ mask_all_bits             # estados complementarios (|S|,)
            complementario = self._tabla[comps]  # (|S|, n_vars)

            # Costo total por estado = suma de min(actual, comp) para cada ncubo
            min_costs = np.minimum(actual, complementario)  # (|S|, n_vars)
            total_costs = min_costs.sum(axis=1)             # (|S|,)

            best_idx = int(np.argmin(total_costs))
            best_state = int(S[best_idx])
            best_actual = actual[best_idx]   # (n_vars,)
            best_comp = complementario[best_idx]  # (n_vars,)

            # presentes: posiciones de bits donde best_state coincide con ini_int
            best_bits = np.array([(best_state >> i) & 1 for i in range(D)], dtype=np.int64)
            presentes_nivel = np.where(ini_bits == best_bits)[0].tolist()

            # futuros: índices de ncubos donde costo actual <= costo complementario
            futuros_nivel = np.where(best_actual <= best_comp)[0].tolist()

            candidatos.append([presentes_nivel, futuros_nivel])

        return candidatos

    def hamming(self, a: List[int], b: List[int]) -> int:
        return sum(x != y for x, y in zip(a, b))