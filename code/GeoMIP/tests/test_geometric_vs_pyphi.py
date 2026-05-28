"""
Benchmark: GeometricSIA vs PyPhi
=================================
Ejecutar desde la raíz de GeoMIP/:
    python tests/test_geometric_vs_pyphi.py

─── CÓMO CONFIGURAR ────────────────────────────────────────────────────────────

  ESTADO_INICIO  →  su longitud determina N y la hoja del Excel:
                    "10000000"           → N=8  → hoja N=8  → carga N8A.csv / N8B.csv
                    "1000000000"         → N=10 → hoja N=10 → carga N10A.csv / N10B.csv
                    "100000000000000"    → N=15 → hoja N=15 → carga N15A.csv / N15B.csv
                    El primer bit SIEMPRE debe ser 1 (estado inicial canónico).

  PAGINA         →  elige la variante de red para ese tamaño:
                    "A" → usa N8A.csv   (red determinista semilla=73)
                    "B" → usa N8B.csv   (red alternativa del mismo tamaño)

  N_TESTS        →  cuántas filas del Excel ejecutar.
                    None → TODAS las pruebas de la hoja (recomendado para el MD).
                    10   → solo las primeras 10 filas.

  TOL_PHI        →  umbral para declarar φ "igual" entre PyPhi y GeometricSIA.

─────────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import csv
import re
from datetime import datetime
from pathlib import Path

# ── CONFIGURAR AQUÍ ──────────────────────────────────────────────────────────
ESTADO_INICIO = "10000"   # longitud = N nodos
PAGINA        = "A"          # "A" o "B"  (variante de red)
N_TESTS       = 4         # None = TODAS las pruebas de la hoja  |  10 = primeras 10
TOL_PHI       = 1e-4         # tolerancia para φ "igual"
# ─────────────────────────────────────────────────────────────────────────────

# Anclar sys.path al módulo GeoMIP/ para que "src.*" sea importable
_MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))

import numpy as np
import pandas as pd

# Parche de compatibilidad Python 3.10+: pyphi usa collections.Iterable
# que fue eliminado en 3.10 y movido a collections.abc.
import collections
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
if not hasattr(collections, "Iterable"):
    setattr(collections, "Iterable",       Iterable)
if not hasattr(collections, "Mapping"):
    setattr(collections, "Mapping",        Mapping)
if not hasattr(collections, "MutableMapping"):
    setattr(collections, "MutableMapping", MutableMapping)
if not hasattr(collections, "Sequence"):
    setattr(collections, "Sequence",       Sequence)

# Aplicar la página ANTES de importar/instanciar cualquier clase que la use
# GeoMIP usa pagina_sample_network (no set_pagina_red_muestra como QNodes)
from src.models.base.application import aplicacion
aplicacion.pagina_sample_network = PAGINA

from src.controllers.manager              import Manager
from src.controllers.strategies.phi       import Phi
from src.controllers.strategies.geometric import GeometricSIA


_PROJECT_ROOT = _MODULE_ROOT.parent
_EXCEL_PATH   = _PROJECT_ROOT / "data" / "DatosPruebas2026_1.xlsx"
_TESTS_DIR    = _MODULE_ROOT / "tests"
_RESULTS_DIR  = _TESTS_DIR / "results"
_MD_PATH      = _TESTS_DIR / "results.md"

_HOJA_POR_N: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}
_ESTRATEGIA = "Geometric"


# ── Helpers de datos ─────────────────────────────────────────────────────────

def _letras_a_binario(texto: str, n_bits: int) -> str:
    posiciones = "ABCDEFGHIJKLMNOPQRST"[:n_bits]
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)


def _leer_pruebas_excel(ruta_excel: Path, n: int) -> list[tuple[str, str]]:
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
    return [(str(r.alcance).strip(), str(r.mecanismo).strip()) for _, r in df.iterrows()]


def _resolver_tpm_path(estado_inicio: str) -> Path:
    n = len(estado_inicio)
    sample_name = f"N{n}{PAGINA}.csv"
    candidates = (
        _MODULE_ROOT / "src"  / ".samples"        / sample_name,
        _MODULE_ROOT          / ".samples"         / sample_name,
        _MODULE_ROOT          / "data" / "samples" / sample_name,
    )
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"No se encontró '{sample_name}'. Busqué en: {', '.join(str(c) for c in candidates)}"
    )


def _speedup(t_phi: float | None, t_est: float | None) -> float | None:
    if t_phi and t_est and t_est > 0:
        return round(t_phi / t_est, 2)
    return None


def _parsear_biparticion(raw: str | None) -> frozenset | None:
    """
    Convierte una bipartición al formato canónico:
      frozenset { (purv_frozenset, mech_frozenset), ... }
    El formato raw de GeoMIP es dos líneas:
      | purv_izq || purv_der |
      | mech_izq || mech_der |
    Devuelve None si no puede parsear.
    """
    if not raw:
        return None
    lines = [l for l in raw.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return None

    def _mitad(line: str, idx: int) -> frozenset:
        partes = line.split("||")
        if len(partes) < 2:
            return frozenset()
        token = partes[idx].strip("|").strip()
        return frozenset(n.strip() for n in token.split(",") if n.strip() and n.strip() != "∅")

    purv_izq  = _mitad(lines[0], 0)
    purv_der  = _mitad(lines[0], 1)
    mech_izq  = _mitad(lines[1], 0)
    mech_der  = _mitad(lines[1], 1)

    return frozenset([(purv_izq, mech_izq), (purv_der, mech_der)])


def _misma_particion(p1: str | None, p2: str | None) -> bool:
    """Compara biparticiones ignorando el orden de las partes (simétrico)."""
    if p1 is None and p2 is None:
        return True
    if p1 is None or p2 is None:
        return False
    if p1 == p2:
        return True
    c1, c2 = _parsear_biparticion(p1), _parsear_biparticion(p2)
    return c1 is not None and c1 == c2


# ── Salida visual en consola ──────────────────────────────────────────────────

_W = 66


def _print_header_global(n: int, total: int) -> None:
    print(f"\n{'━'*_W}")
    print(f"  BENCHMARK  {_ESTRATEGIA} vs PyPhi  │  Red: N{n}{PAGINA}  │  Pruebas: {total}")
    print(f"{'━'*_W}\n")


def _print_prueba(i: int, total: int, letras_alc: str, letras_mec: str,
                  sol_phi, sol_est) -> tuple:
    """Imprime la caja de una prueba. Devuelve (delta_phi, phi_ok, part_ok, speedup)."""
    print(f"  ┌── Prueba {i}/{total} {'─'*(_W-14)}")
    print(f"  │  Alcance  : {letras_alc}")
    print(f"  │  Mecanismo: {letras_mec}")
    print(f"  ├{'─'*(_W-2)}")
    print(f"  │  {'Estrategia':<10}  {'φ (perdida)':>14}  {'Tiempo':>10}  Partición")
    print(f"  │  {'─'*10}  {'─'*14}  {'─'*10}  {'─'*20}")

    def _fila(nombre: str, sol) -> None:
        if sol is None:
            print(f"  │  {nombre:<10}  {'ERROR':>14}  {'---':>10}  ---")
        else:
            print(f"  │  {nombre:<10}  {sol.perdida:>14.6f}  {sol.tiempo_ejecucion:>9.3f}s  {sol.particion or '---'}")

    _fila("PyPhi",      sol_phi)
    _fila(_ESTRATEGIA,  sol_est)

    delta_phi = phi_ok = part_ok = speedup = None

    if sol_phi is not None and sol_est is not None:
        delta_phi = abs(sol_phi.perdida - sol_est.perdida)
        phi_ok    = delta_phi < TOL_PHI
        part_ok   = _misma_particion(sol_phi.particion, sol_est.particion)
        speedup   = _speedup(sol_phi.tiempo_ejecucion, sol_est.tiempo_ejecucion)

        phi_sym  = "✓" if phi_ok  else "✗"
        part_sym = "✓" if part_ok else "✗"
        spd_str  = f"{speedup:.1f}x" if speedup is not None else "N/A"

        print(f"  │  {'─'*10}  {'─'*14}  {'─'*10}  {'─'*20}")
        print(f"  │  {'Δφ':<10}  {delta_phi:>12.6f} {phi_sym}  {'Speedup '+spd_str:>10}  Partición {part_sym}")

    print(f"  └{'─'*(_W-2)}\n")
    return delta_phi, phi_ok, part_ok, speedup


def _print_resumen(total: int, phi_m: int, part_m: int,
                   speedups: list, delta_phis: list, csv_path: Path) -> None:
    avg_spd = round(sum(speedups) / len(speedups), 2) if speedups else None
    avg_dph = sum(delta_phis) / len(delta_phis)       if delta_phis else None
    max_dph = max(delta_phis)                          if delta_phis else None

    print(f"\n{'━'*_W}")
    print(f"  RESUMEN  │  Red: N{len(ESTADO_INICIO)}{PAGINA}  │  {total} pruebas")
    print(f"{'━'*_W}")
    print(f"  Exactitud φ         : {phi_m}/{total}  ({100*phi_m/total:.1f}%)")
    print(f"  Exactitud partición : {part_m}/{total}  ({100*part_m/total:.1f}%)")
    if avg_spd:  print(f"  Speedup promedio    : {avg_spd}x")
    else:        print(f"  Speedup promedio    : N/A")
    if avg_dph is not None: print(f"  Δφ promedio         : {avg_dph:.6f}")
    if max_dph is not None: print(f"  Δφ máximo           : {max_dph:.6f}")
    print(f"  CSV guardado en     : {csv_path}")
    print(f"{'━'*_W}\n")


# ── Generador de Markdown ─────────────────────────────────────────────────────

def _fmt_particion(raw: str | None) -> str:
    if not raw:
        return "---"
    return " ".join(raw.replace("|", "∣").split())


def _construir_seccion_md(n: int, filas: list[dict],
                           phi_m: int, part_m: int,
                           speedups: list, delta_phis: list) -> str:
    red   = f"N{n}{PAGINA}"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(filas)
    avg_spd = round(sum(speedups) / len(speedups), 2) if speedups else None
    avg_dph = sum(delta_phis) / len(delta_phis)       if delta_phis else None
    max_dph = max(delta_phis)                          if delta_phis else None

    lines: list[str] = []
    lines.append(f"## {red} — {n} nodos · {total} pruebas · {ahora}\n")

    for f in filas:
        part_phi = _fmt_particion(f["Partición_PyPhi"])
        part_est = _fmt_particion(f[f"Partición_{_ESTRATEGIA}"])

        phi_phi  = f"{f['φ_PyPhi']:.6f}"              if f["φ_PyPhi"]        is not None else "ERROR"
        phi_est  = f"{f[f'φ_{_ESTRATEGIA}']:.6f}"     if f[f"φ_{_ESTRATEGIA}"] is not None else "ERROR"

        t_phi    = f"{f['t_PyPhi (s)']:.3f} s"        if f["t_PyPhi (s)"]    is not None else "---"
        t_est    = f"{f[f't_{_ESTRATEGIA} (s)']:.3f} s" if f[f"t_{_ESTRATEGIA} (s)"] is not None else "---"

        part_sym = "✓" if f["part_match"] else ("✗" if f["part_match"] is not None else "—")
        phi_sym  = "✓" if f["φ_match"]   else ("✗" if f["φ_match"]   is not None else "—")
        delta    = f"Δφ = {f['Δφ']:.6f}" if f["Δφ"] is not None else ""
        spd      = f"{f['speedup']:.1f}x speedup" if f["speedup"] is not None else "—"

        lines.append(f"#### Prueba {f['Prueba']} · Alcance: `{f['Alcance']}` · Mecanismo: `{f['Mecanismo']}`\n")
        lines.append(f"|                | Partición | φ (pérdida) | Tiempo (s) |")
        lines.append(f"|----------------|-----------|-------------|------------|")
        lines.append(f"| **PyPhi**      | {part_phi} | {phi_phi} | {t_phi} |")
        lines.append(f"| **{_ESTRATEGIA}** | {part_est} | {phi_est} | {t_est} |")
        lines.append(f"| **Match**      | {part_sym} | {phi_sym} {delta} | {spd} |")
        lines.append("")

    lines.append("### Resumen\n")
    lines.append("| Métrica | Valor |")
    lines.append("|---------|-------|")
    lines.append(f"| Exactitud φ | {phi_m}/{total} ({100*phi_m/total:.1f}%) |")
    lines.append(f"| Exactitud partición | {part_m}/{total} ({100*part_m/total:.1f}%) |")
    lines.append(f"| Speedup promedio | {avg_spd}x |" if avg_spd else "| Speedup promedio | N/A |")
    lines.append(f"| Δφ promedio | {avg_dph:.6f} |"   if avg_dph is not None else "| Δφ promedio | N/A |")
    lines.append(f"| Δφ máximo | {max_dph:.6f} |"     if max_dph is not None else "| Δφ máximo | N/A |")
    lines.append(f"| Tolerancia φ | {TOL_PHI} |")
    lines.append("")

    return "\n".join(lines)


def _guardar_markdown(n: int, filas: list[dict],
                       phi_m: int, part_m: int,
                       speedups: list, delta_phis: list) -> None:
    red    = f"N{n}{PAGINA}"
    inicio = f"<!-- BEGIN:{red} -->"
    fin    = f"<!-- END:{red} -->"
    seccion = f"{inicio}\n{_construir_seccion_md(n, filas, phi_m, part_m, speedups, delta_phis)}{fin}\n"

    if _MD_PATH.exists():
        contenido = _MD_PATH.read_text(encoding="utf-8")
        patron    = re.compile(
            rf"{re.escape(inicio)}.*?{re.escape(fin)}\n?",
            re.DOTALL,
        )
        if patron.search(contenido):
            contenido = patron.sub(seccion, contenido)
        else:
            contenido = contenido.rstrip("\n") + "\n\n---\n\n" + seccion
    else:
        contenido = (
            f"# Benchmark {_ESTRATEGIA} vs PyPhi\n\n"
            "Cada sección se actualiza automáticamente al correr "
            "`test_geometric_vs_pyphi.py` con la red correspondiente.\n\n"
            "---\n\n"
            + seccion
        )

    _MD_PATH.write_text(contenido, encoding="utf-8")
    print(f"  MD  actualizado en  : {_MD_PATH}")


# ── Benchmark principal ───────────────────────────────────────────────────────

def ejecutar_benchmark() -> None:
    n           = len(ESTADO_INICIO)
    condiciones = "1" * n

    tpm_path = _resolver_tpm_path(ESTADO_INICIO)
    tpm      = np.genfromtxt(tpm_path, delimiter=",")

    # Forzar al Manager a buscar los CSV en la carpeta correcta.
    # __post_init__ del Manager encuentra src/.samples/ (vacía) antes que
    # data/samples/ — GEOMIP_SAMPLES_DIR tiene prioridad sobre esa búsqueda.
    os.environ["GEOMIP_SAMPLES_DIR"] = str(tpm_path.parent)

    pruebas = _leer_pruebas_excel(_EXCEL_PATH, n)
    if N_TESTS is not None:
        pruebas = pruebas[:N_TESTS]

    _print_header_global(n, len(pruebas))

    filas_csv:  list[dict]  = []
    phi_matches = part_matches = 0
    speedups:   list[float] = []
    delta_phis: list[float] = []

    for i, (letras_alc, letras_mec) in enumerate(pruebas, start=1):
        alcance   = _letras_a_binario(letras_alc, n)
        mecanismo = _letras_a_binario(letras_mec, n)

        sol_phi = sol_est = None
        try:
            sol_phi = Phi(Manager(estado_inicial=ESTADO_INICIO)).aplicar_estrategia(
                condiciones, alcance, mecanismo
            )
        except Exception as e:
            print(f"  [PyPhi ERROR prueba {i}] {e}")

        try:
            sol_est = GeometricSIA(Manager(estado_inicial=ESTADO_INICIO)).aplicar_estrategia(
                condiciones, alcance, mecanismo, tpm
            )
        except Exception as e:
            print(f"  [{_ESTRATEGIA} ERROR prueba {i}] {e}")

        delta_phi, phi_ok, part_ok, speedup = _print_prueba(
            i, len(pruebas), letras_alc, letras_mec, sol_phi, sol_est
        )

        if phi_ok  : phi_matches  += 1
        if part_ok : part_matches += 1
        if speedup : speedups.append(speedup)
        if delta_phi is not None: delta_phis.append(delta_phi)

        filas_csv.append({
            "Prueba":                    i,
            "Alcance":                   letras_alc,
            "Mecanismo":                 letras_mec,
            "φ_PyPhi":                   sol_phi.perdida              if sol_phi else None,
            f"φ_{_ESTRATEGIA}":          sol_est.perdida              if sol_est else None,
            "Δφ":                        delta_phi,
            "φ_match":                   phi_ok,
            "Partición_PyPhi":           sol_phi.particion            if sol_phi else None,
            f"Partición_{_ESTRATEGIA}":  sol_est.particion            if sol_est else None,
            "part_match":                part_ok,
            "t_PyPhi (s)":               sol_phi.tiempo_ejecucion     if sol_phi else None,
            f"t_{_ESTRATEGIA} (s)":      sol_est.tiempo_ejecucion     if sol_est else None,
            "speedup":                   speedup,
        })

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = _RESULTS_DIR / f"comparacion_N{n}{PAGINA}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas_csv[0].keys()))
        writer.writeheader()
        writer.writerows(filas_csv)

    _print_resumen(len(pruebas), phi_matches, part_matches, speedups, delta_phis, csv_path)
    _guardar_markdown(n, filas_csv, phi_matches, part_matches, speedups, delta_phis)


if __name__ == "__main__":
    ejecutar_benchmark()
