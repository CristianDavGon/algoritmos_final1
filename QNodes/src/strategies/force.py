"""Estrategia de fuerza bruta: evaluación exhaustiva de todas las biparticiones.

Evalúa las ``2^(m+n-1) - 1`` biparticiones factibles de un subsistema
``(alcance m, mecanismo n)`` y retorna la de menor φ (Earth Mover's
Distance respecto a la distribución marginal original).

Uso principal: validación de resultados de estrategias heurísticas como
``QNodes`` o ``KQNodes``.

Funcionalidad adicional: el método ``analizar_completamente_una_red``
genera un análisis completo de todos los sistemas candidatos y sus
subsistemas, guardando los resultados en archivos Excel bajo
``review/resolver/``.

Typical usage example::

    estrategia = BruteForce(tpm)
    solucion = estrategia.aplicar_estrategia(
        estado_inicial="100",
        condiciones="111",
        alcance="110",
        mecanismo="101",
    )
    print(solucion.perdida)
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
    COLS_IDX,
    EFFECT,
    EXCEL_EXTENSION,
    FLOAT_ZERO,
    NET_LABEL,
    TYPE_TAG,
)
from src.constants.models import (
    BRUTEFORCE_FULL_ANALYSIS_TAG,
    BRUTEFORCE_LABEL,
    BRUTEFORCE_STRAREGY_TAG,
    DUMMY_ARR,
    DUMMY_EMD,
    ERROR_PARTITION,
)
from src.funcs.format import fmt_biparticion_fuerza_bruta
from src.funcs.force import (
    biparticiones,
    generar_candidatos,
    generar_particiones,
    generar_subsistemas,
)
from src.funcs.iit import literales, seleccionar_emd
from src.middlewares.profile import gestor_perfilado, profile
from src.middlewares.slogger import SafeLogger
from src.models.base.application import aplicacion
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.core.system import System


class BruteForce(SIA):
    """Generador de soluciones mediante fuerza bruta sobre una red.

    Evalúa todas las biparticiones factibles de un subsistema y retorna
    la de menor pérdida de información (φ mínimo). Útil como validador
    de resultados de estrategias heurísticas.

    La clase incluye un método auxiliar para análisis completo de redes
    (``analizar_completamente_una_red``) que genera matrices EMD para
    todos los candidatos y subsistemas posibles.

    Debugging disponible::

        self.logeador.info("General status update")
        self.logeador.debug("Detailed debugging info")
        self.logeador.error("Error occurred")

    El archivo de profiling (extensión HTML) se genera en
    ``review/profiling/`` al usar el decorador ``@profile``; se
    visualiza arrastrándolo al navegador.

    Attributes:
        distancia_metrica: Callable seleccionado según configuración para
            calcular la EMD entre distribuciones.
        logeador: Logger configurado con la etiqueta de la estrategia.

    Example::

        estrategia = BruteForce(tpm)
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
        self.distancia_metrica: Callable = seleccionar_emd()
        self.logeador = SafeLogger(BRUTEFORCE_STRAREGY_TAG)

    # @profile(context={TYPE_TAG: BRUTEFORCE_ANALYSIS_TAG})
    # Descomenta la línea anterior y revisa `./review/profiling/`
    def aplicar_estrategia(
        self,
        estado_inicial: str,
        condiciones: str,
        alcance: str,
        mecanismo: str,
    ) -> Solution:
        """Análisis por fuerza bruta del subsistema especificado.

        Itera sobre todas las biparticiones ``(subalcance, submecanismo)``
        factibles del subsistema y conserva la de menor EMD. Si se
        encuentra una bipartición con EMD = 0 retorna inmediatamente
        (optimización de corte anticipado).

        Args:
            estado_inicial: Estado inicial del sistema en binario,
                p. ej. ``"100"``.
            condiciones: Condiciones de fondo; bit ``'0'`` = dimensión
                condicionada (marginalizada).
            alcance: Elementos futuros del subsistema;
                bit ``'0'`` = marginalizar.
            mecanismo: Elementos presentes del subsistema;
                bit ``'0'`` = marginalizar.

        Returns:
            Objeto :class:`~src.models.core.solution.Solution` con la
            bipartición de mínima pérdida encontrada.

        Example::

            sol = BruteForce(tpm).aplicar_estrategia(
                "100", "111", "110", "101"
            )
            assert sol.perdida >= 0.0
        """
        self.sia_preparar_subsistema(
            estado_inicial, condiciones, alcance, mecanismo
        )

        solucion_base = Solution(
            BRUTEFORCE_LABEL,
            DUMMY_EMD,
            self.sia_dists_marginales,
            DUMMY_ARR,
            ERROR_PARTITION,
            quiere_hablar=True,
        )

        small_phi: float = np.inf
        mejor_dist_marg: np.ndarray = DUMMY_ARR

        futuros = self.sia_subsistema.indices_ncubos
        presentes = self.sia_subsistema.dims_ncubos
        biparticion_prim: tuple[tuple[int, ...], tuple[int, ...]]
        biparticion_dual: tuple[tuple[int, ...], tuple[int, ...]]
        m, n = futuros.size, presentes.size

        # TODO(refactor): considerar dividir en subfunciones
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
                # Corte anticipado (la fuerza bruta absoluta no haría esto)
                if emd_value == FLOAT_ZERO:
                    solucion_base.perdida = emd_value
                    solucion_base.distribucion_particion = part_marg_dist
                    solucion_base.particion = (
                        fmt_biparticion_fuerza_bruta(
                            [
                                biparticion_prim[ACTUAL],
                                biparticion_prim[EFFECT],
                            ],
                            [
                                biparticion_dual[ACTUAL],
                                biparticion_dual[EFFECT],
                            ],
                        )
                    )
                    solucion_base.tiempo_ejecucion = (
                        time.time() - self.sia_tiempo_inicio
                    )
                    return solucion_base

        biparticion_formateada = fmt_biparticion_fuerza_bruta(
            [biparticion_prim[ACTUAL], biparticion_prim[EFFECT]],
            [biparticion_dual[ACTUAL], biparticion_dual[EFFECT]],
        )

        solucion_base.perdida = small_phi
        solucion_base.distribucion_particion = mejor_dist_marg
        solucion_base.particion = biparticion_formateada
        solucion_base.tiempo_ejecucion = (
            time.time() - self.sia_tiempo_inicio
        )
        return solucion_base

    @profile(context={TYPE_TAG: BRUTEFORCE_FULL_ANALYSIS_TAG})
    def analizar_completamente_una_red(self) -> None:
        """Analiza todos los candidatos y subsistemas de la red cargada.

        Para una red de N elementos en tiempos t₀ y t₁, para el estado
        inicial configurado:

        1. Genera los ``2^N - 1`` sistemas candidatos factibles.
        2. Para cada candidato, genera sus ``2^(m+n) - 1`` subsistemas.
        3. Para cada subsistema, evalúa las
           ``2^(m+n-1) - 1`` biparticiones factibles.

        Los resultados se guardan en archivos Excel bajo
        ``review/resolver/<red>/<estado_inicial>/``.

        Decorador ``@profile`` activo; ver ``review/profiling/``.

        Raises:
            OSError: Si no se puede crear el directorio de salida.

        Example::

            BruteForce(tpm).analizar_completamente_una_red()
        """
        self.tpm.output_dir.mkdir(parents=True, exist_ok=True)

        tpm = self.sia_cargar_tpm()
        initial_state = self.sia_subsistema.estado_inicial
        system = System(tpm, initial_state)
        self.__analizar_candidatos(system)
        print(
            f"\n{Fore.RED}Generación finalizada!{Fore.BLUE}\n"
            f"Revisa tu directorio `review/resolver/`.\n"
            f"{Fore.WHITE}Tamaño de la red: {initial_state.size} nodos.\n"
            f"Estado inicial: {initial_state}.\n"
        )

    def __analizar_candidatos(self, sistema: System) -> None:
        """Genera y procesa todos los sistemas candidatos de la red.

        Args:
            sistema: Sistema completo que será condicionado según cada
                combinación de dimensiones para formar el candidato.
        """
        cantidad = len(self.tpm.estado_inicial)
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
        """Aplica condiciones de fondo y continúa con el análisis.

        Args:
            completo: Sistema completo a condicionar.
            condiciones: Dimensiones a condicionar (marginalizar).
        """
        candidato = completo.condicionar(condiciones)
        nombre = literales(
            np.setdiff1d(candidato.dims_ncubos, condiciones)
        )
        self.__procesar_subsistema(candidato, nombre)

    def __procesar_subsistema(
        self,
        mecanismo_removido: System,
        nombre_candidato: str,
    ) -> None:
        """Genera todos los subsistemas de un candidato y los analiza.

        Los resultados se guardan en un archivo Excel nombrado con
        ``nombre_candidato`` dentro de ``tpm.output_dir``.

        Args:
            mecanismo_removido: Sistema candidato condicionado.
            nombre_candidato: Nombre amigable del candidato; determina
                el nombre del fichero de salida en ``review/``.
        """
        results_file = (
            self.tpm.output_dir / f"{nombre_candidato}.{EXCEL_EXTENSION}"
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
        """Determina si el subsistema carece de futuro y debe omitirse.

        Un subsistema sin elementos futuros (alcance vacío tras remover
        ``alcance_removido``) no tiene efecto no-trivial y se descarta.

        Args:
            alcance_removido: Índices de las dimensiones a remover del
                alcance.
            candidate: Sistema candidato sobre el que se aplica el
                alcance.

        Returns:
            ``True`` si el alcance removido agota todos los índices del
            candidato (no quedaría futuro); ``False`` en caso contrario.

        Example::

            omitir = bf.__deberia_omitir_subsistema((0, 1), candidato)
        """
        return len(alcance_removido) == candidate.indices_ncubos.size

    def __analizar_subsistema(
        self,
        candidato: System,
        alcance_removido: NDArray[np.int8],
        mecanismo_removido: NDArray[np.int8],
        writer: pd.ExcelWriter,
    ) -> None:
        """Analiza un subsistema candidato y guarda el resultado en Excel.

        Substrae el alcance y mecanismo del candidato, calcula la
        distribución marginal y evalúa todas las particiones posibles,
        guardando la matriz de EMDs en la hoja de cálculo asociada.

        Args:
            candidato: Sistema candidato del que se substrae el
                subsistema.
            alcance_removido: Dimensiones de alcance a marginalizar.
            mecanismo_removido: Dimensiones de mecanismo a marginalizar.
            writer: Escritor de hoja de cálculo Excel ya abierto.
        """
        subsistema = candidato.substraer(
            alcance_removido, mecanismo_removido
        )
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
        """Evalúa todas las biparticiones del subsistema y devuelve matriz de EMDs.

        Para un subsistema ``(m alcances, n mecanismos)`` la cantidad de
        biparticiones factibles es ``2^(m+n-1) - 1``. La partición
        trivial (todas las variables en el mismo lado) se excluye.

        La matriz resultante tiene:

        - Filas: etiquetas binarias de los mecanismos presentes
          (``n`` bits).
        - Columnas: etiquetas binarias de los alcances futuros
          (``m-1`` bits, primera mitad).

        Args:
            distribucion: Distribución marginal original del subsistema,
                usada como referencia para la EMD.
            subsistema: Subsistema sobre el que se realizan las
                biparticiones.

        Returns:
            :class:`pandas.DataFrame` con los valores de EMD para cada
            bipartición, indexado por etiquetas binarias de mecanismo
            (filas) y alcance (columnas).

        Example::

            df = bf.__analizar_particiones(dist, subsistema)
            print(df.shape)
        """
        m = subsistema.indices_ncubos.size
        n = subsistema.dims_ncubos.size

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

            etiqueta_mecanismo = "".join(
                map(str, mecanismo.astype(int))
            )
            etiqueta_alcance = "".join(
                map(str, alcance.astype(int))
            )
            resultados.loc[etiqueta_mecanismo, etiqueta_alcance] = (
                emd_value
            )

        return resultados

    def __get_nombre_subsistema(
        self,
        candidato: System,
        sub_alcance: NDArray[np.int8],
        sub_mecanismo: NDArray[np.int8],
    ) -> str:
        """Genera el nombre literal del subsistema analizado.

        Usa las dimensiones activas del candidato para construir la
        representación ``"<futuro>|<presente>"``.

        Args:
            candidato: Sistema candidato cuyas dimensiones se usan como
                referencia.
            sub_alcance: Alcance (futuros) que será eliminado.
            sub_mecanismo: Mecanismo (presentes) que será eliminado.

        Returns:
            Cadena con la representación literal del subsistema,
            p. ej. ``"ABC|abc"``.

        Example::

            nombre = bf.__get_nombre_subsistema(cand, alc, mec)
        """
        futuro_removido = np.setdiff1d(
            candidato.dims_ncubos, sub_alcance
        )
        presente_removido = np.setdiff1d(
            candidato.dims_ncubos, sub_mecanismo
        )
        return (
            f"{literales(futuro_removido)}"
            f"|{literales(presente_removido)}"
        )
