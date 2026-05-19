import csv
from pathlib import Path

import numpy as np
import pandas as pd

from src.controllers.manager import Manager
from src.strategies.q_nodes import QNodes


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3}


def _letras_a_binario(texto: str, n_bits: int) -> str:
    """'ABCDFG' → '11011100000...' (posición A=0, B=1, ...)."""
    posiciones = "ABCDEFGHIJKLMNOPQRST"[:n_bits]
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def _leer_pruebas_excel(ruta_excel: Path, n: int) -> list[tuple[str, str]]:
    """Lee pares (alcance, mecanismo) del Excel canónico DatosPruebas2026_1.xlsx."""
    sheet_idx = _N_A_SHEET.get(n, 2)
    df = pd.read_excel(
        ruta_excel,
        sheet_name=sheet_idx,
        header=None,
        skiprows=5,        # fila 0-4 son cabeceras: estado inicial, sistema, particiones, labels, columnas
        usecols="B:C",
        names=["alcance", "mecanismo"],
    )
    df = df.dropna(subset=["alcance", "mecanismo"])
    return [(str(row.alcance).strip(), str(row.mecanismo).strip()) for _, row in df.iterrows()]


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
):
    n = len(estado_inicio)
    condiciones = "1" * n
    pruebas = _leer_pruebas_excel(ruta_excel, n)
    resultados = []

    gestor = Manager(estado_inicio)
    tpm = gestor.cargar_red()

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas, start=1):
        alcance = _letras_a_binario(letras_alcance, n)
        mecanismo = _letras_a_binario(letras_mecanismo, n)
        print(f"Prueba {i:>3} — Alcance: {letras_alcance:<10} Mecanismo: {letras_mecanismo}")

        try:
            analizador = QNodes(tpm)  # nueva instancia por iteración: evita cache contaminada
            sol = analizador.aplicar_estrategia(estado_inicio, condiciones, alcance, mecanismo)
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
        writer = csv.DictWriter(f, fieldnames=["Prueba", "Alcance", "Mecanismo", "Partición", "Pérdida (φ)", "Tiempo (s)"])
        writer.writeheader()
        writer.writerows(resultados)
    print(f"Resultados guardados en {ruta_salida}")


def iniciar():
    """Punto de entrada principal: procesa DatosPruebas2026_1.xlsx con N8A."""
    project_root = Path(__file__).resolve().parents[2]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    ruta_salida = RESULTS_DIR / "resultados_N8A.csv"

    estado_inicio = "10000000"  # N=8, estado inicial canónico

    ejecutar_desde_excel(ruta_excel, ruta_salida, estado_inicio)
