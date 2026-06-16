"""Singleton de configuración global para la estrategia QNodes.

Centraliza todos los parámetros de ejecución (notación de indexado,
distancia métrica, tiempo de EMD, semilla aleatoria, página de red de
muestra y modo de estados) en una única instancia accesible desde cualquier
módulo de la estrategia.

Typical usage example::

    from src.models.base.application import aplicacion
    from src.models.enums.distance import MetricDistance
    from src.models.enums.notation import Notation
    from src.models.enums.temporal_emd import TimeEMD

    aplicacion.set_notacion(Notation.BIG_ENDIAN)
    aplicacion.set_distancia(MetricDistance.HAMMING)
    aplicacion.set_tiempo_emd(TimeEMD.EMD_INTEGRADA)
"""

from __future__ import annotations

from src.constants.base import ABC_START, ACTIVE, INACTIVE
from src.models.enums.distance import MetricDistance
from src.models.enums.notation import Notation
from src.models.enums.temporal_emd import TimeEMD


class Application:
    """Singleton de configuración global de la estrategia QNodes.

    Almacena y expone los parámetros que controlan el comportamiento de la
    ejecución: notación de indexado, distancia métrica, dirección temporal
    de la EMD, semilla del generador de números aleatorios de NumPy, página
    de red de muestra y modo de estados.

    Los datasets ubicados en ``src/samples/`` ya están indexados en
    little-endian; si la notación configurada coincide con la de llegada no
    se re-indexan.

    Attributes:
        semilla_numpy (int): Semilla determinista para
            ``numpy.random.default_rng``.  Por defecto ``73``.
        pagina_red_muestra (str): Etiqueta de la red de muestra a cargar
            desde ``src/samples/``.  Por defecto el valor de
            ``ABC_START`` (``"A"``).
        distancia_metrica (str): Identificador de la distancia métrica
            empleada; corresponde a ``MetricDistance.<valor>.value``.
            Por defecto ``"distancia-hamming"``.
        indexado_llegada (str): Notación con que están indexados los
            datasets en disco.  Por defecto ``"little-endian"``.
        notacion_indexado (str): Notación de indexado activa para la
            ejecución.  Si difiere de ``indexado_llegada`` se re-indexa el
            dataset.  Por defecto ``"little-endian"``.
        tiempo_emd (str): Dirección temporal de la EMD; corresponde a
            ``TimeEMD.<valor>.value``.  Por defecto ``"emd-effect"``.
        modo_estados (bool): Indica si se trabaja con estados activos
            (``ACTIVE``) o inactivos (``INACTIVE``).  Por defecto
            ``ACTIVE``.
        profiler_habilitado (bool): Si ``True``, activa el perfilador de
            rendimiento que escribe en ``../../../review/profiling/``.
            Por defecto ``True``.

    Example::

        from src.models.base.application import aplicacion

        aplicacion.set_tiempo_emd(TimeEMD.EMD_INTEGRADA)
        print(aplicacion.tiempo_emd)  # "emd-cause-effect"
    """

    def __init__(self) -> None:
        """Inicializa el singleton con los valores predeterminados."""
        self.semilla_numpy: int = 73
        self.pagina_red_muestra: str = ABC_START
        self.distancia_metrica: str = MetricDistance.HAMMING.value
        self.indexado_llegada: str = Notation.LIL_ENDIAN.value
        self.notacion_indexado: str = Notation.LIL_ENDIAN.value
        self.tiempo_emd: str = TimeEMD.EMD_EFECTO.value
        self.modo_estados: bool = ACTIVE
        self.profiler_habilitado: bool = True

    def set_pagina_red_muestra(self, pagina: str) -> None:
        """Establece la página de red de muestra a cargar.

        Args:
            pagina: Etiqueta de la red (p. ej. ``"B"``).

        Example::

            aplicacion.set_pagina_red_muestra("C")
        """
        self.pagina_red_muestra = pagina

    def set_notacion(self, tipo: Notation) -> None:
        """Establece la notación de indexado activa.

        Normaliza siempre a cadena para evitar choques entre el enum y su
        ``.value``.

        Args:
            tipo: Miembro de :class:`~src.models.enums.notation.Notation`
                que representa la notación binaria deseada.

        Example::

            aplicacion.set_notacion(Notation.GRAY_CODE)
        """
        self.notacion_indexado = (
            tipo.value if isinstance(tipo, Notation) else str(tipo)
        )

    def set_distancia(self, tipo: MetricDistance) -> None:
        """Establece la distancia métrica para los cálculos de EMD.

        Normaliza siempre a cadena para evitar choques entre el enum y su
        ``.value``.

        Args:
            tipo: Miembro de
                :class:`~src.models.enums.distance.MetricDistance` que
                representa la distancia deseada.

        Example::

            aplicacion.set_distancia(MetricDistance.EUCLIDIANA)
        """
        self.distancia_metrica = (
            tipo.value if isinstance(tipo, MetricDistance) else str(tipo)
        )

    def set_estados_activos(self) -> None:
        """Configura el modo de estados en activos (``ACTIVE``).

        Example::

            aplicacion.set_estados_activos()
        """
        self.modo_estados = ACTIVE

    def set_estados_inactivos(self) -> None:
        """Configura el modo de estados en inactivos (``INACTIVE``).

        Example::

            aplicacion.set_estados_inactivos()
        """
        self.modo_estados = INACTIVE

    def set_tiempo_emd(self, tipo: TimeEMD) -> None:
        """Establece la dirección temporal de la EMD.

        Normaliza siempre a cadena para evitar choques entre el enum y su
        ``.value``.

        Args:
            tipo: Miembro de
                :class:`~src.models.enums.temporal_emd.TimeEMD` que
                representa la dirección temporal deseada (efecto, causa o
                integrada).

        Example::

            aplicacion.set_tiempo_emd(TimeEMD.EMD_CAUSA)
        """
        self.tiempo_emd = (
            tipo.value if isinstance(tipo, TimeEMD) else str(tipo)
        )

    def set_distancia_metrica(self, tipo: MetricDistance) -> None:
        """Alias de :meth:`set_distancia` para compatibilidad.

        Normaliza siempre a cadena para evitar choques entre el enum y su
        ``.value``.

        Args:
            tipo: Miembro de
                :class:`~src.models.enums.distance.MetricDistance` que
                representa la distancia deseada.

        Example::

            aplicacion.set_distancia_metrica(MetricDistance.MANHATTAN)
        """
        self.distancia_metrica = (
            tipo.value if isinstance(tipo, MetricDistance) else str(tipo)
        )

    def activar_profiling(self) -> None:
        """Activa el perfilador de rendimiento.

        Los resultados se guardan en ``../../../review/profiling/``.

        Example::

            aplicacion.activar_profiling()
        """
        self.profiler_habilitado = True

    def desactivar_profiling(self) -> None:
        """Desactiva el perfilador de rendimiento.

        Example::

            aplicacion.desactivar_profiling()
        """
        self.profiler_habilitado = False


# Instancia singleton accesible globalmente dentro de la estrategia QNodes
aplicacion = Application()
