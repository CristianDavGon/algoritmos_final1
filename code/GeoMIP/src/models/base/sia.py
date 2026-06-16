"""Clase base abstracta SIA para estrategias de análisis de información integrada.

Este módulo define la clase :class:`SIA` (Strategy + Template Method), raíz
de todos los algoritmos de análisis de sistemas causales implementados en
GeoMIP.  Cualquier estrategia concreta debe heredar de ``SIA`` e implementar
:meth:`aplicar_estrategia`.

Typical usage example::

    class MiEstrategia(SIA):
        def aplicar_estrategia(self):
            self.sia_preparar_subsistema(
                condicion="111",
                alcance="110",
                mecanismo="101",
                tpm=mi_tpm,
            )
            # … lógica de bipartición …

    estrategia = MiEstrategia(gestor)
    estrategia.aplicar_estrategia()
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as NDArray

from src.constants.base import (
    COLON_DELIM,
    FLOAT_ZERO,
    STR_ZERO,
)
from src.constants.error import ERROR_INCOMPATIBLE_SIZES
from src.constants.models import SIA_PREPARATION_TAG
from src.controllers.manager import Manager
from src.middlewares.slogger import SafeLogger
from src.models.core.system import System


class SIA(ABC):
    """Clase abstracta base para las estrategias de análisis de sistemas causales.

    Define el contrato (Strategy) y el flujo común (Template Method) que
    comparten todos los algoritmos de búsqueda de bipartición mínima según
    IIT 4.0.

    Attributes:
        sia_gestor (Manager): Gestor que encapsula la ruta de la TPM y el
            estado inicial como cadena de bits.  El estado inicial se
            transforma a ``np.ndarray`` de ``int8`` antes de usarse.
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

        gestor = Manager(tpm_filename="red.csv", estado_inicial="101")
        class Concreta(SIA):
            def aplicar_estrategia(self):
                tpm = self.sia_cargar_tpm()
                self.sia_preparar_subsistema("111", "110", "101", tpm)
        Concreta(gestor).aplicar_estrategia()
    """

    def __init__(self, gestor: Manager) -> None:
        """Inicializa la instancia con el gestor de datos.

        Args:
            gestor: Gestor que provee la ruta de la TPM y el estado inicial
                codificado como cadena de bits (p. ej. ``"101"``).
        """
        self.sia_gestor = gestor
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

    def sia_cargar_tpm(self) -> np.ndarray:
        """Carga la Matriz de Probabilidades de Transición desde disco.

        Lee el archivo CSV delimitado por ``COLON_DELIM`` indicado en
        ``sia_gestor.tpm_filename``.

        Returns:
            Matriz TPM como ``np.ndarray`` de forma ``(estados, variables)``.

        Example::

            tpm = instancia.sia_cargar_tpm()
            # tpm.shape == (8, 3) para una red de 3 variables
        """
        return np.loadtxt(
            self.sia_gestor.tpm_filename,
            delimiter=COLON_DELIM,
        )

    def sia_preparar_subsistema(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray,
    ) -> None:
        """Construye el subsistema candidato listo para ser biparticionado.

        Aplica el siguiente flujo:

        1. Valida que ``condicion``, ``alcance`` y ``mecanismo`` tengan la
           misma longitud que el estado inicial.
        2. Convierte las cadenas de bits en índices de dimensión.
        3. Crea el sistema completo a partir de la TPM y el estado inicial.
        4. Aplica condiciones de fondo (*background conditions*) para obtener
           el sistema candidato.
        5. Substrae dimensiones de alcance y mecanismo para obtener el
           subsistema mínimo.
        6. Almacena el subsistema, sus distribuciones marginales y la marca
           de tiempo de inicio.

        Args:
            condicion: Cadena de bits del mismo largo que el estado inicial.
                Los bits en ``'0'`` indican las variables a condicionar
                (fijarlas al valor del estado inicial).
            alcance: Cadena de bits; los bits en ``'0'`` indican variables a
                marginalizar en el alcance (futuro) del candidato.
            mecanismo: Cadena de bits; los bits en ``'0'`` indican variables
                a marginalizar en el mecanismo (presente) del candidato.
            tpm: Matriz de probabilidades de transición con forma
                ``(estados, variables)``.

        Raises:
            Exception: Si ``condicion``, ``alcance`` o ``mecanismo`` tienen
                una longitud distinta a la del estado inicial almacenado en
                ``sia_gestor``.

        Example::

            instancia.sia_preparar_subsistema(
                condicion="111",
                alcance="110",
                mecanismo="101",
                tpm=np.loadtxt("red.csv", delimiter=","),
            )
        """
        if self.chequear_parametros(condicion, alcance, mecanismo):
            raise Exception(ERROR_INCOMPATIBLE_SIZES)

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

        # Preparar directorio de salida
        self.sia_gestor.output_dir.mkdir(parents=True, exist_ok=True)

        estado_inicial = np.array(
            [canal for canal in self.sia_gestor.estado_inicial],
            dtype=np.int8,
        )

        # Reutilizar el sistema completo si ya fue construido previamente
        if not hasattr(self, '_sistema_completo'):
            self._sistema_completo = System(tpm, estado_inicial)
        completo = self._sistema_completo
        self.sia_logger.debug("Sistema original creado.")

        candidato = completo.condicionar(dims_condicionadas)
        self.sia_logger.debug("Sistema candidato creado.")

        subsistema = candidato.substraer(dims_alcance, dims_mecanismo)
        self.sia_logger.debug("Subsistema creado.")

        self.sia_subsistema = subsistema
        self.sia_dists_marginales = subsistema.distribucion_marginal()
        self.sia_tiempo_inicio = time.time()

    def chequear_parametros(
        self,
        candidato: str,
        futuro: str,
        presente: str,
    ) -> bool:
        """Valida que los parámetros de preparación sean compatibles.

        Comprueba que ``candidato``, ``futuro`` y ``presente`` tengan la
        misma longitud que el estado inicial registrado en el gestor.  Si
        todas las longitudes coinciden los parámetros son válidos.

        Args:
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

            invalido = instancia.chequear_parametros("11", "110", "101")
            # invalido == True  →  longitudes inconsistentes
        """
        return not (
            len(self.sia_gestor.estado_inicial)
            == len(candidato)
            == len(futuro)
            == len(presente)
        )
