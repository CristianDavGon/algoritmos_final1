"""Middleware de logging estructurado para GeoMIP.

Provee ``SafeLogger``, un wrapper sobre ``logging.Logger`` que:

* Garantiza codificación UTF-8 en todos los handlers.
* Aplica colores ANSI a la salida de consola mediante *colorama*.
* Organiza los archivos de log por fecha y hora de ejecución.
* Convierte de forma segura cualquier objeto a ``str`` antes de emitir.

Typical usage example::

    from src.middlewares.slogger import get_logger

    log = get_logger("mi_modulo")
    log.info("Iniciando análisis con", n_nodos, "nodos")
    log.error("Fallo al leer red:", exc)
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from colorama import Fore, Style, init

from src.constants.base import LOGS_PATH

# ---------------------------------------------------------------------------
# Inicialización única de colorama
# ---------------------------------------------------------------------------
_COLORAMA_INITIALIZED: bool = False


def _init_colorama_once() -> None:
    """Inicializa colorama una sola vez por proceso."""
    global _COLORAMA_INITIALIZED
    if not _COLORAMA_INITIALIZED:
        init(autoreset=True)
        _COLORAMA_INITIALIZED = True


# ---------------------------------------------------------------------------
# Formatter con colores para consola
# ---------------------------------------------------------------------------

class ColorFormatter(logging.Formatter):
    """Formatter para consola que aplica colores ANSI por nivel de log.

    Utiliza *colorama* para compatibilidad con terminales Windows y POSIX.
    Los colores se aplican únicamente al nombre del nivel, preservando el
    resto del mensaje sin modificaciones.

    Attributes:
        COLORS: Mapeo de nivel de log a código de color ANSI.

    Example::

        handler = logging.StreamHandler()
        handler.setFormatter(
            ColorFormatter("%(levelname)s: %(message)s")
        )
    """

    COLORS: dict[int, str] = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,          # gris
        logging.INFO: Fore.BLUE,                     # azul
        logging.WARNING: Fore.YELLOW,                # amarillo
        logging.ERROR: Fore.RED,                     # rojo
        logging.CRITICAL: Fore.MAGENTA,              # magenta
        logging.FATAL: Fore.RED + Style.BRIGHT,      # rojo brillante
    }

    def __init__(self, *args, **kwargs) -> None:
        """Inicializa el formatter y activa colorama si aún no lo está."""
        super().__init__(*args, **kwargs)
        _init_colorama_once()

    def format(self, record: logging.LogRecord) -> str:
        """Formatea el registro aplicando color al nombre del nivel.

        Args:
            record: Registro de log a formatear.

        Returns:
            Cadena formateada con el nombre del nivel coloreado.
        """
        color = self.COLORS.get(record.levelno, "")
        # Guarda el nombre del nivel original para restaurarlo después
        original_levelname = record.levelname
        # Aplica el color al nombre del nivel
        record.levelname = (
            f"{color}{original_levelname}{Style.RESET_ALL}"
        )
        # Formato del mensaje
        formatted = super().format(record)
        # Restaura el nombre del nivel original
        record.levelname = original_levelname
        return formatted


# ---------------------------------------------------------------------------
# Logger seguro
# ---------------------------------------------------------------------------

class SafeLogger:
    """Logger robusto con soporte UTF-8 y salida estructurada por fecha.

    Crea automáticamente la jerarquía de directorios
    ``<LOGS_PATH>/DD_MM_YYYY/HHhrs/<name>.log`` y un archivo
    ``last_<name>.log`` en el directorio raíz para acceso rápido al
    último log.

    Attributes:
        _logger: Instancia interna de ``logging.Logger``.

    Example::

        log = SafeLogger("geomip.solver")
        log.info("Red cargada con", n, "nodos")
        log.error("Partición inválida:", detalle)
    """

    def __init__(self, name: str) -> None:
        """Inicializa el logger y sus handlers.

        Args:
            name: Nombre del logger (se usa como nombre de archivo).
        """
        self._logger: logging.Logger = self.__setup_logger(name)

    # ------------------------------------------------------------------
    # Métodos privados de soporte
    # ------------------------------------------------------------------

    def _safe_str(self, obj: Any) -> str:
        """Convierte cualquier objeto a ``str`` de forma segura.

        Para colecciones usa ``str()`` directamente.  Para cualquier
        otro objeto aplica codificación UTF-8 con reemplazo de
        caracteres inválidos.

        Args:
            obj: Objeto a convertir.

        Returns:
            Representación textual del objeto, nunca lanza excepción.
        """
        try:
            if isinstance(obj, (list, tuple, set, dict)):
                return str(obj)
            return (
                str(obj)
                .encode("utf-8", errors="replace")
                .decode("utf-8")
            )
        except Exception:
            return "[Objeto no representable]"

    def _safe_format(self, *args, **kwargs) -> str:
        """Concatena args y kwargs en un único mensaje seguro.

        Args:
            *args: Valores posicionales a incluir en el mensaje.
            **kwargs: Pares clave=valor a adjuntar al mensaje.

        Returns:
            Cadena con todos los argumentos separados por espacios.
        """
        args_str = " ".join(self._safe_str(arg) for arg in args)
        if kwargs:
            kwargs_str = " ".join(
                f"{k}={self._safe_str(v)}"
                for k, v in kwargs.items()
            )
            return f"{args_str} {kwargs_str}"
        return args_str

    def __setup_logger(self, name: str) -> logging.Logger:
        """Configura handlers de archivo y consola para el logger.

        Si el logger ya posee handlers (fue configurado previamente),
        lo devuelve sin modificaciones para evitar duplicados.

        Args:
            name: Nombre del logger (igual que el nombre de archivo).

        Returns:
            Instancia de ``logging.Logger`` completamente configurada.
        """
        logger = logging.getLogger(name)
        # Si el logger ya fue configurado, reutilizarlo sin crear
        # directorios ni handlers nuevos
        if logger.handlers:
            return logger

        # Crear estructura de directorios para logs detallados
        base_log_dir = Path(LOGS_PATH)
        base_log_dir.mkdir(exist_ok=True)

        current_time = datetime.now()
        date_dir = base_log_dir / current_time.strftime("%d_%m_%Y")
        date_dir.mkdir(exist_ok=True)

        hour_dir = date_dir / f"{current_time.strftime('%H')}hrs"
        hour_dir.mkdir(exist_ok=True)

        # Archivo para logs detallados (organizados por sesión)
        detailed_log_file = hour_dir / f"{name}.log"
        # Archivo para el último log (acceso rápido)
        last_log_file = base_log_dir / f"last_{name}.log"

        logger.setLevel(logging.ERROR)
        # Evita la propagación a loggers padre
        logger.propagate = False

        # Formatter para archivos (sin colores)
        plain_formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s "
            "%(processName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Formatter para consola (con colores y formato reducido)
        colored_formatter = ColorFormatter(
            "%(levelname)s (%(asctime)s): %(message)s",
            datefmt="%H:%M:%S",
        )

        # Handler para archivo detallado
        detailed_file_handler = logging.FileHandler(
            detailed_log_file, mode="w", encoding="utf-8"
        )
        detailed_file_handler.setLevel(logging.DEBUG)
        detailed_file_handler.setFormatter(plain_formatter)

        # Handler para el archivo "last" (sobrescribe cada ejecución)
        last_file_handler = logging.FileHandler(
            last_log_file, mode="w", encoding="utf-8"
        )
        last_file_handler.setLevel(logging.DEBUG)
        last_file_handler.setFormatter(plain_formatter)

        # Handler para consola (muestra todos los niveles)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(colored_formatter)

        logger.addHandler(detailed_file_handler)
        logger.addHandler(last_file_handler)
        logger.addHandler(console_handler)

        return logger

    # ------------------------------------------------------------------
    # API pública de logging
    # ------------------------------------------------------------------

    def set_log(self, level: int, *args, **kwargs) -> None:
        """Emite un mensaje al nivel indicado.

        Args:
            level: Constante de nivel (``logging.DEBUG``, etc.).
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        message = self._safe_format(*args, **kwargs)
        self._logger.log(level, message)

    def debug(self, *args, **kwargs) -> None:
        """Emite un mensaje a nivel DEBUG.

        Args:
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        self.set_log(logging.DEBUG, *args, **kwargs)

    def info(self, *args, **kwargs) -> None:
        """Emite un mensaje a nivel INFO.

        Args:
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        self.set_log(logging.INFO, *args, **kwargs)

    def warn(self, *args, **kwargs) -> None:
        """Emite un mensaje a nivel WARNING.

        Args:
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        self.set_log(logging.WARNING, *args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        """Emite un mensaje a nivel ERROR.

        Args:
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        self.set_log(logging.ERROR, *args, **kwargs)

    def critic(self, *args, **kwargs) -> None:
        """Emite un mensaje a nivel CRITICAL.

        Args:
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        self.set_log(logging.CRITICAL, *args, **kwargs)

    def fatal(self, *args, **kwargs) -> None:
        """Emite un mensaje a nivel FATAL.

        Args:
            *args: Partes del mensaje.
            **kwargs: Pares clave=valor adicionales.
        """
        self.set_log(logging.FATAL, *args, **kwargs)


# ---------------------------------------------------------------------------
# Funciones de conveniencia
# ---------------------------------------------------------------------------

def get_logger(name: str) -> SafeLogger:
    """Crea y devuelve una instancia de ``SafeLogger``.

    Args:
        name: Nombre del logger (generalmente ``__name__`` del módulo).

    Returns:
        Instancia configurada de ``SafeLogger``.

    Example::

        log = get_logger(__name__)
        log.info("Módulo inicializado")
    """
    return SafeLogger(name)


def log_execution(logger: SafeLogger) -> Callable:
    """Decorador que registra el inicio y fin de una función.

    Emite mensajes DEBUG al entrar y salir de la función decorada.
    En caso de excepción, emite ERROR y la relanza.

    Args:
        logger: Instancia de ``SafeLogger`` a utilizar.

    Returns:
        Decorador aplicable a cualquier función callable.

    Example::

        log = get_logger("solver")

        @log_execution(log)
        def resolver(sistema):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.debug(f"Iniciando {func.__name__}")
                result = func(*args, **kwargs)
                logger.debug(f"Completado {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}")
                raise

        return wrapper

    return decorator
