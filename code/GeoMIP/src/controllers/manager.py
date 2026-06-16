"""Controlador principal de gestión de redes TPM para el módulo GeoMIP.

Proporciona la clase :class:`Manager` que localiza los archivos CSV de
matrices de probabilidad de transición (TPM) almacenados en el directorio
de muestras y establece la ruta de salida para resultados y perfilado.

Typical usage example::

    from src.controllers.manager import Manager

    gestor = Manager(estado_inicial="1010")
    tpm = np.genfromtxt(gestor.tpm_filename, delimiter=",")
    print(gestor.output_dir)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.constants.base import (
    ABC_START,
    COLON_DELIM,
    CSV_EXTENSION,
    RESOLVER_PATH,
    SAMPLES_PATH,
)
from src.models.base.application import aplicacion

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
# Umbral en gigabytes a partir del cual se solicita confirmación al usuario
_UMBRAL_GB: float = 1.0
# Factor para estimar el tiempo de generación (segundos por GB)
_FACTOR_TIEMPO_POR_GB: float = 2.0
# Formato de precisión decimal para TPMs estocásticas
_FMT_FLOAT: str = "%.6f"
# Formato entero para TPMs deterministas
_FMT_INT: str = "%d"
# Divisor para convertir bytes a gigabytes
_BYTES_POR_GB: int = 1024 ** 3


@dataclass
class Manager:
    """Gestor de archivos TPM y directorios de salida para GeoMIP.

    Localiza el fichero CSV de la TPM correspondiente al tamaño del
    sistema (determinado por ``estado_inicial``) dentro de
    ``ruta_base``, y calcula la ruta del directorio donde se
    almacenarán los resultados del resolver y del perfilado.

    La resolución de ``ruta_base`` sigue el siguiente orden de
    prioridad:

    1. Variable de entorno ``GEOMIP_SAMPLES_DIR`` (si existe y apunta
       a un directorio válido).
    2. Rutas canónicas relativas a la raíz del paquete GeoMIP.
    3. Ruta configurada por defecto en ``src/constants/base.py``.

    Attributes:
        estado_inicial: Cadena binaria que representa el estado del
            sistema en ``t``. Su longitud determina el número de nodos
            ``N`` y, por tanto, el archivo ``NXY.csv`` a cargar.
        ruta_base: Directorio donde residen los archivos de muestra
            ``NXY.csv``. Se resuelve automáticamente en
            :meth:`__post_init__`.

    Example::

        gestor = Manager(estado_inicial="101")
        print(gestor.tpm_filename)   # .../N3A.csv
        print(gestor.output_dir)     # review/resolver/N3A/101
    """

    estado_inicial: str
    ruta_base: Path = Path(SAMPLES_PATH)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Resuelve ``ruta_base`` según el entorno y la disposición del repo."""
        # 1. Variable de entorno tiene máxima prioridad
        env_samples_dir = os.getenv("GEOMIP_SAMPLES_DIR")
        if env_samples_dir:
            env_path = Path(env_samples_dir).expanduser().resolve()
            if env_path.exists():
                self.ruta_base = env_path
                return

        # 2. Búsqueda progresiva de rutas canónicas
        method2_root = Path(__file__).resolve().parents[2]
        geomip_root = Path(__file__).resolve().parents[4]
        candidatos = (
            method2_root / "src" / ".samples",
            method2_root / ".samples",
            geomip_root / "data" / "samples",
        )

        for candidato in candidatos:
            if candidato.exists():
                self.ruta_base = candidato
                return

        # 3. Ruta por defecto anclada al directorio raíz del módulo
        self.ruta_base = (method2_root / self.ruta_base).resolve()

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def pagina(self) -> str:
        """Página de red activa según la configuración de la aplicación.

        Returns:
            Sufijo de página (p. ej. ``"A"``, ``"B"``).
        """
        return aplicacion.pagina_sample_network

    @property
    def tpm_filename(self) -> Path:
        """Ruta absoluta al archivo CSV de la TPM correspondiente.

        El nombre sigue el patrón ``N{n}{pagina}.csv``, donde ``n``
        es ``len(estado_inicial)``.

        Returns:
            Objeto :class:`~pathlib.Path` al fichero CSV.
        """
        nombre = f"N{len(self.estado_inicial)}{self.pagina}.{CSV_EXTENSION}"
        return self.ruta_base / nombre

    @property
    def output_dir(self) -> Path:
        """Directorio de salida para resultados y perfilado.

        Returns:
            Ruta ``review/resolver/N{n}{pagina}/{estado_inicial}``.
        """
        return Path(
            f"{RESOLVER_PATH}"
            f"/N{len(self.estado_inicial)}{self.pagina}"
            f"/{self.estado_inicial}"
        )

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def generar_red(
        self,
        dimensiones: int,
        datos_discretos: bool = True,
    ) -> str | None:
        """Genera y guarda en disco una red TPM aleatoria.

        Crea un archivo ``NXY.csv`` en ``SAMPLES_PATH`` con una TPM
        en notación *little-endian*. Si ``datos_discretos`` es
        ``True`` la red es determinista (valores 0/1); de lo contrario
        es estocástica (valores reales en [0, 1]).

        Si ya existe un archivo ``N{dimensiones}A.csv``, se pregunta
        al usuario si desea generar uno nuevo con el siguiente sufijo
        alfabético.

        Args:
            dimensiones: Número de nodos del sistema (``N ≥ 1``).
            datos_discretos: Si es ``True`` genera una TPM
                determinista; si es ``False`` genera una TPM
                estocástica. Por defecto ``True``.

        Returns:
            Nombre del archivo generado (p. ej. ``"N4A.csv"``), o
            ``None`` si el usuario cancela la operación.

        Raises:
            ValueError: Si ``dimensiones < 1``.

        Example::

            gestor = Manager(estado_inicial="0000")
            nombre = gestor.generar_red(4)
            print(nombre)  # "N4A.csv"
        """
        np.random.seed(aplicacion.semilla_numpy)

        if dimensiones < 1:
            raise ValueError("Las dimensiones deben ser positivas")

        # Estimar tamaño en disco y tiempo de generación
        num_estados = 1 << dimensiones
        total_size_gb = (num_estados * dimensiones) / _BYTES_POR_GB
        estimated_time = total_size_gb * _FACTOR_TIEMPO_POR_GB

        print(f"Tamaño estimado: {total_size_gb:.6f} GB")
        print(f"Tiempo estimado: {estimated_time:.1f} segundos")

        if total_size_gb > _UMBRAL_GB:
            respuesta = input(
                "El sistema ocupará más de 1GB. ¿Continuar? (s/n): "
            )
            if respuesta.lower() != "s":
                return None

        # Resolver nombre de archivo sin colisiones
        base_path = Path(SAMPLES_PATH)
        base_path.mkdir(parents=True, exist_ok=True)

        sufijo = ABC_START
        while (
            base_path / f"N{dimensiones}{sufijo}.{CSV_EXTENSION}"
        ).exists():
            respuesta = input(
                f"Ya existe N{dimensiones}{sufijo}.{CSV_EXTENSION}."
                " ¿Generar nueva red? (s/n): "
            )
            if respuesta.lower() != "s":
                return f"N{dimensiones}{sufijo}.{CSV_EXTENSION}"
            sufijo = chr(ord(sufijo) + 1)

        filename = f"N{dimensiones}{sufijo}.{CSV_EXTENSION}"
        filepath = base_path / filename

        # Generar la matriz de estados
        print("Generando estados...")
        start_time = time.time()

        if datos_discretos:
            states = np.random.randint(
                2,
                size=(num_estados, dimensiones),
                dtype=np.int8,
            )
        else:
            states = np.random.random(size=(num_estados, dimensiones))

        print(
            f"Generación completada en "
            f"{time.time() - start_time:.2f} segundos"
        )

        # Persistir en disco
        print(f"Guardando en {filepath}...")
        start_time = time.time()
        np.savetxt(
            filepath,
            states,
            delimiter=COLON_DELIM,
            fmt=_FMT_INT if datos_discretos else _FMT_FLOAT,
        )

        file_size_gb = os.path.getsize(filepath) / _BYTES_POR_GB
        print(f"Archivo guardado: {file_size_gb:.6f} GB")
        print(
            f"Tiempo de guardado: {time.time() - start_time:.2f} segundos"
        )

        return filename
