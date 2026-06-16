"""Middleware de perfilado de rendimiento para GeoMIP.

Provee ``ProfilingManager``, ``ProfilerContext`` y el decorador
``profile`` para medir el tiempo de ejecución y generar reportes
HTML detallados con *pyinstrument*.

El perfilado se activa/desactiva mediante
``aplicacion.profiler_habilitado``.  Cuando está deshabilitado, el
decorador ``profile`` no añade overhead medible.

Typical usage example::

    from src.middlewares.profile import profile, profiler_manager

    profiler_manager.start_session("analisis_phi")

    @profile(name="calcular_phi")
    def calcular_phi(sistema):
        ...
"""

from __future__ import annotations

import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from pyinstrument import Profiler
from pyinstrument.renderers import HTMLRenderer

from src.constants.base import HTML_EXTENSION, PROFILING_PATH
from src.models.base.application import aplicacion


class ProfilingManager:
    """Gestor central de perfilado: mantiene configuración y sesión activa.

    Attributes:
        enabled: Indica si el perfilado está habilitado en esta instancia.
        output_dir: Directorio raíz donde se almacenan los reportes HTML.
        interval: Intervalo de muestreo en segundos para *pyinstrument*.
        current_session: Ruta relativa de la sesión activa (o ``None``).

    Example::

        gestor = ProfilingManager(habilitado=True)
        gestor.start_session("experimento_01")
        ruta = gestor.get_output_path("calcular_phi", "html")
    """

    def __init__(
        self,
        habilitado: bool = aplicacion.profiler_habilitado,
        dir_salida: Path = Path(PROFILING_PATH),
        intervalo: float = 0.001,
    ) -> None:
        """Inicializa el gestor de perfilado.

        Args:
            habilitado: Activa o desactiva el perfilado.
                Por defecto toma el valor de
                ``aplicacion.profiler_habilitado``.
            dir_salida: Directorio donde se guardarán los reportes.
            intervalo: Intervalo de muestreo en segundos
                (resolución del profiler).
        """
        self.enabled: bool = habilitado
        self.output_dir: Path = dir_salida
        self.interval: float = intervalo
        self.current_session: str | None = None
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Crea el directorio de salida si el perfilado está habilitado."""
        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def start_session(self, session_name: str) -> None:
        """Abre una sesión de perfilado organizada por fecha y hora.

        Crea la estructura ``<output_dir>/<session_name>/DD_MM_YYYY/HHhrs``
        y registra la ruta relativa como sesión activa.

        Args:
            session_name: Nombre lógico de la sesión
                (p. ej. ``"analisis_red_5"``).
        """
        if self.enabled:
            timestamp = datetime.now().strftime("%d_%m_%Y/%Hhrs")
            session_path = (
                self.output_dir / session_name / timestamp
            )
            session_path.mkdir(parents=True, exist_ok=True)
            self.current_session = str(
                session_path.relative_to(self.output_dir)
            )

    def get_output_path(self, name: str, format: str) -> Path:
        """Genera la ruta de salida para un reporte de perfil.

        Args:
            name: Nombre del perfil (generalmente el nombre de la función).
            format: Extensión del archivo sin punto (p. ej. ``"html"``).

        Returns:
            Ruta absoluta al archivo de reporte dentro del directorio
            de la sesión activa (o ``"default"`` si no hay sesión).
        """
        session_dir = self.current_session or "default"
        return self.output_dir / session_dir / f"{name}.{format}"


class ProfilerContext:
    """Gestor de contexto que encapsula la medición de una función.

    Inicia el profiler al entrar (``__enter__``) y genera el reporte
    HTML al salir (``__exit__``).  Si el gestor está deshabilitado,
    ambos métodos son no-ops.

    Attributes:
        manager: Referencia al ``ProfilingManager`` configurado.
        name: Identificador del perfil que se guardará.
        context: Metadatos adicionales (args/kwargs de la función).
        start_time: Marca de tiempo de inicio (``perf_counter``).
        profiler: Instancia de ``pyinstrument.Profiler`` o ``None``.

    Example::

        with ProfilerContext(gestor, "mi_funcion", {}) as ctx:
            resultado = mi_funcion()
    """

    def __init__(
        self,
        manager: ProfilingManager,
        name: str,
        context: dict,
    ) -> None:
        """Inicializa el contexto de perfilado.

        Args:
            manager: Gestor de perfilado activo.
            name: Nombre del perfil a registrar.
            context: Diccionario con metadatos de la ejecución.
        """
        self.manager: ProfilingManager = manager
        self.name: str = name
        self.context: dict = context
        self.start_time: float | None = None
        self.profiler: Profiler | None = (
            None
            if not manager.enabled
            else Profiler(
                interval=manager.interval,
                async_mode="disabled",
            )
        )

    def __enter__(self) -> ProfilerContext:
        """Inicia la medición si el perfilado está habilitado.

        Returns:
            La propia instancia de contexto.
        """
        if self.manager.enabled:
            self.start_time = time.perf_counter()
            self.profiler.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Detiene el profiler y escribe el reporte HTML.

        Args:
            exc_type: Tipo de excepción (si ocurrió alguna).
            exc_val: Valor de la excepción.
            exc_tb: Traceback de la excepción.
        """
        if not self.manager.enabled:
            return

        self.profiler.stop()

        # Generar reporte HTML detallado con línea de tiempo
        html_path = self.manager.get_output_path(
            self.name, HTML_EXTENSION
        )
        with open(html_path, "w") as f:
            f.write(
                self.profiler.output(
                    renderer=HTMLRenderer(
                        show_all=True,
                        timeline=True,
                    )
                )
            )


# Instancia global del gestor (singleton de módulo)
profiler_manager = ProfilingManager()


def profile(
    name: str | None = None,
    context: dict | None = None,
) -> Callable:
    """Decorador para perfilar funciones con pyinstrument.

    Envuelve la función objetivo en un ``ProfilerContext``.  Si el
    perfilado está deshabilitado, la función se ejecuta sin overhead.

    Al usar este decorador en un método, agregar la nota en su
    docstring::

        Note:
            Decorada con ``@profile``; genera reporte HTML en
            ``review/profiling``.

    Args:
        name: Nombre personalizado del perfil.  Si es ``None``,
            se usa ``func.__name__``.
        context: Diccionario con metadatos adicionales que se
            adjuntan al registro del perfil.

    Returns:
        Decorador que envuelve la función en un contexto de perfilado.

    Example::

        @profile(name="phi_calculo")
        def calcular_phi(sistema):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not profiler_manager.enabled:
                return func(*args, **kwargs)

            profile_name = name or func.__name__
            profile_context = {
                **(context or {}),
                "args": str(args),
                "kwargs": str(kwargs),
            }

            with ProfilerContext(
                profiler_manager,
                profile_name,
                profile_context,
            ):
                return func(*args, **kwargs)

        return wrapper

    return decorator
