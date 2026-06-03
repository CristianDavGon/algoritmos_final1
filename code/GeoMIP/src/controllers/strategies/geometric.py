import heapq
from src.constants.error import ERROR_INCOMPATIBLE_SIZES
from src.models.core.system import System
from src.constants.base import NET_LABEL, STR_ZERO
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
from typing import List, Dict, Tuple

from concurrent.futures import ThreadPoolExecutor
import itertools

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
        """
        Implementa el algoritmo para encontrar la bipartición óptima
        utilizando el enfoque geométrico-topológico.
        """
        self.sia_logger.critic("empieza.")
        estado_inicial = self.estado_inicial
        estado_final = self.estado_final
        self.idx_ncubos = list(range(len(self.sia_subsistema.indices_ncubos)))
        D = len(estado_inicial)
        D_ncubos = len(self.sia_subsistema.indices_ncubos)
        self._D = D
        self._ini_int = self._estado_a_int(estado_inicial.tolist())
        self._tabla = np.zeros((2**D, D_ncubos), dtype=np.float64)
        self.caminos: Dict[int, List[int]] = {0: [self._ini_int]}
        for nivel in range(1, D + 1):
            self.calcular_costos_nivel(estado_final, nivel)
        candidatos = self.identificar_particiones_optimas()
        for idx, (presentes, futuros) in enumerate(candidatos):
            presentes = self.sia_subsistema.dims_ncubos[presentes]
            futuros = self.sia_subsistema.indices_ncubos[futuros]
            dist =self.sia_subsistema.bipartir(futuros,presentes).distribucion_marginal()
            emd = emd_efecto(dist, self.sia_dists_marginales)
            key = [(0,nodo) for nodo in presentes]
            key.extend([(1,nodo) for nodo in futuros])
            # print(fmt_biparte_q(list(key), self.nodes_complement(key)))
            self.memoria_particiones[tuple(key)] = (emd, dist)
        return min(
            self.memoria_particiones, key=lambda k: self.memoria_particiones[k][0]
        )
    
    def calcular_costos_nivel(self, estado_final: np.ndarray, nivel: int) -> None:
        fin_int = self._estado_a_int(estado_final.tolist())
        visitados: set[int] = set()
        self.caminos[nivel] = []
        for anterior_int in self.caminos[nivel - 1]:
            for i in range(self._D):
                if ((anterior_int >> i) & 1) != ((fin_int >> i) & 1):
                    nuevo_int = anterior_int ^ (1 << i)
                    if nuevo_int not in visitados:
                        self.caminos[nivel].append(nuevo_int)
                        self.calcular_costo(nuevo_int)
                        visitados.add(nuevo_int)

    def calcular_costo(self, fin_int: int) -> None:
        """Calcula tx(ini, fin) y lo escribe en self._tabla[fin_int].

        tx(i,j) = (1/2^dh) * (|X[i]-X[j]| + sum_{pred} tx(i, pred))
        donde pred recorre los predecesores de j en el camino desde i.
        """
        ini_int = self._ini_int
        dist_hamming = bin(ini_int ^ fin_int).count('1')
        factor = 1.0 / (2 ** dist_hamming)
        self._tabla[fin_int] = np.abs(
            self._flat_data_matrix[:, ini_int]
          - self._flat_data_matrix[:, fin_int]
        )
        if dist_hamming > 1:
            for i in range(self._D):
                if ((ini_int >> i) & 1) != ((fin_int >> i) & 1):
                    pred_int = fin_int ^ (1 << i)
                    self._tabla[fin_int] += self._tabla[pred_int]
        self._tabla[fin_int] *= factor

    def identificar_particiones_optimas(self) -> list:
        """Identifica las particiones óptimas basadas en los costos de transición."""
        ini_int = self._ini_int
        D = self._D
        fin_int = self._estado_a_int(self.estado_final.tolist())
        costos = self._tabla[fin_int]
        candidatos = []
        n_vars = len(costos)
        presentes_comun = list(range(len(self.estado_final)))
        for idx in range(n_vars):
            futuros = [i for i in range(n_vars) if i != idx]
            candidatos.append([presentes_comun, futuros])
        es_par = len(self.caminos) % 2 == 0
        mitad = len(self.caminos) // 2 if es_par else (len(self.caminos) // 2) + 1
        for nivel in range(1, mitad):
            costo_candidato_nivel = 1e5
            presentes_nivel: list[int] = []
            futuros_nivel: list[int] = []
            for estado_int in self.caminos[nivel]:
                actual = self._tabla[estado_int]
                comp_int = estado_int ^ ((1 << D) - 1)
                complementario = self._tabla[comp_int]
                presentes = [idx for idx in range(D) if ((estado_int >> idx) & 1) == ((ini_int >> idx) & 1)]
                futuros = []
                costo_candidato = 0.0
                for idx in range(len(self.idx_ncubos)):
                    if actual[idx] <= complementario[idx]:
                        futuros.append(idx)
                        costo_candidato += actual[idx]
                    else:
                        costo_candidato += complementario[idx]
                if costo_candidato < costo_candidato_nivel:
                    costo_candidato_nivel = costo_candidato
                    presentes_nivel = presentes
                    futuros_nivel = futuros
            candidatos.append([presentes_nivel, futuros_nivel])
        return candidatos

    def hamming(self,a: List[int], b: List[int]) -> int:
        return sum(x != y for x, y in zip(a, b))