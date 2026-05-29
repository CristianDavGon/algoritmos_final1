from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from tests.models import TestCase

_HOJA_POR_N: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}
_ABECEDARY = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def letras_a_binario(texto: str, n_bits: int) -> str:
    """Convert a letter string to a binary mask of length n_bits.

    Args:
        texto: Letter string, e.g. "ABCDE".
        n_bits: Total number of bits (= number of nodes).

    Returns:
        Binary string of length n_bits, e.g. "11111000...".
    """
    posiciones = _ABECEDARY[:n_bits]
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def cargar_casos(
    ruta_excel: Path,
    n: int,
    estado_inicial: str,
    n_tests: Optional[int] = None,
) -> list[TestCase]:
    """Load (alcance, mecanismo) test pairs from the canonical Excel file.

    Args:
        ruta_excel: Path to DatosPruebas2026_1.xlsx.
        n: Number of nodes; selects the correct sheet.
        estado_inicial: Initial state binary string, e.g. "1000000000".
        n_tests: If given, limit to first n_tests rows.

    Returns:
        List of TestCase objects ready for benchmark execution.
    """
    sheet_idx = _HOJA_POR_N.get(n, 2)
    df = pd.read_excel(
        ruta_excel,
        sheet_name=sheet_idx,
        header=None,
        skiprows=5,
        usecols="B:C",
        names=["alcance", "mecanismo"],
    )
    df = df.dropna(subset=["alcance", "mecanismo"])
    if n_tests is not None:
        df = df.head(n_tests)

    condicion = "1" * n
    casos: list[TestCase] = []
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        alcance_letras = str(row.alcance).strip()
        mecanismo_letras = str(row.mecanismo).strip()
        casos.append(
            TestCase(
                index=idx,
                alcance_letras=alcance_letras,
                mecanismo_letras=mecanismo_letras,
                alcance_bin=letras_a_binario(alcance_letras, n),
                mecanismo_bin=letras_a_binario(mecanismo_letras, n),
                estado_inicial=estado_inicial,
                condicion=condicion,
            )
        )
    return casos
