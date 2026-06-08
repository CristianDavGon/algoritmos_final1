import csv
from pathlib import Path

import numpy as np
import pandas as pd

from src.controllers.manager import Manager
from src.models.base.application import aplicacion
from src.reporter import guardar_markdown
from src.strategies.kqnodes import KQNodes


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "kqnodes"

_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}

_CAMPOS_CSV = [
    "Prueba", "Alcance", "Mecanismo",
    "k", "Criterio",
    "Partición", "Pérdida (φ)", "Tiempo (s)",
]


def _letras_a_binario(texto: str, n_bits: int, posiciones: str) -> str:
    """'ABCDFG' → '11011100000...' (posición A=0, B=1, ...)."""
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def _leer_pruebas_excel(ruta_excel: Path, n: int) -> list[tuple[str, str]]:
    """Lee todas las filas de alcance/mecanismo de la hoja correspondiente a n."""
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
        print(f"Error al leer el Excel (Hoja {sheet_idx}, n={n}): {e}")
        return []

    df = df.dropna(subset=["alcance", "mecanismo"])
    return [(str(row.alcance).strip(), str(row.mecanismo).strip()) for _, row in df.iterrows()]


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
    k_valores: list[int],
    criterios: list[str],
) -> None:
    """Ejecuta KQNodes sobre todas las pruebas del Excel con todos los k y criterios dados.

    Cada fila del Excel genera len(k_valores) × len(criterios) filas en el CSV de salida.
    """
    n = len(estado_inicio)
    posiciones_n = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:n]
    condicion = "1" * n
    pruebas = _leer_pruebas_excel(ruta_excel, n)

    if not pruebas:
        print(f"[WARN] Sin pruebas para n={n}.")
        return

    gestor = Manager(estado_inicio)
    tpm = gestor.cargar_red()
    kqn = KQNodes(tpm)

    total_pruebas = len(pruebas)
    total_filas = total_pruebas * len(k_valores) * len(criterios)
    print(f"n={n}: {total_pruebas} pruebas × {len(k_valores)} k × {len(criterios)} criterios = {total_filas} ejecuciones")

    resultados: list[dict] = []

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas, start=1):
        alcance = _letras_a_binario(letras_alcance, n, posiciones_n)
        mecanismo = _letras_a_binario(letras_mecanismo, n, posiciones_n)
        print(f"  Prueba {i:>3}/{total_pruebas} — Alc: {letras_alcance:<8} Mec: {letras_mecanismo}")

        for k in k_valores:
            for criterio in criterios:
                try:
                    sol = kqn.aplicar_estrategia(
                        estado_inicio, condicion, alcance, mecanismo,
                        k=k, criterio=criterio,
                    )
                    resultados.append({
                        "Prueba": i,
                        "Alcance": letras_alcance,
                        "Mecanismo": letras_mecanismo,
                        "k": k,
                        "Criterio": criterio,
                        "Partición": sol.particion,
                        "Pérdida (φ)": sol.perdida,
                        "Tiempo (s)": sol.tiempo_ejecucion,
                    })
                except Exception as e:
                    print(f"    [ERROR] k={k} criterio={criterio}: {e}")
                    resultados.append({
                        "Prueba": i,
                        "Alcance": letras_alcance,
                        "Mecanismo": letras_mecanismo,
                        "k": k,
                        "Criterio": criterio,
                        "Partición": None,
                        "Pérdida (φ)": None,
                        "Tiempo (s)": None,
                    })

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CAMPOS_CSV)
        writer.writeheader()
        writer.writerows(resultados)
    print(f"  CSV: {ruta_salida} ({len(resultados)} filas)")
    ruta_md = guardar_markdown(resultados, ruta_salida.with_suffix(".md"), "KQNodes", estado_inicio)
    print(f"  MD:  {ruta_md}")


def iniciar_kqnodes(
    estado: str,
    k: int,
    criterio: str,
) -> None:
    """Punto de entrada: procesa DatosPruebas2026_1.xlsx para el estado, k y criterio dados.

    Args:
        estado: String binario que define el estado inicial s(t) (ej. "10000000" -> n=8).
        k: Número de partes de la k-partición.
        criterio: Criterio de refinamiento ("C4" = corte marginal mínimo, "C1" = tamaño máximo).
    """
    project_root = Path(__file__).resolve().parents[2]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    muestra = aplicacion.pagina_red_muestra
    n = len(estado)
    ruta_salida = RESULTS_DIR / f"resultado__N{n}_{muestra}_{k}.csv"
    ejecutar_desde_excel(ruta_excel, ruta_salida, estado, [k], [criterio])
