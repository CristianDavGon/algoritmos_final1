"""Singleton de configuración global para la estrategia GeoMIP.

Centraliza todos los parámetros de ejecución (notación binaria, distancia
métrica, semilla aleatoria y página de red de muestra) en una única instancia
accesible desde cualquier módulo de la estrategia.

Typical usage example::

    from src.models.base.application import aplicacion
    from src.models.enums.distance import MetricDistance
    from src.models.enums.notation import Notation

    aplicacion.set_notacion(Notation.BIG_ENDIAN)
    aplicacion.set_distancia(MetricDistance.MANHATTAN)
"""

from __future__ import annotations

from src.constants.base import ACTIVOS, INACTIVOS
from src.models.enums.distance import MetricDistance
from src.models.enums.notation import Notation


class Application:
    """Singleton de configuración global de la estrategia GeoMIP.

    Almacena y expone los parámetros que controlan el comportamiento de la
    ejecución: notación de indexado, distancia métrica, semilla del generador
    de números aleatorios de NumPy, página de red de muestra y modo de
    estados.

    Attributes:
        pagina_sample_network (str): Etiqueta de la red de muestra a cargar
            desde ``src/samples/``.  Por defecto ``"A"``.
        semilla_numpy (int): Semilla determinista para
            ``numpy.random.default_rng``.  Por defecto ``73``.
        notacion (str): Valor de la notación de indexado activa; corresponde
            a ``Notation.<valor>.value``.  Por defecto ``"little-endian"``.
        modo_estados (bool | int): Indica si se trabaja con estados activos
            (``ACTIVOS``) o inactivos (``INACTIVOS``).  Por defecto
            ``ACTIVOS``.
        distancia_metrica (str): Identificador de la distancia métrica
            empleada en los cálculos de EMD; corresponde a
            ``MetricDistance.<valor>.value``.  Por defecto ``"emd-effect"``.
        profiler_habilitado (bool): Si ``True``, activa el perfilador de
            rendimiento.  Por defecto ``False``.

    Example::

        from src.models.base.application import aplicacion

        aplicacion.set_notacion(Notation.BIG_ENDIAN)
        print(aplicacion.notacion)  # "big-endian"
    """

    def __init__(self) -> None:
        """Inicializa el singleton con los valores predeterminados."""
        self.pagina_sample_network: str = "A"
        self.semilla_numpy: int = 73
        self.notacion: str = Notation.LIL_ENDIAN.value
        self.modo_estados = ACTIVOS
        self.distancia_metrica: str = MetricDistance.EMD_EFECTO.value
        self.profiler_habilitado: bool = False

    def set_notacion(self, tipo: Notation) -> None:
        """Establece la notación de indexado activa.

        Args:
            tipo: Miembro de :class:`~src.models.enums.notation.Notation`
                que representa la notación binaria deseada (p. ej.
                ``Notation.BIG_ENDIAN``).

        Example::

            aplicacion.set_notacion(Notation.GRAY_CODE)
        """
        self.notacion = tipo

    def set_distancia(self, tipo: MetricDistance) -> None:
        """Establece la distancia métrica para los cálculos de EMD.

        Args:
            tipo: Miembro de
                :class:`~src.models.enums.distance.MetricDistance` que
                representa la distancia deseada (p. ej.
                ``MetricDistance.MANHATTAN``).

        Example::

            aplicacion.set_distancia(MetricDistance.EUCLIDIANA)
        """
        self.distancia_metrica = tipo

    def set_estados_activos(self) -> None:
        """Configura el modo de estados en activos (``ACTIVOS``).

        Example::

            aplicacion.set_estados_activos()
        """
        self.modo_estados = ACTIVOS

    def set_estados_inactivos(self) -> None:
        """Configura el modo de estados en inactivos (``INACTIVOS``).

        Example::

            aplicacion.set_estados_inactivos()
        """
        self.modo_estados = INACTIVOS


# Instancia singleton accesible globalmente dentro de la estrategia GeoMIP
aplicacion = Application()
