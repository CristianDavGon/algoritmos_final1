"""Funciones matemáticas y de utilidad base para el módulo QNodes (IIT 4.0).

Incluye la generación de etiquetas alfabéticas (``ABECEDARY``),
el cálculo de la Earth Mover's Distance (EMD) para repertorios efecto
y causal, la selección dinámica de métricas y notaciones de indexado,
la conversión entre notaciones *big-endian* / *little-endian*, y
utilidades combinatorias para estados binarios.

Typical usage example::

    from src.funcs.iit import emd_efecto, ABECEDARY, reindexar

    phi = emd_efecto(distribucion_p, distribucion_q)
    etiqueta = ABECEDARY[0]    # "A"
    indices = reindexar(4)     # array en la notación configurada
"""

from __future__ import annotations

from itertools import product
from typing import Callable

import numpy as np
from numpy.typing import NDArray

from src.constants.base import (
    ABC_START,
    EMPTY_STR,
    INT_ZERO,
    STR_ONE,
    VOID_STR,
)
from src.models.base.application import aplicacion
from src.models.enums.distance import MetricDistance
from src.models.enums.notation import Notation
from src.models.enums.temporal_emd import TimeEMD

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
# Tamaño máximo del alfabeto soportado (cubre hasta "AN" estilo Excel)
_MAX_ETIQUETAS: int = 40
# Tamaño óptimo de grupo de bits para n ≤ 24 (empírico)
_BIT_GROUP_NORMAL: int = 4
# Tamaño óptimo de grupo de bits para n > 24 (empírico)
_BIT_GROUP_GRANDE: int = 6
# Umbral de nodos a partir del cual se usa el grupo grande
_UMBRAL_N_GRANDE: int = 24
# Límites para el cálculo del tamaño de bloque en lil_endian
_BLOCK_BITS_MIN: int = 12
_BLOCK_BITS_MAX: int = 16
_BLOCK_BITS_BASE: int = 28


# ---------------------------------------------------------------------------
# Etiquetas de nodos (estilo columnas Excel)
# ---------------------------------------------------------------------------

def get_labels(n: int) -> tuple[str, ...]:
    """Genera etiquetas alfanuméricas en estilo columnas de Excel.

    Produce ``n`` cadenas del tipo A, B, …, Z, AA, AB, … para
    identificar nodos en la visualización de resultados.

    Args:
        n: Número de etiquetas a generar (≥ 0).

    Returns:
        Tupla de ``n`` cadenas en orden ascendente.

    Example::

        get_labels(3)    # ("A", "B", "C")
        get_labels(27)   # ("A", ..., "Z", "AA")
    """

    def get_excel_column(n: int) -> str:
        """Convierte un entero positivo a su nombre de columna Excel."""
        if n <= 0:
            return ""
        return (
            get_excel_column((n - 1) // 26)
            + chr((n - 1) % 26 + ord(ABC_START))
        )

    return tuple(get_excel_column(i) for i in range(1, n + 1))


# Tabla global de etiquetas mayúsculas y minúsculas
ABECEDARY: tuple[str, ...] = get_labels(_MAX_ETIQUETAS)
LOWER_ABECEDARY: list[str] = [letter.lower() for letter in ABECEDARY]


def literales(
    remaining_vars: NDArray[np.int8],
    lowercase: bool = False,
) -> str:
    """Convierte un array de índices de nodos a su representación literal.

    Args:
        remaining_vars: Array de índices enteros de los nodos activos.
        lowercase: Si es ``True`` devuelve letras minúsculas (mecanismo);
            si es ``False`` devuelve mayúsculas (purview).

    Returns:
        Cadena concatenada de letras o ``"∅"`` si el array está vacío.

    Example::

        literales(np.array([0, 2]))            # "AC"
        literales(np.array([1]), lowercase=True)  # "b"
    """
    if not remaining_vars.size:
        return VOID_STR
    return EMPTY_STR.join(
        ABECEDARY[i].lower() if lowercase else ABECEDARY[i]
        for i in remaining_vars
    )


# ---------------------------------------------------------------------------
# Selección de métrica EMD temporal
# ---------------------------------------------------------------------------

def seleccionar_emd() -> Callable[
    [NDArray[np.float32], NDArray[np.float32]],
    float,
]:
    """Devuelve la función EMD configurada para la dirección temporal activa.

    Consulta ``aplicacion.tiempo_emd`` y devuelve la función
    correspondiente al tiempo (efecto o causal).

    Returns:
        Callable que acepta dos arrays de distribución y retorna la
        distancia EMD como ``float``.

    Raises:
        ValueError: Si el valor de ``tiempo_emd`` no está entre las
            métricas disponibles.

    Example::

        fn = seleccionar_emd()
        phi = fn(distribucion_p, distribucion_q)
    """
    emd_metricas: dict[
        str,
        Callable[[NDArray[np.float32], NDArray[np.float32]], float],
    ] = {
        TimeEMD.EMD_EFECTO.value: emd_efecto,
        # TimeEMD.EMD_CAUSA.value: emd_causal,  # pendiente de activar
    }

    emd_tiempo = (
        aplicacion.tiempo_emd.value
        if isinstance(aplicacion.tiempo_emd, TimeEMD)
        else str(aplicacion.tiempo_emd)
    )

    if emd_tiempo not in emd_metricas:
        metricas_disponibles = ", ".join(sorted(emd_metricas.keys()))
        raise ValueError(
            f"Tiempo EMD no soportado: '{emd_tiempo}'. "
            f"Opciones disponibles: {metricas_disponibles}"
        )

    return emd_metricas[emd_tiempo]


# ---------------------------------------------------------------------------
# EMD efecto (solución analítica)
# ---------------------------------------------------------------------------

def emd_efecto(
    u: NDArray[np.float32],
    v: NDArray[np.float32],
) -> float:
    """Calcula la EMD analítica entre dos repertorios efecto.

    Aprovecha la independencia condicional de los nodos: la EMD del
    repertorio efecto conjunto es igual a la suma de las EMDs de las
    distribuciones marginales de cada nodo. Para un solo nodo la EMD
    se reduce a la diferencia absoluta entre las probabilidades del
    estado ON/OFF.

    Sean ``X_1``, ``X_2`` variables aleatorias independientes con
    distribuciones ``u_1``, ``v_1`` y ``u_2``, ``v_2``
    respectivamente:

    .. math::

        \\text{EMD}(u, v) = \\sum_i |u_i - v_i|

    Args:
        u: Vector de probabilidades del repertorio de referencia.
            Forma ``(2^n,)`` con dtype ``float32``.
        v: Vector de probabilidades del repertorio a comparar.
            Misma forma y dtype que ``u``.

    Returns:
        Distancia EMD como escalar positivo.

    Example::

        u = np.array([0.3, 0.7], dtype=np.float32)
        v = np.array([0.5, 0.5], dtype=np.float32)
        emd_efecto(u, v)   # 0.4
    """
    return float(np.sum(np.abs(u - v)))


# ---------------------------------------------------------------------------
# EMD causal (con matriz de costes Hamming)
# ---------------------------------------------------------------------------

def emd_causal(
    u: NDArray[np.float64],
    v: NDArray[np.float64],
) -> float:
    """Calcula la EMD entre repertorios causales usando distancia de Hamming.

    A diferencia de :func:`emd_efecto`, los nodos del repertorio causal
    no son independientes; se construye la matriz de costes con la
    distancia de Hamming entre pares de estados y se resuelve el
    problema de transporte óptimo con ``pyemd``.

    Args:
        u: Distribución de probabilidad sobre ``2^n`` estados (presente
            → pasado). Dtype ``float64``.
        v: Distribución de probabilidad de referencia. Misma forma
            que ``u``.

    Returns:
        Distancia EMD causal como escalar positivo, o ``-1`` si
        ``pyemd`` no está disponible.

    Example::

        u = np.array([0.25, 0.25, 0.25, 0.25])
        v = np.array([0.5, 0.0, 0.0, 0.5])
        emd_causal(u, v)   # valor escalar ≥ 0
    """
    try:
        from pyemd import emd

        if not all(isinstance(arr, np.ndarray) for arr in [u, v]):
            raise TypeError("u y v deben ser instancias de numpy.ndarray.")

        n: int = u.size
        coste: NDArray[np.float64] = np.empty((n, n))
        distancia_metrica: Callable = seleccionar_distancia()

        for i in range(n):
            # Calcular mitad inferior de la matriz y reflejarla
            coste[i, :i] = [distancia_metrica(i, j) for j in range(i)]
            coste[:i, i] = coste[i, :i]
        np.fill_diagonal(coste, INT_ZERO)

        mat_costes: NDArray[np.float64] = np.array(coste, dtype=np.float64)
        return emd(u, v, mat_costes)

    except ImportError as e:
        print(f"pyemd no está instalado correctamente: {e}")
        return -1


# ---------------------------------------------------------------------------
# Selección de métrica de distancia espacial
# ---------------------------------------------------------------------------

def seleccionar_distancia() -> Callable[
    [NDArray[np.float32], NDArray[np.float32]],
    float,
]:
    """Devuelve la función de distancia espacial configurada en la aplicación.

    Consulta ``aplicacion.distancia_metrica`` y devuelve la función
    correspondiente (actualmente solo Hamming).

    Returns:
        Callable que acepta dos enteros y retorna la distancia.

    Raises:
        ValueError: Si la métrica configurada no está disponible.

    Example::

        fn = seleccionar_distancia()
        d = fn(0b101, 0b110)   # 2
    """
    distancias_metricas: dict[
        str,
        Callable[[NDArray[np.float32], NDArray[np.float32]], float],
    ] = {
        MetricDistance.HAMMING.value: hamming_distance,
        # MetricDistance.EUCLIDIANA.value: euclidean_distance,
        # MetricDistance.MANHATTAN.value: manhattan_distance,
    }
    distancia = (
        aplicacion.distancia_metrica.value
        if isinstance(aplicacion.distancia_metrica, MetricDistance)
        else str(aplicacion.distancia_metrica)
    )
    if distancia not in distancias_metricas:
        opciones = ", ".join(sorted(distancias_metricas.keys()))
        raise ValueError(
            f"Distancia métrica no soportada: '{distancia}'. "
            f"Opciones disponibles: {opciones}"
        )
    return distancias_metricas[distancia]


# ---------------------------------------------------------------------------
# Distancia de Hamming y conteo de bits
# ---------------------------------------------------------------------------

def hamming_distance(a: int, b: int) -> int:
    """Cuenta el número de bits que difieren entre dos enteros.

    Args:
        a: Primer entero.
        b: Segundo entero.

    Returns:
        Número de posiciones de bit distintas (distancia de Hamming).

    Example::

        hamming_distance(0b101, 0b110)   # 2
    """
    return count_bits(a ^ b)


def count_bits(n: int) -> int:
    """Cuenta el número de bits en ``1`` de la representación binaria de ``n``.

    Args:
        n: Entero no negativo cuya representación binaria se analiza.

    Returns:
        Número de bits activos (``1``) en la representación binaria.

    Example::

        count_bits(0b1011)   # 3
    """
    return bin(n).count(STR_ONE)


# ---------------------------------------------------------------------------
# Reindexado de notación
# ---------------------------------------------------------------------------

def reindexar(n: int) -> np.ndarray:
    """Genera la secuencia de índices en la notación configurada.

    Consulta ``aplicacion.notacion_indexado`` y retorna el array de
    índices en orden *big-endian* o *little-endian*.

    Args:
        n: Número de nodos del sistema.

    Returns:
        Array ``uint32`` con los índices reordenados según la notación
        activa.

    Raises:
        ValueError: Si la notación configurada no es reconocida.

    Example::

        # Con notación big-endian y n=3 → array([0, 1, 2])
        indices = reindexar(3)
    """
    notaciones = {
        Notation.BIG_ENDIAN.value: big_endian(n),
        Notation.LIL_ENDIAN.value: lil_endian(n),
        # ... otras notaciones
    }
    notacion = (
        aplicacion.notacion_indexado.value
        if isinstance(aplicacion.notacion_indexado, Notation)
        else str(aplicacion.notacion_indexado)
    )
    if notacion not in notaciones:
        opciones = ", ".join(sorted(notaciones.keys()))
        raise ValueError(
            f"Notación de indexado no soportada: '{notacion}'. "
            f"Opciones disponibles: {opciones}"
        )
    return notaciones[notacion]


def seleccionar_estado(subestado: np.ndarray) -> np.ndarray:
    """Reordena el subestado según la notación de indexado activa.

    Args:
        subestado: Array binario del estado del sistema en el hipercubo.

    Returns:
        Subestado en orden directo (*big-endian*) o invertido
        (*little-endian*) según la configuración.

    Raises:
        ValueError: Si la notación configurada no es reconocida.

    Example::

        arr = np.array([1, 0, 1])
        seleccionar_estado(arr)   # [1, 0, 1] o [1, 0, 1][::-1]
    """
    notaciones = {
        Notation.BIG_ENDIAN.value: subestado,
        Notation.LIL_ENDIAN.value: subestado[::-1],
        # ... otras notaciones
    }
    notacion = (
        aplicacion.notacion_indexado.value
        if isinstance(aplicacion.notacion_indexado, Notation)
        else str(aplicacion.notacion_indexado)
    )
    if notacion not in notaciones:
        opciones = ", ".join(sorted(notaciones.keys()))
        raise ValueError(
            f"Notación de estado no soportada: '{notacion}'. "
            f"Opciones disponibles: {opciones}"
        )
    return notaciones[notacion]


# ---------------------------------------------------------------------------
# Generación de índices por notación
# ---------------------------------------------------------------------------

def big_endian(n: int) -> np.ndarray:
    """Genera un array de índices en orden natural (*big-endian*).

    Args:
        n: Número de nodos del sistema.

    Returns:
        Array ``uint32`` con valores ``[0, 1, …, n-1]``.

    Example::

        big_endian(3)   # array([0, 1, 2], dtype=uint32)
    """
    return np.array(range(n), dtype=np.uint32)


def lil_endian(n: int) -> np.ndarray:
    """Genera la permutación de índices en notación *little-endian*.

    Implementación vectorizada por bloques. Los parámetros de bloque y
    grupo de bits se ajustan automáticamente según ``n``.

    Args:
        n: Número de nodos. Si ``n ≤ 0`` retorna ``[0]``.

    Returns:
        Array ``uint32`` de longitud ``2^n`` con la permutación
        *little-endian* de los índices de estado.

    Example::

        lil_endian(2)   # array([0, 2, 1, 3], dtype=uint32)
    """
    if n <= 0:
        # Caso especial: sistema degenerado
        return np.array([0], dtype=np.uint32)

    size = 1 << n
    result = np.zeros(size, dtype=np.uint32)

    # Tamaño de bloque adaptado al número de nodos
    block_bits = max(
        _BLOCK_BITS_MIN,
        min(_BLOCK_BITS_MAX, _BLOCK_BITS_BASE - int(np.log2(n))),
    )
    block_size = 1 << block_bits

    # Precomputar desplazamientos de bits para inversión de orden
    shifts = np.array(
        [n - i - 1 for i in range(n)],
        dtype=np.uint32,
    )

    # Buffer reutilizable por bloque para reducir asignaciones
    block_result = np.zeros(block_size, dtype=np.uint32)

    # Tamaño de grupo de bits (ajuste empírico según n)
    bit_group_size = (
        _BIT_GROUP_GRANDE if n > _UMBRAL_N_GRANDE else _BIT_GROUP_NORMAL
    )

    for start in range(0, size, block_size):
        end = min(start + block_size, size)
        current_size = end - start

        # Reiniciar sección activa del buffer
        block_result[:current_size] = 0
        block_indices = np.arange(start, end, dtype=np.uint32)

        # Procesar bits en grupos para mejor rendimiento de caché
        for base_bit in range(0, n, bit_group_size):
            bits_remaining = min(bit_group_size, n - base_bit)
            if bits_remaining <= 0:
                break

            # Extraer grupo de bits con máscara vectorizada
            group_mask = np.uint32((1 << bits_remaining) - 1)
            group_values = (block_indices >> base_bit) & group_mask

            for j in range(bits_remaining):
                shift = shifts[base_bit + j]
                bit_value = (group_values >> j) & np.uint32(1)
                block_result[:current_size] |= bit_value << shift

        result[start:end] = block_result[:current_size]

    return result


# ---------------------------------------------------------------------------
# Combinaciones con restricciones
# ---------------------------------------------------------------------------

def get_restricted_combinations(
    binary_str: str,
) -> tuple[list[str], list[str]]:
    """Genera combinaciones de B y C restringidas por la máscara A.

    B solo puede tener ``1`` en las posiciones donde A también tiene
    ``1``. C es una copia de B (mantenida para extensibilidad futura).

    Args:
        binary_str: Cadena binaria A que define las posiciones activas.

    Returns:
        Par ``(B, C)`` donde cada elemento es una lista de cadenas
        binarias del mismo ancho que ``binary_str``.

    Example::

        B, C = get_restricted_combinations("101")
        # B = ["000", "001", "100", "101"]
    """
    ones_count = binary_str.count("1")
    width = len(binary_str)
    one_positions = [
        i for i, bit in enumerate(binary_str) if bit == "1"
    ]

    def generate_valid_combinations() -> list[str]:
        """Genera combinaciones válidas sobre las posiciones activas."""
        base_combinations = list(
            product(["0", "1"], repeat=ones_count)
        )
        valid_combinations: list[str] = []

        for comb in base_combinations:
            resultado = ["0"] * width
            for pos, bit in zip(one_positions, comb):
                resultado[pos] = bit
            valid_combinations.append("".join(resultado))

        return valid_combinations

    # C es igual a B; se mantiene separado para futura diferenciación
    B = generate_valid_combinations()
    C = B.copy()
    return B, C


def generate_combinations(A: str) -> list[tuple[str, str, str]]:
    """Genera el producto cartesiano de A con las combinaciones B y C.

    Formatea cada cadena agrupando bits de a dos caracteres, luego
    devuelve el producto cartesiano sin el elemento trivial (0, 0, 0).

    Args:
        A: Cadena binaria de referencia.

    Returns:
        Lista de tripletas ``(A_fmt, B_fmt, C_fmt)`` con todas las
        combinaciones válidas excepto la trivial.

    Example::

        generate_combinations("1100")   # [(A_fmt, b1, c1), ...]
    """
    B, C = get_restricted_combinations(A)
    # Formatear cada cadena agrupando bits de a dos
    formatted_B = [
        EMPTY_STR.join(b[i: i + 2] for i in range(0, len(b), 2))
        for b in B
    ]
    formatted_C = [
        EMPTY_STR.join(c[i: i + 2] for i in range(0, len(c), 2))
        for c in C
    ]
    formatted_A = EMPTY_STR.join(
        A[i: i + 2] for i in range(0, len(A), 2)
    )

    # Excluir el primer elemento (trivial: todos ceros)
    return list(product([formatted_A], formatted_B, formatted_C))[1:]


# ---------------------------------------------------------------------------
# Conversión decimal-binario y enumeración de estados
# ---------------------------------------------------------------------------

def dec2bin(decimal: int, width: int) -> str:
    """Convierte un entero a su representación binaria de ancho fijo.

    Args:
        decimal: Entero no negativo a convertir.
        width: Número mínimo de dígitos (con relleno de ceros a la
            izquierda).

    Returns:
        Cadena binaria de longitud ``width``.

    Example::

        dec2bin(5, 4)   # "0101"
    """
    return format(decimal, f"0{width}b")


def estados_binarios(n: int) -> list[str]:
    """Enumera todos los estados binarios no nulos de un sistema de ``n`` nodos.

    Args:
        n: Número de nodos del sistema (``N ≥ 1``).

    Returns:
        Lista de ``2^n - 1`` cadenas binarias (sin el estado todo-cero).

    Example::

        estados_binarios(2)   # ["01", "10", "11"]
    """
    return [dec2bin(i, n) for i in range(1 << n)][1:]
