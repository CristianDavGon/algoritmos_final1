from src.controllers.manager import Manager
from src.controllers.strategies.geometric import GeometricSIA
from src.controllers.strategies.q_nodes import QNodes
# Optional import: this project often runs only geometric strategy.
try:
    from src.controllers.strategies.phi import Phi
except Exception:
    Phi = None
import multiprocessing
import numpy as np
import pandas as pd
import os
from pathlib import Path


METHOD2_ROOT = Path(__file__).resolve().parents[1]
GEOMIP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = GEOMIP_ROOT / "results"

_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}


def _letras_a_binario(texto: str, n_bits: int) -> str:
    """'ABCDFG' → '11011100000...'"""
    # 26 nodos
    posiciones = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:n_bits]
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
        skiprows=5,
        usecols="B:C",
        names=["alcance", "mecanismo"],
    )
    df = df.dropna(subset=["alcance", "mecanismo"])
    return [(str(r.alcance).strip(), str(r.mecanismo).strip()) for _, r in df.iterrows()]


def resolver_tpm_path(estado_inicio: str) -> Path:
    sample_name = f"N{len(estado_inicio)}B.csv"
    candidates = (
        METHOD2_ROOT / "src" / ".samples" / sample_name,
        METHOD2_ROOT / ".samples" / sample_name,
        GEOMIP_ROOT / "data" / "samples" / sample_name,
    )
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"No se encontró '{sample_name}'. Busqué en: {', '.join(str(c) for c in candidates)}"
    )


def ejecutar_con_tiempo(config_sistema, condiciones, alcance, mecanismo, resultado_queue, tpm):
    try:
        analizador_fi = GeometricSIA(config_sistema)
        sia_dos = analizador_fi.aplicar_estrategia(condiciones, alcance, mecanismo, tpm)
        resultado_queue.put({
            "particion": sia_dos.particion,
            "perdida": sia_dos.perdida,
            "tiempo": sia_dos.tiempo_ejecucion,
        })
    except Exception as e:
        resultado_queue.put({"particion": None, "perdida": None, "tiempo": None})

def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
):
    n = len(estado_inicio)
    condiciones = "1" * n
    pruebas = _leer_pruebas_excel(ruta_excel, n)
    resultados = []

    tpm_path = resolver_tpm_path(estado_inicio)
    tpm = np.genfromtxt(tpm_path, delimiter=",")

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas, start=1):
        alcance = _letras_a_binario(letras_alcance, n)
        mecanismo = _letras_a_binario(letras_mecanismo, n)
        print(f"Prueba {i:>3} — Alcance: {letras_alcance:<10} Mecanismo: {letras_mecanismo}")

        config_sistema = Manager(estado_inicial=estado_inicio)

        resultado_queue = multiprocessing.Queue()
        proceso = multiprocessing.Process(
            target=ejecutar_con_tiempo,
            args=(config_sistema, condiciones, alcance, mecanismo, resultado_queue, tpm),
        )
        proceso.start()
        proceso.join(timeout=3600)

        if proceso.is_alive():
            print(f"  Tiempo límite alcanzado en prueba {i}.")
            proceso.terminate()
            proceso.join()
            resultado = {"particion": None, "perdida": None, "tiempo": None}
        else:
            resultado = (
                resultado_queue.get()
                if not resultado_queue.empty()
                else {"particion": None, "perdida": None, "tiempo": None}
            )

        resultados.append({
            "Prueba": i,
            "Alcance": letras_alcance,
            "Mecanismo": letras_mecanismo,
            "Partición": resultado["particion"],
            "Pérdida (φ)": resultado["perdida"],
            "Tiempo (s)": resultado["tiempo"],
        })

    df_resultados = pd.DataFrame(resultados)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_resultados.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"Resultados guardados en {ruta_salida}")

def iniciar():
    ruta_entrada = Path(
        os.getenv(
            "GEOMIP_INPUT_XLSX",
            str(PROJECT_ROOT / "data" / "DatosPruebas2026_1.xlsx"),
        )
    )
    estado_inicio = os.getenv("GEOMIP_ESTADO_INICIO", "1" + "0" * 14)
    n = len(estado_inicio)

    ruta_salida_default = str(RESULTS_DIR / f"resultados_N{n}B.csv")
    ruta_salida = Path(os.getenv("GEOMIP_OUTPUT_CSV", ruta_salida_default))

    ejecutar_desde_excel(ruta_entrada, ruta_salida, estado_inicio=estado_inicio)