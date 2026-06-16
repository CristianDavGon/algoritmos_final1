"""
Orquestación batch de GeoMIP: lectura de Excel, ejecución y exportación CSV+MD.

Módulo principal de ejecución de GeoMIP. Lee el archivo de pruebas
``DatosPruebas2026_1.xlsx``, convierte letras (A, B, …) a vectores binarios,
instancia ``GeometricSIA`` y ejecuta el análisis de bipartición sobre cada
par (alcance, mecanismo). Para n ≤ ``UMBRAL_POOL`` usa ejecución directa;
para n > ``UMBRAL_POOL`` usa ``multiprocessing.Pool`` con timeout.
Los resultados se exportan a CSV y a Markdown.

Typical usage example::

    from src.main import iniciar
    iniciar(estado="10000000")
"""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path

import numpy as np
import pandas as pd

from src.controllers.manager import Manager
from src.controllers.strategies.geometric import GeometricSIA
from src.models.base.application import aplicacion
from src.reporter import guardar_markdown

try:
    from src.controllers.strategies.phi import Phi
except Exception:
    Phi = None  # Dependencia opcional: PyPhi puede no estar instalado


GEOMIP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = GEOMIP_ROOT / "results" / "geomip"

_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}
TIMEOUT_SEGUNDOS: int = 3600
UMBRAL_POOL: int = 20
ABECEDARIO: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _letras_a_binario(texto: str, n_bits: int) -> str:
    """Convierte letras de nodos a vector binario de longitud ``n_bits``.

    Mapea cada letra al índice correspondiente (A=0, B=1, …) y activa el
    bit en esa posición. Letras no reconocidas se ignoran.

    Args:
        texto (str): Letras del alcance o mecanismo (p. ej. ``"ABC"``).
        n_bits (int): Longitud del vector binario (= número de nodos n).

    Returns:
        str: Cadena binaria de longitud ``n_bits`` (p. ej. ``"11100...0"``).
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
    """Lee pares (alcance, mecanismo) del Excel canónico de pruebas.

    Selecciona la hoja según ``n`` (mapeada por ``_N_A_SHEET``), salta las
    primeras 5 filas de encabezado y extrae las columnas B y C.

    Args:
        ruta_excel (Path): Ruta al archivo ``DatosPruebas2026_1.xlsx``.
        n (int): Tamaño de la red; determina la hoja del Excel.

    Returns:
        list[tuple[str, str]]: Lista de pares ``(alcance, mecanismo)``
            en formato de letras (p. ej. ``("ABC", "AB")``).
    """
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
    return [
        (str(r.alcance).strip(), str(r.mecanismo).strip())
        for _, r in df.iterrows()
    ]


def resolver_tpm_path(estado_inicio: str) -> Path:
    """Localiza el archivo CSV de la TPM para el estado dado.

    Busca ``N{n}A.csv`` en los directorios candidatos en orden de prioridad.

    Args:
        estado_inicio (str): Estado inicial binario; su longitud define n.

    Returns:
        Path: Ruta al archivo CSV de la TPM encontrado.

    Raises:
        FileNotFoundError: Si el archivo no existe en ninguna ubicación
            candidata.
    """
    sample_name = f"N{len(estado_inicio)}A.csv"
    candidates = (
        GEOMIP_ROOT / "src" / ".samples" / sample_name,
        GEOMIP_ROOT / ".samples" / sample_name,
        GEOMIP_ROOT / "data" / "samples" / sample_name,
    )
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"No se encontró '{sample_name}'. Busqué en: "
        f"{', '.join(str(c) for c in candidates)}"
    )


_worker_tpm = None
_worker_analizador = None


def _init_worker(tpm: np.ndarray, estado_inicio: str) -> None:
    """Inicializa el worker del pool creando TPM y GeometricSIA una sola vez.

    Evita el overhead de pickling al instanciar el analizador en el proceso
    worker. Se llama una vez por proceso del pool.

    Args:
        tpm (np.ndarray): Matriz de Probabilidad de Transición precargada.
        estado_inicio (str): Estado inicial binario del sistema.
    """
    global _worker_tpm, _worker_analizador
    _worker_tpm = tpm
    _worker_analizador = GeometricSIA(Manager(estado_inicial=estado_inicio))


def _ejecutar_caso(
    condiciones: str, alcance: str, mecanismo: str
) -> dict:
    """Ejecuta un caso de análisis en el worker del pool.

    Args:
        condiciones (str): Vector binario de condición de fondo.
        alcance (str): Vector binario del alcance.
        mecanismo (str): Vector binario del mecanismo.

    Returns:
        dict: Diccionario con claves ``particion``, ``perdida``, ``tiempo``.
            Los valores son ``None`` si ocurre una excepción.
    """
    try:
        sia_dos = _worker_analizador.aplicar_estrategia(
            condiciones, alcance, mecanismo, _worker_tpm
        )
        return {
            "particion": sia_dos.particion,
            "perdida": sia_dos.perdida,
            "tiempo": sia_dos.tiempo_ejecucion,
        }
    except Exception:
        return {"particion": None, "perdida": None, "tiempo": None}


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    estado_inicio: str,
) -> None:
    """Ejecuta GeoMIP sobre todas las pruebas del Excel y exporta resultados.

    Para n ≤ ``UMBRAL_POOL``: ejecución directa en el proceso principal.
    Para n > ``UMBRAL_POOL``: pool de un worker con timeout de
    ``TIMEOUT_SEGUNDOS`` por prueba.

    Args:
        ruta_excel (Path): Ruta al archivo ``DatosPruebas2026_1.xlsx``.
        ruta_salida (Path): Ruta de salida del CSV de resultados.
        estado_inicio (str): Estado inicial binario del sistema.
    """
    n = len(estado_inicio)
    condiciones = "1" * n
    pruebas = _leer_pruebas_excel(ruta_excel, n)
    resultados = []

    tpm_path = resolver_tpm_path(estado_inicio)
    tpm = np.loadtxt(tpm_path, delimiter=",")

    if n <= UMBRAL_POOL:
        # Ejecución directa: elimina overhead de IPC por prueba.
        analizador = GeometricSIA(Manager(estado_inicial=estado_inicio))
        for i, (letras_alcance, letras_mecanismo) in enumerate(
            pruebas, start=1
        ):
            alcance = _letras_a_binario(letras_alcance, n)
            mecanismo = _letras_a_binario(letras_mecanismo, n)
            print(
                f"Prueba {i:>3} — Alcance: {letras_alcance:<10} "
                f"Mecanismo: {letras_mecanismo}"
            )
            try:
                sia_dos = analizador.aplicar_estrategia(
                    condiciones, alcance, mecanismo, tpm
                )
                resultado = {
                    "particion": sia_dos.particion,
                    "perdida": sia_dos.perdida,
                    "tiempo": sia_dos.tiempo_ejecucion,
                }
            except Exception:
                resultado = {
                    "particion": None,
                    "perdida": None,
                    "tiempo": None,
                }
            resultados.append({
                "Prueba": i,
                "Alcance": letras_alcance,
                "Mecanismo": letras_mecanismo,
                "Partición": resultado["particion"],
                "Pérdida (φ)": resultado["perdida"],
                "Tiempo (s)": resultado["tiempo"],
            })
    else:
        # Pool con timeout para redes grandes; GeometricSIA creado una vez.
        pool = multiprocessing.Pool(
            processes=1,
            initializer=_init_worker,
            initargs=(tpm, estado_inicio),
        )
        try:
            for i, (letras_alcance, letras_mecanismo) in enumerate(
                pruebas, start=1
            ):
                alcance = _letras_a_binario(letras_alcance, n)
                mecanismo = _letras_a_binario(letras_mecanismo, n)
                print(
                    f"Prueba {i:>3} — Alcance: {letras_alcance:<10} "
                    f"Mecanismo: {letras_mecanismo}"
                )
                async_result = pool.apply_async(
                    _ejecutar_caso, (condiciones, alcance, mecanismo)
                )
                try:
                    resultado = async_result.get(timeout=TIMEOUT_SEGUNDOS)
                except multiprocessing.TimeoutError:
                    print(f"  Tiempo límite alcanzado en prueba {i}.")
                    pool.terminate()
                    pool.join()
                    pool = multiprocessing.Pool(
                        processes=1,
                        initializer=_init_worker,
                        initargs=(tpm, estado_inicio),
                    )
                    resultado = {
                        "particion": None,
                        "perdida": None,
                        "tiempo": None,
                    }
                except Exception:
                    resultado = {
                        "particion": None,
                        "perdida": None,
                        "tiempo": None,
                    }
                resultados.append({
                    "Prueba": i,
                    "Alcance": letras_alcance,
                    "Mecanismo": letras_mecanismo,
                    "Partición": resultado["particion"],
                    "Pérdida (φ)": resultado["perdida"],
                    "Tiempo (s)": resultado["tiempo"],
                })
        finally:
            pool.terminate()
            pool.join()

    df_resultados = pd.DataFrame(resultados)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_resultados.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"  CSV: {ruta_salida}")
    ruta_md = guardar_markdown(
        resultados, ruta_salida.with_suffix(".md"), "GeoMIP", estado_inicio
    )
    print(f"  MD:  {ruta_md}")


def iniciar(estado: str | None = None) -> None:
    """Punto de entrada principal: procesa el Excel y ejecuta GeoMIP.

    Lee la ruta del Excel y del CSV de salida desde variables de entorno si
    están definidas; en caso contrario usa los valores por defecto del
    proyecto.

    Args:
        estado (str | None): Estado inicial binario. Si es ``None``, se lee
            de la variable de entorno ``GEOMIP_ESTADO_INICIO`` o se usa
            ``"1" + "0" * 24`` (n=25).
    """
    ruta_entrada = Path(
        os.getenv(
            "GEOMIP_INPUT_XLSX",
            str(PROJECT_ROOT / "data" / "DatosPruebas2026_1.xlsx"),
        )
    )
    estado_inicio = estado or os.getenv("GEOMIP_ESTADO_INICIO", "1" + "0" * 24)
    n = len(estado_inicio)
    muestra = aplicacion.pagina_sample_network

    ruta_salida_default = str(RESULTS_DIR / f"resultados_N{n}{muestra}.csv")
    ruta_salida = Path(os.getenv("GEOMIP_OUTPUT_CSV", ruta_salida_default))

    ejecutar_desde_excel(ruta_entrada, ruta_salida, estado_inicio=estado_inicio)
