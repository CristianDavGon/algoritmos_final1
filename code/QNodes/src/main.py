"""
Orquestación batch de QNodes: lectura de Excel, ejecución y exportación CSV+MD.

Módulo principal de ejecución de QNodes. Lee el archivo de pruebas
``DatosPruebas2026_1.xlsx``, convierte letras (A, B, …) a vectores binarios,
instancia ``QNodes`` (oracle lazy + MAO) y ejecuta el análisis de bipartición
sobre cada par (alcance, mecanismo). Los resultados se exportan a CSV y
Markdown.

Typical usage example::

    from src.main import iniciar
    iniciar(estado="10000000")
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from src.controllers.manager import Manager
from src.models.base.application import aplicacion
from src.reporter import guardar_markdown
from src.strategies.qnodes import QNodes


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "qnodes"

_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}
ABECEDARIO: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _letras_a_binario(texto: str, n_bits: int, posiciones: str) -> str:
    """Convierte letras de nodos a vector binario de longitud ``n_bits``.

    Mapea cada letra al índice correspondiente en ``posiciones`` (A=0, B=1,
    …) y activa el bit en esa posición. Letras no reconocidas se ignoran.

    Args:
        texto (str): Letras del alcance o mecanismo (p. ej. ``"ABC"``).
        n_bits (int): Longitud del vector binario (= número de nodos n).
        posiciones (str): Cadena de caracteres válidos de longitud n.

    Returns:
        str: Cadena binaria de longitud ``n_bits`` (p. ej. ``"11100...0"``).
    """
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def _leer_pruebas_excel(
    ruta_excel: Path, n: int
) -> list[tuple[str, str]]:
    """Lee pares (alcance, mecanismo) del Excel canónico de pruebas.

    Selecciona la hoja según ``n`` (mapeada por ``_N_A_SHEET``), salta las
    primeras 5 filas de encabezado y extrae las columnas B y C.

    Args:
        ruta_excel (Path): Ruta al archivo ``DatosPruebas2026_1.xlsx``.
        n (int): Tamaño de la red; determina la hoja del Excel.

    Returns:
        list[tuple[str, str]]: Lista de pares ``(alcance, mecanismo)``
            en formato de letras. Retorna lista vacía si hay error de
            lectura.
    """
    sheet_idx = _N_A_SHEET.get(n, 2)
    try:
        df = pd.read_excel(
            ruta_excel,
            sheet_name=sheet_idx,
            header=None,
            skiprows=5,
            usecols="B:C",
            names=["alcance", "mecanismo"],
        )
    except Exception as e:
        print(f"Error crítico al leer el Excel (Hoja {sheet_idx}): {e}")
        return []

    df = df.dropna(subset=["alcance", "mecanismo"])
    if df.empty:
        print(
            f"Advertencia: sin datos válidos en columnas B:C "
            f"de la hoja {sheet_idx}"
        )

    return [
        (str(row.alcance).strip(), str(row.mecanismo).strip())
        for _, row in df.iterrows()
    ]


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
) -> None:
    """Ejecuta QNodes sobre todas las pruebas del Excel y exporta resultados.

    Crea una sola instancia de ``QNodes`` y reutiliza la TPM para todas las
    pruebas. Los resultados se guardan en CSV (UTF-8) y en Markdown.

    Args:
        ruta_excel (Path): Ruta al archivo ``DatosPruebas2026_1.xlsx``.
        ruta_salida (Path): Ruta de salida del CSV de resultados.
        estado_inicio (str): Estado inicial binario del sistema.
    """
    n = len(estado_inicio)
    pruebas = _leer_pruebas_excel(ruta_excel, n)
    resultados = []

    # Extraer constantes del bucle (invariantes de iteración)
    posiciones_n = ABECEDARIO[:n]
    condiciones = "1" * n

    gestor = Manager(estado_inicio)
    tpm = gestor.cargar_red()

    analizador = QNodes(tpm)

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas, start=1):
        alcance = _letras_a_binario(letras_alcance, n, posiciones_n)
        mecanismo = _letras_a_binario(letras_mecanismo, n, posiciones_n)
        print(
            f"Prueba {i:>3} — Alcance: {letras_alcance:<10} "
            f"Mecanismo: {letras_mecanismo}"
        )

        try:
            sol = analizador.aplicar_estrategia(
                estado_inicio, condiciones, alcance, mecanismo
            )
            resultados.append({
                "Prueba": i,
                "Alcance": letras_alcance,
                "Mecanismo": letras_mecanismo,
                "Partición": sol.particion,
                "Pérdida (φ)": sol.perdida,
                "Tiempo (s)": sol.tiempo_ejecucion,
            })
        except Exception as e:
            resultados.append({
                "Prueba": i,
                "Alcance": letras_alcance,
                "Mecanismo": letras_mecanismo,
                "Partición": None,
                "Pérdida (φ)": None,
                "Tiempo (s)": None,
            })
            print(f"  Error en prueba {i}: {e}")

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Prueba", "Alcance", "Mecanismo",
                "Partición", "Pérdida (φ)", "Tiempo (s)",
            ],
        )
        writer.writeheader()
        writer.writerows(resultados)
    print(f"  CSV: {ruta_salida}")
    ruta_md = guardar_markdown(
        resultados, ruta_salida.with_suffix(".md"), "QNodes", estado_inicio
    )
    print(f"  MD:  {ruta_md}")


def iniciar(estado: str) -> None:
    """Punto de entrada principal: procesa el Excel y ejecuta QNodes.

    Args:
        estado (str): Estado inicial binario (p. ej. ``"10000000"`` → n=8).
            Su longitud determina la red a analizar y la hoja del Excel.
    """
    project_root = Path(__file__).resolve().parents[2]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    muestra = aplicacion.pagina_red_muestra

    n = len(estado)
    ruta_salida = RESULTS_DIR / f"resultado__N{n}_{muestra}.csv"

    ejecutar_desde_excel(ruta_excel, ruta_salida, estado)
