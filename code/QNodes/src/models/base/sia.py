"""Clase base abstracta SIA para estrategias de análisis de información integrada.

Este módulo define la clase :class:`SIA` (Strategy + Template Method), raíz
de todos los algoritmos de análisis de sistemas causales implementados en
QNodes.  Cualquier estrategia concreta debe heredar de ``SIA`` e implementar
:meth:`aplicar_estrategia`.

A diferencia de la versión GeoMIP, aquí la TPM se inyecta directamente en
el constructor y el estado inicial se recibe como parámetro de
:meth:`sia_preparar_subsistema`.

Typical usage example::

    class MiEstrategia(SIA):
        def aplicar_estrategia(self):
            self.sia_preparar_subsistema(
                estado_inicial="101",
                condicion="111",
                alcance="110",
                mecanismo="101",
            )
            # … lógica de bipartición …

    estrategia = MiEstrategia(tpm=mi_tpm)
    estrategia.aplicar_estrategia()
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as NDArray

from src.constants.base import (
    COLS_IDX,
    FLOAT_ZERO,
    STR_ZERO,
)
from src.constants.error import ERROR_ESPACIOS_INCOMPATIBLES
from src.constants.models import SIA_PREPARATION_TAG
from src.middlewares.slogger import SafeLogger
from src.models.core.system import System


class SIA(ABC):
    """Clase abstracta base para las estrategias de análisis de sistemas causales.

    Define el contrato (Strategy) y el flujo común (Template Method) que
    comparten todos los algoritmos de búsqueda de bipartición mínima según
    IIT 4.0 en la estrategia QNodes.

    A diferencia de ``GeoMIP.SIA``, la TPM se inyecta en el constructor y
    el estado inicial se pasa en cada llamada a
    :meth:`sia_preparar_subsistema`, lo que permite reutilizar la instancia
    con distintos estados iniciales sin recargar la matriz.

    Attributes:
        tpm (np.ndarray): Matriz de Probabilidades de Transición con forma
            ``(estados, variables)``.  Se inyecta al construir la instancia.
        sia_logger (SafeLogger): Logger no bloqueante que escribe en
            ``logs/<fecha>/<hora>/``.  No afecta el rendimiento de la
            ejecución principal.
        sia_subsistema (System): Subsistema resultante de aplicar condiciones
            de fondo y substracción; se almacena para reutilización durante
            el particionamiento.
        sia_dists_marginales (np.ndarray): Distribuciones marginales del
            subsistema; se reutilizan en los cálculos de EMD.
        sia_tiempo_inicio (float): Marca de tiempo (``time.time()``) al
            finalizar la preparación del subsistema.

    Example::

        class Concreta(SIA):
            def aplicar_estrategia(self):
                self.sia_preparar_subsistema(
                    "101", "111", "110", "101"
                )
        Concreta(tpm=mi_tpm).aplicar_estrategia()
    """

    def __init__(self, tpm: np.ndarray) -> None:
        """Inicializa la instancia con la TPM del sistema.

        Args:
            tpm: Matriz de Probabilidades de Transición con forma
                ``(estados, variables)``.  Se valida implícitamente al
                construir el :class:`~src.models.core.system.System`.
        """
        self.tpm = tpm
        self.sia_logger = SafeLogger(SIA_PREPARATION_TAG)

        self.sia_subsistema: System
        self.sia_dists_marginales: NDArray[np.float32]
        self.sia_tiempo_inicio: float = FLOAT_ZERO

    @abstractmethod
    def aplicar_estrategia(self) -> None:
        """Ejecuta el algoritmo concreto de bipartición mínima.

        Las subclases deben implementar aquí su metodología específica para
        resolver el problema de mínima información integrada (Φ).

        Raises:
            NotImplementedError: Si la subclase no implementa este método.
        """

    # ------------------------------------------------------------------
    # Métodos de plantilla (Template Method)
    # ------------------------------------------------------------------

    def sia_preparar_subsistema(
        self,
        estado_inicial: str,
        condicion: str,
        alcance: str,
        mecanismo: str,
    ) -> None:
        """Construye el subsistema candidato listo para ser biparticionado.

        Aplica el siguiente flujo:

        1. Valida que ``estado_inicial``, ``condicion``, ``alcance`` y
           ``mecanismo`` tengan la misma longitud que la dimensión de la TPM.
        2. Convierte las cadenas de bits en arrays de índices de dimensión.
        3. Crea el sistema completo a partir de la TPM y el estado inicial.
        4. Aplica condiciones de fondo (*background conditions*) para obtener
           el sistema candidato.
        5. Substrae dimensiones de alcance y mecanismo para obtener el
           subsistema mínimo.
        6. Almacena el subsistema, sus distribuciones marginales y la marca
           de tiempo de inicio.

        Args:
            estado_inicial: Cadena de bits que describe el estado actual del
                sistema (p. ej. ``"101"`` para 3 variables).  Debe tener la
                misma longitud que el número de variables de la TPM.
            condicion: Cadena de bits del mismo largo que ``estado_inicial``.
                Los bits en ``'0'`` indican las variables a condicionar
                (fijarlas al valor del estado inicial).
            alcance: Cadena de bits; los bits en ``'0'`` indican variables a
                marginalizar en el alcance (futuro) del candidato.
            mecanismo: Cadena de bits; los bits en ``'0'`` indican variables
                a marginalizar en el mecanismo (presente) del candidato.

        Raises:
            Exception: Si alguna de las cadenas tiene una longitud distinta
                al número de columnas de la TPM.

        Example::

            instancia.sia_preparar_subsistema(
                estado_inicial="101",
                condicion="111",
                alcance="110",
                mecanismo="101",
            )
        """
        if self.chequear_parametros(
            estado_inicial, condicion, alcance, mecanismo
        ):
            raise Exception(ERROR_ESPACIOS_INCOMPATIBLES)

        # Índices de variables a condicionar (bit == '0')
        dims_condicionadas = np.array(
            [
                ind
                for ind, bit in enumerate(condicion)
                if bit == STR_ZERO
            ],
            dtype=np.int8,
        )
        # Índices de variables a marginalizar en el alcance (bit == '0')
        dims_alcance = np.array(
            [
                ind
                for ind, bit in enumerate(alcance)
                if bit == STR_ZERO
            ],
            dtype=np.int8,
        )
        # Índices de variables a marginalizar en el mecanismo (bit == '0')
        dims_mecanismo = np.array(
            [
                ind
                for ind, bit in enumerate(mecanismo)
                if bit == STR_ZERO
            ],
            dtype=np.int8,
        )
        dims_estado_inicial = np.array(
            [int(bit) for bit in estado_inicial],
            dtype=np.int8,
        )

        completo = System(self.tpm, dims_estado_inicial)

        candidato = completo.condicionar(dims_condicionadas)
        self.sia_logger.critic("Sistema candidato creado.")

        subsistema = candidato.substraer(dims_alcance, dims_mecanismo)
        self.sia_logger.critic("Subsistema creado.")

        self.sia_subsistema = subsistema
        self.sia_dists_marginales = subsistema.distribucion_marginal()
        self.sia_tiempo_inicio = time.time()

    def chequear_parametros(
        self,
        estado_inicial: str,
        candidato: str,
        futuro: str,
        presente: str,
    ) -> bool:
        """Valida que los parámetros de preparación sean compatibles.

        Comprueba que ``estado_inicial``, ``candidato``, ``futuro`` y
        ``presente`` tengan la misma longitud que el número de columnas de
        la TPM (``tpm[COLS_IDX]``).  Si todas las longitudes coinciden, los
        parámetros son válidos.

        Args:
            estado_inicial: Cadena de bits del estado actual del sistema.
            candidato: Cadena de bits para las variables a condicionar.
                Un ``'1'`` conserva la variable; un ``'0'`` la condiciona.
            futuro: Cadena de bits para las variables del alcance.
                Un ``'1'`` conserva la variable; un ``'0'`` la marginaliza.
            presente: Cadena de bits para las variables del mecanismo.
                Un ``'1'`` conserva la variable; un ``'0'`` la marginaliza.

        Returns:
            ``True`` si alguna longitud difiere (parámetros inválidos);
            ``False`` si todas las longitudes son iguales (parámetros
            válidos).

        Example::

            invalido = instancia.chequear_parametros("10", "111", "110", "101")
            # invalido == True  →  longitudes inconsistentes
        """
        return not (
            len(self.tpm[COLS_IDX])
            == len(estado_inicial)
            == len(candidato)
            == len(futuro)
            == len(presente)
        )
