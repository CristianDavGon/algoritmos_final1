"""Generadores de particiones y subsistemas para el módulo GeoMIP.

Proporciona funciones para enumerar combinaciones de condicionamiento,
subsistemas candidatos y biparticiones binarias eficientes en memoria.
Estas rutinas constituyen el motor combinatorio que alimenta las
estrategias de búsqueda de la MIP (partición de integración mínima).

Typical usage example::

    from src.funcs.system import (
        generar_candidatos,
        generar_particiones,
        biparticiones,
    )

    for combo in generar_candidatos(4):
        print(combo)   # (), (0,), (1,), (0,1), ...

    for m_part, n_part in generar_particiones(3, 2):
        print(m_part, n_part)
"""

from __future__ import annotations

from itertools import chain, combinations, islice, product
from typing import Generator, Union

import numpy as np


def generar_candidatos(
    n_vars: int,
) -> Generator[tuple[int, ...], None, None]:
    """Genera todos los subconjuntos propios de ``range(n_vars)``.

    Produce combinaciones en orden creciente de tamaño, desde el
    conjunto vacío ``()`` hasta los subconjuntos de tamaño
    ``n_vars - 1``. Se usa para enumerar condicionamientos candidatos
    en el cómputo de φ.

    Args:
        n_vars: Número total de variables del sistema (``N ≥ 1``).

    Returns:
        Generador perezoso de tuplas de índices enteros.

    Example::

        list(generar_candidatos(3))
        # [(), (0,), (1,), (2,), (0, 1), (0, 2), (1, 2)]
    """
    return (
        combo
        for r in range(n_vars)
        for combo in combinations(range(n_vars), r)
    )


def generar_subsistemas(
    vars: tuple[int, ...],
) -> Generator[tuple[tuple[int, ...], tuple[int, ...]], None, None]:
    """Genera el producto cartesiano de subsistemas temporales.

    Cada subsistema es un par ``(pasado, futuro)`` donde tanto
    ``pasado`` como ``futuro`` son subconjuntos de ``vars``.  El
    tamaño de los subconjuntos va desde vacío hasta ``len(vars)``
    (inclusive), a diferencia de :func:`generar_candidatos` que
    excluye el conjunto total para facilitar la marginalización.

    Args:
        vars: Tupla de índices de las variables del sistema candidato.

    Returns:
        Generador de pares de tuplas ``(subconj_pasado,
        subconj_futuro)``.

    Example::

        list(generar_subsistemas((0, 1)))
        # [((), ()), ((), (0,)), ..., ((0, 1), (0, 1))]
    """
    tiempos = [
        combo
        for r in range(len(vars) + 1)
        for combo in combinations(vars, r)
    ]
    return product(tiempos, tiempos)


def generar_particiones_conjuntos() -> None:
    """Marcador de posición para la generación de particiones de conjuntos.

    Pendiente de implementación.
    """
    pass


def generar_particiones(
    m: int,
    n: int,
    *,
    as_matrix: bool = False,
    as_generator: bool = True,
) -> Union[
    Generator[tuple[np.ndarray, np.ndarray], None, None],
    np.ndarray,
    list[tuple[np.ndarray, np.ndarray]],
]:
    """Genera biparticiones binarias del espacio de estados (M × N).

    Enumera todos los pares de vectores de bits ``(m_row, n_row)``
    correspondientes a las ``2^(M-1) × 2^N - 1`` biparticiones
    no triviales (se excluye el par todo-ceros).

    Se usan operaciones vectorizadas de NumPy para construir las
    matrices de bits en un solo paso y evitar bucles Python en la
    generación.

    Args:
        m: Número de bits de la primera parte (``M ≥ 1``).
        n: Número de bits de la segunda parte (``N ≥ 0``).
        as_matrix: Si es ``True`` y ``as_generator`` es ``False``,
            retorna una matriz 2-D de forma ``(total, M + N)``.
        as_generator: Si es ``True`` (por defecto) retorna un
            generador perezoso de pares de arrays.

    Returns:
        Generador de tuplas ``(m_row, n_row)``, matriz 2-D, o lista
        de tuplas según los flags ``as_generator`` y ``as_matrix``.

    Raises:
        ValueError: Si ``m < 1`` (primera parte vacía no soportada).

    Example::

        for m_row, n_row in generar_particiones(2, 2):
            print(m_row, n_row)
    """
    # Validar que la primera parte tenga al menos un elemento
    if m < 1:
        raise ValueError(
            f"Alcance trivial: Future no debe tener {m} elementos"
        )

    # Número de combinaciones para cada parte usando bit-shift
    m_combinations = 1 << (m - 1)  # 2^(M-1)
    n_combinations = 1 << n         # 2^N

    # Construir matrices de bits con broadcasting vectorizado
    m_indices = np.arange(
        m_combinations, dtype=np.uint32
    )[:, np.newaxis]
    n_indices = np.arange(
        n_combinations, dtype=np.uint32
    )[:, np.newaxis]

    m_shifts = np.arange(m - 1, -1, -1, dtype=np.uint8)
    n_shifts = np.arange(n - 1, -1, -1, dtype=np.uint8)

    m_bits = (m_indices >> m_shifts) & 1
    n_bits = (n_indices >> n_shifts) & 1

    if as_generator:

        def partition_generator():
            """Generador perezoso de pares de filas de bits."""
            # Fila m=0: comenzar desde j=1 para evitar la partición trivial
            m_row = m_bits[0]
            for j in range(1, n_combinations):
                yield m_row, n_bits[j]

            # Resto de filas: iterar sobre todos los valores de n
            for i in range(1, m_combinations):
                m_row = m_bits[i]
                for j in range(n_combinations):
                    yield m_row, n_bits[j]

        return partition_generator()

    if as_matrix:
        # Construir matriz resultado con broadcasting
        total_rows = m_combinations * n_combinations
        result = np.empty((total_rows, m + n), dtype=np.uint8)

        result_view_m = result[:, :m].reshape(
            m_combinations, n_combinations, m
        )
        result_view_n = result[:, m:].reshape(
            m_combinations, n_combinations, n
        )

        result_view_m[:] = m_bits[:, np.newaxis, :]
        result_view_n[:] = n_bits

        return result if not as_generator else (row for row in result)

    # Modo lista: retornar todos los pares como tuplas
    return [
        (m_bits[i], n_bits[j])
        for i in range(m_combinations)
        for j in range(n_combinations)
    ]


def biparticiones(
    alcances: np.ndarray,
    mecanismos: np.ndarray,
    total: int | None = None,
) -> islice:
    """Enumera las biparticiones internas de un subsistema (alcance × mecanismo).

    Genera el producto cartesiano de todos los subconjuntos de
    ``alcances`` y ``mecanismos``, excluyendo el primer elemento
    (vacío × vacío) y el último (conjunto completo × conjunto completo).

    Args:
        alcances: Array de índices del purview del subsistema.
        mecanismos: Array de índices del mecanismo del subsistema.
        total: Número total de pares a generar. Si es ``None`` se
            calcula como ``2^|alcances| × 2^|mecanismos|``.

    Returns:
        Iterador acotado de pares ``(subconj_alcance,
        subconj_mecanismo)``.

    Example::

        A = np.array([0, 1])
        M = np.array([0, 1])
        list(biparticiones(A, M))
        # Todos los pares no triviales
    """
    if total is None:
        total = (1 << alcances.size) * (1 << mecanismos.size)
    return islice(
        product(subconjuntos(alcances), subconjuntos(mecanismos)),
        1,
        total - 1,
    )


def subconjuntos(
    arr: np.ndarray,
) -> chain[tuple[int, ...]]:
    """Genera todos los subconjuntos de un array ordenados por tamaño.

    Equivale a la función potencia del conjunto ``arr``, desde el
    vacío ``()`` hasta el conjunto completo.

    Args:
        arr: Array de elementos a combinar.

    Returns:
        Iterador de tuplas desde tamaño 0 hasta ``len(arr)``.

    Example::

        list(subconjuntos(np.array([0, 1])))
        # [(), (0,), (1,), (0, 1)]
    """
    return chain.from_iterable(
        combinations(arr, r) for r in range(len(arr) + 1)
    )
