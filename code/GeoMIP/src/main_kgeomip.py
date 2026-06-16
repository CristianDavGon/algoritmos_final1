"""
Orquestación batch de KGeoMIP: lectura de Excel, ejecución y exportación CSV+MD.

Módulo de ejecución de KGeoMIP (extensión k-particiones geométrica). Lee el
archivo de pruebas ``DatosPruebas2026_1.xlsx``, convierte letras a vectores
binarios y ejecuta ``KGeoMIP.aplicar_estrategia`` con el k y variante dados.
Los resultados incluyen columnas adicionales (``k``, ``Criterio``) respecto al
formato base de bipartición.

Ejecutar a través de ``exec_kgeomip.py`` desde ``code/GeoMIP/``.

Typical usage example::

    from src.main_kgeomip import iniciar_kgeomip
    iniciar_kgeomip(estado="10000000", k=3, variante="E4")
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import pandas as pd

from src.controllers.manager import Manager
from src.controllers.strategies.kgeomip import KGeoMIP
from src.models.base.application import aplicacion
from src.reporter import guardar_markdown


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "kgeomip"

_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}
ABECEDARIO: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_CAMPOS_CSV: list[str] = [
    "Prueba", "Alcance", "Mecanismo",
    "k", "Criterio",
    "Partición", "Pérdida (φ)", "Tiempo (s)",
]


def _letras_a_binario(texto: str, n_bits: int) -> str:
    """Convierte letras de nodos a vector binario de longitud ``n_bits``.

    Args:
        texto (str): Letras del alcance o mecanismo (p. ej. ``"ABC"``).
        n_bits (int): Longitud del vector binario (= número de nodos n).

    Returns:
        str: Cadena binaria de longitud ``n_bits``.
    """
    posiciones = ABECEDARIO[:n_bits]
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def _leer_pruebas_excel(
    ruta_excel: Path, n: int
) -> list[tuple[str, str]]:
    """Lee todas las filas de alcance/mecanismo de la hoja correspondiente a n.

    Args:
        ruta_excel (Path): Ruta al archivo ``DatosPruebas2026_1.xlsx``.
        n (int): Tamaño de la red; determina la hoja del Excel.

    Returns:
        list[tuple[str, str]]: Lista de pares ``(alcance, mecanismo)``.
            Retorna lista vacía si hay error de lectura.
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
        print(f"Error al leer el Excel (Hoja {sheet_idx}, n={n}): {e}")
        return []

    df = df.dropna(subset=["alcance", "mecanismo"])
    return [
        (str(row.alcance).strip(), str(row.mecanismo).strip())
        for _, row in df.iterrows()
    ]


def _resolver_tpm(n: int, muestra: str) -> tuple[np.ndarray, Path]:
    """Localiza y carga el archivo NXY.csv de la TPM.

    Args:
        n (int): Número de nodos del sistema.
        muestra (str): Página de la muestra (p. ej. ``"A"``).

    Returns:
        tuple[np.ndarray, Path]: Par ``(tpm, directorio_samples)``.

    Raises:
        FileNotFoundError: Si el archivo CSV no se encuentra en ninguna
            ubicación candidata.
    """
    geomip_root = Path(__file__).resolve().parents[1]
    candidates = (
        geomip_root / "data" / "samples" / f"N{n}{muestra}.csv",
        geomip_root / "src" / ".samples" / f"N{n}{muestra}.csv",
    )
    for c in candidates:
        if c.exists():
            return np.genfromtxt(c, delimiter=","), c.parent
    raise FileNotFoundError(
        f"N{n}{muestra}.csv no encontrado. Buscado en: "
        f"{[str(c) for c in candidates]}"
    )


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
    k: int,
    variante: str,
) -> None:
    """Ejecuta KGeoMIP sobre todas las pruebas del Excel y exporta resultados.

    Args:
        ruta_excel (Path): Ruta al archivo ``DatosPruebas2026_1.xlsx``.
        ruta_salida (Path): Ruta de salida del CSV de resultados.
        estado_inicio (str): Estado inicial binario del sistema.
        k (int): Número de partes de la k-partición (k ∈ {2, 3, 4, 5}).
        variante (str): Variante del algoritmo (``"E4"`` = divisivo
            recomendado, ``"A"`` = aglomerativo).
    """
    n = len(estado_inicio)
    condicion = "1" * n
    muestra = aplicacion.pagina_sample_network
    pruebas = _leer_pruebas_excel(ruta_excel, n)

    if not pruebas:
        print(f"[WARN] Sin pruebas para n={n}.")
        return

    tpm, samples_dir = _resolver_tpm(n, muestra)
    os.environ["GEOMIP_SAMPLES_DIR"] = str(samples_dir)

    total_pruebas = len(pruebas)
    print(f"n={n}: {total_pruebas} pruebas — k={k} variante={variante}")

    resultados: list[dict] = []

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas, start=1):
        alcance = _letras_a_binario(letras_alcance, n)
        mecanismo = _letras_a_binario(letras_mecanismo, n)
        print(
            f"  Prueba {i:>3}/{total_pruebas} — "
            f"Alc: {letras_alcance:<8} Mec: {letras_mecanismo}"
        )

        try:
            kg = KGeoMIP(Manager(estado_inicial=estado_inicio))
            sol = kg.aplicar_estrategia(
                condicion, alcance, mecanismo, tpm, k=k, variante=variante
            )
            resultados.append({
                "Prueba": i,
                "Alcance": letras_alcance,
                "Mecanismo": letras_mecanismo,
                "k": k,
                "Criterio": variante,
                "Partición": sol.particion,
                "Pérdida (φ)": sol.perdida,
                "Tiempo (s)": sol.tiempo_ejecucion,
            })
        except Exception as e:
            print(f"    [ERROR]: {e}")
            resultados.append({
                "Prueba": i,
                "Alcance": letras_alcance,
                "Mecanismo": letras_mecanismo,
                "k": k,
                "Criterio": variante,
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

    ruta_md = guardar_markdown(
        resultados, ruta_salida.with_suffix(".md"), "KGeoMIP", estado_inicio
    )
    print(f"  MD:  {ruta_md}")


def iniciar_kgeomip(
    estado: str,
    k: int,
    variante: str,
) -> None:
    """Punto de entrada: procesa el Excel de pruebas para el estado, k y variante.

    Args:
        estado (str): Estado inicial binario (p. ej. ``"10000000"`` → n=8).
        k (int): Número de partes de la k-partición (k ∈ {2, 3, 4, 5}).
        variante (str): Variante del algoritmo (``"E4"`` recomendado).
    """
    project_root = Path(__file__).resolve().parents[2]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    muestra = aplicacion.pagina_sample_network
    n = len(estado)
    ruta_salida = RESULTS_DIR / f"resultado__N{n}_{muestra}_{k}.csv"
    ejecutar_desde_excel(ruta_excel, ruta_salida, estado, k, variante)
