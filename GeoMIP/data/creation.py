"""
Generación de TPMs sintéticas para pruebas de GeoMIP.

Script auxiliar de datos. Permite crear Matrices de Probabilidad de
Transición (TPM) aleatorias de tamaño ``2^N × N`` y guardarlas como
archivos CSV en ``.assets/``. Útil para generar samples para redes de
gran tamaño (N > 15) que no están incluidas en el repositorio.

Typical usage example::

    python creation.py
    # Genera .assets/Sys8.csv para N=8 por defecto.

    from data.creation import generate_and_save
    system = generate_and_save(N=10)
"""

from __future__ import annotations

import os
import sys
import time

import numpy as np

BYTES_POR_GB: int = 1024 ** 3
UMBRAL_CONFIRMACION_GB: float = 1.0
FACTOR_TIEMPO_ESTIMADO: float = 2.0
DIRECTORIO_SALIDA: str = ".assets"


class SystemCreator:
    """Generador de estados aleatorios para sistemas de N nodos.

    Crea una matriz de estados binarios de forma ``(2^N, N)`` usando valores
    enteros de 8 bits, lo que corresponde a una TPM aleatoria no-normalizada.
    Solicita confirmación al usuario si el tamaño supera ``UMBRAL_CONFIRMACION_GB``.

    Attributes:
        N (int): Número de nodos del sistema.
        num_states (int): Número total de estados (``2^N``).
        states (np.ndarray): Matriz de estados con shape ``(2^N, N)``,
            dtype ``np.int8``.

    Example::

        creator = SystemCreator(N=8)
        creator.save_to_csv()
    """

    def __init__(self, N: int) -> None:
        """Inicializa el generador y crea la matriz de estados.

        Estima el tamaño en GB y solicita confirmación si supera
        ``UMBRAL_CONFIRMACION_GB``. Luego genera la matriz de forma
        ``(2^N, N)`` con valores aleatorios en {0, 1}.

        Args:
            N (int): Número de nodos del sistema (debe ser positivo).
        """
        self.N = N
        self.num_states = 2 ** N

        total_size_gb = (self.num_states * N) / BYTES_POR_GB
        print(f"\nTamaño estimado: {total_size_gb:.6f} GB")
        if total_size_gb > UMBRAL_CONFIRMACION_GB:
            confirm = input(
                "El sistema ocupará más de 1GB. ¿Desea continuar? (s/n): "
            )
            if confirm.lower() != "s":
                sys.exit("Operación cancelada por el usuario")

        estimated_time = total_size_gb * FACTOR_TIEMPO_ESTIMADO
        print(
            f"Tiempo estimado: {estimated_time:.1f} segundos "
            f"({estimated_time / 60:.1f} minutos)"
        )

        print("Generando estados...")
        start_time = time.time()
        self.states = np.random.randint(
            2, size=(self.num_states, N), dtype=np.int8
        )
        elapsed = time.time() - start_time
        print(f"Generación completada en {elapsed:.2f} segundos")

    def marginalize(self, dimension: int) -> np.ndarray:
        """Extrae la columna correspondiente a la dimensión indicada.

        Args:
            dimension (int): Índice de la dimensión (1 ≤ dimension < N).

        Returns:
            np.ndarray: Arreglo 1D con los valores de la dimensión indicada.

        Raises:
            ValueError: Si ``dimension`` está fuera del rango ``[1, N-1)``.
        """
        if dimension < 1 or dimension >= self.N:
            raise ValueError(
                f"La dimensión debe estar en [1, {self.N - 1})"
            )
        return self.states[:, dimension]

    def save_to_csv(self, filename: str | None = None) -> None:
        """Guarda la matriz de estados como CSV en ``DIRECTORIO_SALIDA``.

        Args:
            filename (str | None): Nombre del archivo de salida. Si es
                ``None``, se usa ``"Sys{N}.csv"``.
        """
        filename = f"Sys{self.N}.csv" if filename is None else filename

        os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)
        filepath = os.path.join(DIRECTORIO_SALIDA, filename)
        print(f"\nGuardando estados en {filepath}...")

        start_time = time.time()
        np.savetxt(filepath, self.states, delimiter=",", fmt="%d")

        elapsed = time.time() - start_time
        file_size_gb = os.path.getsize(filepath) / BYTES_POR_GB
        print(f"Archivo guardado: {file_size_gb:.6f} GB")
        print(f"Tiempo de guardado: {elapsed:.2f} segundos")


def generate_and_save(N: int) -> SystemCreator:
    """Genera un sistema de N nodos y guarda su TPM como CSV.

    Args:
        N (int): Número de nodos del sistema.

    Returns:
        SystemCreator: Instancia con la matriz de estados generada.
    """
    print(f"\nGenerando sistema con N={N}...")
    start_total = time.time()

    system = SystemCreator(N)
    system.save_to_csv()

    total_time = time.time() - start_total
    print(
        f"\nTiempo total del proceso: {total_time:.2f} segundos "
        f"({total_time / 60:.2f} minutos)"
    )
    return system


if __name__ == "__main__":
    try:
        system = generate_and_save(8)
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"\nError: {e}")
