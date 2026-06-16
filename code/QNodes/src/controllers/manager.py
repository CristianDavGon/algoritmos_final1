"""Controlador principal de gestión de redes TPM para el módulo QNodes.

Proporciona la clase :class:`Manager` que localiza los archivos CSV de
matrices de probabilidad de transición (TPM) almacenados en el directorio
de muestras, los carga en memoria como arrays NumPy y gestiona el
directorio de salida para resultados y perfilado.

Typical usage example::

    from src.controllers.manager import Manager

    gestor = Manager(estado_inicial="1010")
    tpm = gestor.cargar_red()        # NDArray shape (2^N, N)
    print(gestor.tpm_filename)       # .../N4A.csv
    print(gestor.output_dir)         # review/resolver/N4A/1010
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from src.constants.base import (
    ABC_START,
    COLON_DELIM,
    CSV_EXTENSION,
    PATH_RESOLVER,
    PATH_SAMPLES,
)
from src.models.base.application import aplicacion

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
# Umbral en gigabytes a partir del cual se solicita confirmación al usuario
_UMBRAL_GB: float = 1.0
# Factor de estimación: segundos por gigabyte generado
_FACTOR_TIEMPO_POR_GB: float = 2.0
# Formato de precisión decimal para TPMs estocásticas
_FMT_FLOAT: str = "%.6f"
# Formato entero para TPMs deterministas
_FMT_INT: str = "%d"
# Divisor para convertir bytes a gigabytes
_BYTES_POR_GB: int = 1024 ** 3


@dataclass
class Manager:
    """Gestor de archivos TPM y directorios de salida para QNodes.

    Localiza el fichero CSV de la TPM correspondiente al tamaño del
    sistema (determinado por ``estado_inicial``) dentro de
    ``ruta_base``, permite cargarlo en memoria y calcula la ruta del
    directorio donde se almacenarán los resultados.

    Si ``ruta_base`` no es una ruta absoluta se ancla automáticamente
    al directorio raíz del módulo QNodes en :meth:`__post_init__`.

    Attributes:
        estado_inicial: Cadena binaria que representa el estado del
            sistema en ``t``. Su longitud determina el número de nodos
            ``N`` y el archivo ``NXY.csv`` a cargar.
        ruta_base: Directorio donde residen los archivos de muestra
            ``NXY.csv``. Se resuelve en :meth:`__post_init__`.

    Example::

        gestor = Manager(estado_inicial="101")
        tpm = gestor.cargar_red()
        print(tpm.shape)   # (8, 3) para N=3
    """

    estado_inicial: str
    ruta_base: Path = field(
        default_factory=lambda: Path(PATH_SAMPLES)
    )

    def __post_init__(self) -> None:
        """Ancla ``ruta_base`` al directorio raíz de QNodes si es relativa."""
        if not self.ruta_base.is_absolute():
            # Subir dos niveles desde controllers/ → QNodes/
            qnodes_root = Path(__file__).resolve().parents[2]
            self.ruta_base = (qnodes_root / self.ruta_base).resolve()

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def pagina(self) -> str:
        """Página de red activa según la configuración de la aplicación.

        Returns:
            Sufijo de página (p. ej. ``"A"``, ``"B"``).
        """
        return aplicacion.pagina_red_muestra

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
            f"{PATH_RESOLVER}"
            f"/N{len(self.estado_inicial)}{self.pagina}"
            f"/{self.estado_inicial}"
        )

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def preparar_directorio_salida(self) -> None:
        """Crea el directorio de salida y todos sus padres si no existen.

        Example::

            gestor = Manager(estado_inicial="101")
            gestor.preparar_directorio_salida()
            # Crea review/resolver/N3A/101/
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def cargar_red(self) -> np.ndarray:
        """Lee el archivo CSV de la TPM y lo devuelve como array NumPy.

        Returns:
            Array 2-D de forma ``(2^N, N)`` con los valores de la TPM.
            Las filas corresponden a estados del sistema en ``t`` y
            las columnas a la probabilidad de activación de cada nodo
            en ``t+1``.

        Example::

            gestor = Manager(estado_inicial="1010")
            tpm = gestor.cargar_red()
            print(tpm.shape)   # (16, 4)
        """
        return np.genfromtxt(self.tpm_filename, delimiter=COLON_DELIM)

    def generar_red(
        self,
        dimensiones: int,
        datos_deterministas: bool = True,
    ) -> str | None:
        """Genera y guarda en disco una red TPM aleatoria.

        Crea un archivo ``NXY.csv`` en ``PATH_SAMPLES`` con una TPM
        en notación *little-endian*. Si ``datos_deterministas`` es
        ``True`` la red es determinista (valores 0/1); de lo contrario
        es estocástica (valores reales en [0, 1]).

        Si ya existe un archivo ``N{dimensiones}A.csv``, se pregunta
        al usuario si desea generar uno nuevo con el siguiente sufijo
        alfabético.

        Args:
            dimensiones: Número de nodos del sistema (``N ≥ 1``).
            datos_deterministas: Si es ``True`` genera una TPM
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
            print(nombre)   # "N4A.csv"
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
        base_path = Path(PATH_SAMPLES)
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

        if datos_deterministas:
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
            fmt=_FMT_INT if datos_deterministas else _FMT_FLOAT,
        )

        file_size_gb = os.path.getsize(filepath) / _BYTES_POR_GB
        print(f"Archivo guardado: {file_size_gb:.6f} GB")
        print(
            f"Tiempo de guardado: {time.time() - start_time:.2f} segundos"
        )

        return filename
