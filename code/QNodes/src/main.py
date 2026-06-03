import csv
from pathlib import Path

import numpy as np
import pandas as pd

from src.controllers.manager import Manager
from src.strategies.qnodes import QNodes


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "qnodes"


_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}


def _letras_a_binario(texto: str, n_bits: int, posiciones: str) -> str:
    """'ABCDFG' → '11011100000...' (posición A=0, B=1, ...)."""
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def _leer_pruebas_excel(ruta_excel: Path, n: int) -> list[tuple[str, str]]:
    """
    Abre el Excel, busca la hoja correcta según N y extrae las columnas de Alcance y Mecanismo.
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
        print(f"Advertencia: No se encontraron datos válidos en las columnas B:C de la hoja {sheet_idx}")
        
    return [(str(row.alcance).strip(), str(row.mecanismo).strip()) for _, row in df.iterrows()]


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
):
    n = len(estado_inicio)
    pruebas = _leer_pruebas_excel(ruta_excel, n)
    resultados = []
    
    # Optimizaciones: Sacar constantes del bucle (Invariantes)
    posiciones_n = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:n]
    condiciones = "1" * n

    gestor = Manager(estado_inicio)
    tpm = gestor.cargar_red()

    analizador = QNodes(tpm) 

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas, start=1):
        alcance = _letras_a_binario(letras_alcance, n, posiciones_n)
        mecanismo = _letras_a_binario(letras_mecanismo, n, posiciones_n)
        print(f"Prueba {i:>3} — Alcance: {letras_alcance:<10} Mecanismo: {letras_mecanismo}")

        try:
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
    """Punto de entrada principal: procesa DatosPruebas2026_1.xlsx con N15B."""
    project_root = Path(__file__).resolve().parents[2]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    estado_inicio = "1" + "0" * 21
    n = len(estado_inicio)
    ruta_salida = RESULTS_DIR / f"resultados_N{n}B.csv"

    ejecutar_desde_excel(ruta_excel, ruta_salida, estado_inicio)
