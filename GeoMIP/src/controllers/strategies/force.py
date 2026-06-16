"""Estrategia de fuerza bruta para el análisis de irreducibilidad sistémica.

Implementa ``BruteForce``, que extiende ``SIA`` evaluando exhaustivamente todas
las biparticiones posibles del subsistema para encontrar la MIP (Minimum
Information Partition) exacta.

Su uso principal es la **validación** de otras estrategias (``GeometricSIA``,
``QNodes``), ya que garantiza encontrar el óptimo global a costa de complejidad
exponencial ``O(2^{m+n})``.

El método ``analizar_completamente_una_red`` genera todos los sistemas candidatos
y sus subsistemas, almacenando resultados en hojas de cálculo Excel bajo
``review/resolver/``.

Typical usage example::

    gestor = Manager(...)
    estrategia = BruteForce(gestor)
    solucion = estrategia.aplicar_estrategia(condicion, alcance, mecanismo)
"""

from __future__ import annotations

import time
from typing import Callable

import numpy as np
import pandas as pd
from colorama import Fore
from numpy.typing import NDArray

from src.constants.base import (
    ACTUAL,
    EFECTO,
    EXCEL_EXTENSION,
    NET_LABEL,
    TYPE_TAG,
)
from src.constants.models import (
    BRUTEFORCE_ANALYSIS_TAG,
    BRUTEFORCE_FULL_ANALYSIS_TAG,
    BRUTEFORCE_LABEL,
    BRUTEFORCE_STRAREGY_TAG,
    DUMMY_ARR,
    DUMMY_EMD,
    ERROR_PARTITION,
)
from src.controllers.manager import Manager
from src.funcs.base import literales, seleccionar_metrica
from src.funcs.format import fmt_biparticion
from src.funcs.system import (
    biparticiones,
    generar_candidatos,
    generar_particiones,
    generar_subsistemas,
)
from src.middlewares.profile import profile, profiler_manager
from src.middlewares.slogger import SafeLogger
from src.models.base.application import aplicacion
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.core.system import System

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Valor inicial de pequeña phi antes de evaluar biparticiones.
_PHI_INICIAL: float = float("inf")

#: Formato del mensaje de finalización de análisis completo.
_MSG_GENERACION_OK: str = (
    "{rojo}Generación finalizada!{azul}\n"
    "Revisa tu directorio `review/resolver/`.\n"
    "{blanco}Tamaño de la red: {n} nodos.\n"
    "Estado inicial: {estado}.\n"
)


class BruteForce(SIA):
    """Búsqueda exhaustiva de la MIP sobre todas las biparticiones del subsistema.

    Evalúa todas las ``2^{m+n}`` biparticiones posibles (futuros × presentes)
    del subsistema y retorna la de mínima EMD como solución.

    Para activar el perfil de rendimiento (``@profile``), arrastrar el HTML
    generado en ``review/profiling/`` al navegador para visualizar tiempos
    acumulados y temporales por subrutina.

    Para habilitar logging detallado::

        self.logger.info("General status update")
        self.logger.debug("Detailed debugging info")
        self.logger.debuging("debuging message")
        self.logger.error("Error occurred")

    El archivo de log se almacena con el nombre configurado en
    ``setup_logger(...)``.

    Attributes:
        distancia_metrica: Función de distancia seleccionada según
            ``aplicacion.distancia_metrica`` (p.ej. EMD efecto o causa).
        logger: Logger seguro con tag ``BRUTEFORCE_STRAREGY_TAG``.

    Example::

        gestor = Manager(estado_inicial="101", pagina=0)
        sia = BruteForce(gestor)
        sol = sia.aplicar_estrategia("111", "101", "011")
        print(sol.perdida, sol.particion)
    """

    def __init__(self, gestor: Manager) -> None:
        super().__init__(gestor)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(gestor.estado_inicial)}{gestor.pagina}"
        )
        self.distancia_metrica: Callable = seleccionar_metrica(
            aplicacion.distancia_metrica
        )
        self.logger = SafeLogger(BRUTEFORCE_STRAREGY_TAG)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @profile(context={TYPE_TAG: BRUTEFORCE_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condiciones: str,
        alcance: str,
        mecanismo: str,
    ) -> Solution:
        """Análisis por fuerza bruta sobre el subsistema indicado.

        Evalúa exhaustivamente todas las biparticiones ``(subalcance,
        submecanismo)`` del subsistema definido por ``condiciones``,
        ``alcance`` y ``mecanismo``, y retorna la de menor EMD.

        Note:
            Decorado con ``@profile``: registra tiempos en
            ``review/profiling/`` como HTML de pyinstrument.

        Args:
            condiciones: Cadena binaria de condiciones de fondo; los bits en
                ``"0"`` indican dimensiones a condicionar en el estado inicial.
            alcance: Cadena binaria que selecciona elementos futuros (NCubes);
                los bits en ``"0"`` se marginalizan.
            mecanismo: Cadena binaria que selecciona elementos presentes
                (dims); los bits en ``"0"`` se marginalizan.

        Returns:
            Objeto ``Solution`` con la bipartición MIP, pérdida, distribuciones
            y tiempo total de ejecución.

        Example::

            sol = sia.aplicar_estrategia("111", "101", "011")
            assert sol.perdida >= 0.0
        """
        tpm = self.sia_cargar_tpm()
        self.sia_preparar_subsistema(condiciones, alcance, mecanismo, tpm)

        solucion_base = Solution(
            BRUTEFORCE_LABEL,
            DUMMY_EMD,
            self.sia_dists_marginales,
            DUMMY_ARR,
            ERROR_PARTITION,
        )

        small_phi: float = _PHI_INICIAL
        mejor_dist_marg: np.ndarray = DUMMY_ARR

        futuros = self.sia_subsistema.indices_ncubos
        presentes = self.sia_subsistema.dims_ncubos
        biparticion_prim: tuple[tuple[int, ...], tuple[int, ...]]
        biparticion_dual: tuple[tuple[int, ...], tuple[int, ...]]
        m, n = futuros.size, presentes.size

        for subalcance, submecanismo in biparticiones(
            futuros, presentes, (1 << m) * (1 << n)
        ):
            subsistema = self.sia_subsistema
            arr_alcance = np.array(subalcance, dtype=np.int8)
            arr_mecanismo = np.array(submecanismo, dtype=np.int8)

            particion = subsistema.bipartir(arr_alcance, arr_mecanismo)

            part_marg_dist = particion.distribucion_marginal()
            emd_value = self.distancia_metrica(
                part_marg_dist, self.sia_dists_marginales
            )
            if emd_value < small_phi:
                small_phi = emd_value
                mejor_dist_marg = part_marg_dist
                biparticion_prim = submecanismo, subalcance
                biparticion_dual = (
                    set(presentes.data) - set(submecanismo),
                    set(futuros.data) - set(subalcance),
                )

        biparticion_formateada = fmt_biparticion(
            [biparticion_prim[ACTUAL], biparticion_prim[EFECTO]],
            [biparticion_dual[ACTUAL], biparticion_dual[EFECTO]],
        )

        solucion_base.perdida = small_phi
        solucion_base.distribucion_particion = mejor_dist_marg
        solucion_base.particion = biparticion_formateada
        solucion_base.tiempo_ejecucion = time.time() - self.sia_tiempo_inicio
        solucion_base.hablar = True

        return solucion_base

    @profile(context={TYPE_TAG: BRUTEFORCE_FULL_ANALYSIS_TAG})
    def analizar_completamente_una_red(self) -> None:
        """Genera el análisis completo de todos los subsistemas de una red.

        Para una red de ``N`` elementos con un único estado inicial, crea los
        ``2^N - 1`` sistemas candidatos factibles, y para cada uno evalúa sus
        ``2^{m+n-1} - 1`` biparticiones no triviales.  Los resultados se
        almacenan como hojas Excel en ``review/resolver/<red>/<estado>/``.

        Note:
            Decorado con ``@profile``: registra tiempos en
            ``review/profiling/`` como HTML de pyinstrument.
        """
        self.sia_gestor.output_dir.mkdir(parents=True, exist_ok=True)

        tpm = self.sia_cargar_tpm()
        initial_state = np.array(
            [canal for canal in self.sia_gestor.estado_inicial],
            dtype=np.int8,
        )
        system = System(tpm, initial_state)
        self.__analizar_candidatos(system)
        print(
            f"\n{Fore.RED}Generación finalizada!{Fore.BLUE}\n"
            f"Revisa tu directorio `review/resolver/`.\n"
            f"{Fore.WHITE}Tamaño de la red: {initial_state.size} nodos.\n"
            f"Estado inicial: {initial_state}.\n"
        )

    # ------------------------------------------------------------------
    # Métodos privados de análisis completo
    # ------------------------------------------------------------------

    def __analizar_candidatos(self, sistema: System) -> None:
        """Genera y analiza todos los sistemas candidatos factibles.

        Itera sobre todas las combinaciones de dimensiones candidatas y delega
        el análisis de cada una a ``__procesar_candidato``.

        Args:
            sistema: Sistema completo que será condicionado según cada
                combinación de dimensiones candidatas.
        """
        cantidad = len(self.sia_gestor.estado_inicial)
        dim_candidatas = generar_candidatos(cantidad)

        for dimensiones in dim_candidatas:
            self.__procesar_candidato(
                sistema, np.array(dimensiones, dtype=np.int8)
            )

    def __procesar_candidato(
        self,
        completo: System,
        condiciones: NDArray[np.int8],
    ) -> None:
        """Condiciona el sistema completo y procesa sus subsistemas.

        Args:
            completo: Sistema completo a condicionar.
            condiciones: Array de bits que indica las dimensiones a condicionar
                en el sistema completo.
        """
        candidato = completo.condicionar(condiciones)
        nombre = literales(np.setdiff1d(candidato.dims_ncubos, condiciones))
        self.__procesar_subsistema(candidato, nombre)

    def __procesar_subsistema(
        self,
        mecanismo_removido: System,
        nombre_candidato: str,
    ) -> None:
        """Genera todos los subsistemas de un candidato y los analiza.

        Escribe los resultados de cada subsistema en una hoja Excel nombrada
        por su representación literal bajo ``review/``.

        Args:
            mecanismo_removido: Sistema candidato ya condicionado.
            nombre_candidato: Nombre amigable del candidato; determina el nombre
                del fichero Excel en ``review/``.
        """
        results_file = (
            self.sia_gestor.output_dir
            / f"{nombre_candidato}.{EXCEL_EXTENSION}"
        )

        with pd.ExcelWriter(results_file) as writer:
            for alcance_removido, sub_present in generar_subsistemas(
                mecanismo_removido.dims_ncubos
            ):
                if not self.__deberia_omitir_subsistema(
                    alcance_removido, mecanismo_removido
                ):
                    self.__analizar_subsistema(
                        mecanismo_removido,
                        np.array(alcance_removido, dtype=np.int8),
                        np.array(sub_present, dtype=np.int8),
                        writer,
                    )

    def __deberia_omitir_subsistema(
        self,
        alcance_removido: tuple[int, ...],
        candidate: System,
    ) -> bool:
        """Decide si un subsistema debe omitirse por no tener futuro.

        Un subsistema sin futuro no tiene efecto no trivial que analizar;
        se produce cuando todos los índices del candidato serían removidos.

        Args:
            alcance_removido: Índices de las dimensiones que serán removidas.
            candidate: Sistema del que se removerán los alcances.

        Returns:
            ``True`` si el número de alcances a remover es igual al total de
            índices del candidato (futuro vacío).

        Example::

            omitir = sia.__deberia_omitir_subsistema((0, 1), candidato)
        """
        return len(alcance_removido) == candidate.indices_ncubos.size

    def __analizar_subsistema(
        self,
        candidato: System,
        alcance_removido: NDArray[np.int8],
        mecanismo_removido: NDArray[np.int8],
        writer: pd.ExcelWriter,
    ) -> None:
        """Analiza un subsistema y escribe su resultado en una hoja Excel.

        Substrae los alcances y mecanismos indicados del candidato, calcula la
        distribución marginal y delega el análisis de particiones a
        ``__analizar_particiones``.  El resultado se almacena en una hoja cuyo
        nombre es la representación literal del subsistema.

        Args:
            candidato: Subsistema candidato del que se substraerán elementos.
            alcance_removido: Elementos futuros (NCubes) que serán
                marginalizados.
            mecanismo_removido: Elementos presentes (dims) que serán
                marginalizados.
            writer: Escritor ``pd.ExcelWriter`` del documento ya asociado.
        """
        subsistema = candidato.substraer(alcance_removido, mecanismo_removido)
        dist_marginal = subsistema.distribucion_marginal()

        nombre_subsistema = self.__get_nombre_subsistema(
            candidato, alcance_removido, mecanismo_removido
        )
        resultado = self.__analizar_particiones(dist_marginal, subsistema)
        resultado.to_excel(writer, sheet_name=nombre_subsistema)

    def __analizar_particiones(
        self,
        distribucion: NDArray[np.float32],
        subsistema: System,
    ) -> pd.DataFrame:
        """Analiza todas las biparticiones de un subsistema y retorna la matriz EMD.

        Genera una matriz donde las filas representan mecanismos (presentes) y
        las columnas representan alcances (futuros), indexadas por su
        representación binaria.  La celda ``(mecanismo, alcance)`` contiene la
        EMD entre la distribución marginal de la bipartición y la distribución
        original del subsistema.

        La primera partición (trivial) se omite; el índice ``i`` arranca en
        ``1``.  La cantidad de biparticiones con ``k=2`` es
        ``2^{m+n-1} - 1 = [(2^m - 1) · 2^n] - 1``.

        Args:
            distribucion: Distribución marginal de referencia del subsistema.
            subsistema: Subsistema que será biparticionado.

        Returns:
            ``pd.DataFrame`` con filas = representaciones binarias de mecanismos,
            columnas = representaciones binarias de alcances, y valores EMD.

        Example::

            df = sia.__analizar_particiones(dist, subsistema)
            print(df.min().min())   # mínima EMD del subsistema
        """
        m, n = (
            subsistema.indices_ncubos.size,
            subsistema.dims_ncubos.size,
        )

        llave_presente = [f"{number:0{n}b}" for number in range(1 << n)]
        llave_futuro = [
            f"{number:0{m}b}" for number in range(1 << m - 1)
        ]

        resultados = pd.DataFrame(
            columns=llave_futuro,
            index=llave_presente,
            dtype=np.float32,
        )

        for alcance, mecanismo in generar_particiones(m, n):
            sub_alcance = np.array(
                [i for i, bit in enumerate(alcance) if bit]
            )
            sub_mecanismo = np.array(
                [i for i, bit in enumerate(mecanismo) if bit]
            )

            particion = subsistema.bipartir(
                np.array(sub_alcance, dtype=np.int8),
                np.array(sub_mecanismo, dtype=np.int8),
            )

            dist_parte_marginal = particion.distribucion_marginal()
            emd_value = self.distancia_metrica(
                dist_parte_marginal, distribucion
            )

            etiqueta_mecanismo = "".join(map(str, mecanismo.astype(int)))
            etiqueta_alcance = "".join(map(str, alcance.astype(int)))

            resultados.loc[etiqueta_mecanismo, etiqueta_alcance] = emd_value

        return resultados

    def __get_nombre_subsistema(
        self,
        candidato: System,
        sub_alcance: NDArray[np.int8],
        sub_mecanismo: NDArray[np.int8],
    ) -> str:
        """Retorna la representación literal del subsistema analizado.

        Usa las etiquetas de dimensión para generar un nombre amigable del
        tipo ``"ABC|BC"`` donde el lado izquierdo es el futuro retenido y el
        derecho es el presente retenido.

        Args:
            candidato: Sistema candidato del que se obtendrán las dimensiones.
            sub_alcance: Alcance (futuro) que será eliminado en el proceso.
            sub_mecanismo: Mecanismo (presente) que será eliminado.

        Returns:
            Cadena con el nombre del subsistema en formato ``"futuro|presente"``.

        Example::

            nombre = sia.__get_nombre_subsistema(candidato, alcance, mec)
            # "AB|BC"
        """
        futuro_removido = np.setdiff1d(candidato.dims_ncubos, sub_alcance)
        presente_removido = np.setdiff1d(
            candidato.dims_ncubos, sub_mecanismo
        )
        return (
            f"{literales(futuro_removido)}|{literales(presente_removido)}"
        )
