"""GeoMIP (GeometricSIA) vs BruteForce benchmark.

BruteForce actúa como oráculo de referencia (ground-truth) en lugar de PyPhi.
Usar solo para n <= 6 porque BruteForce es exponencial en tiempo.

Run standalone (from code/ directory):
    python tests/test_geomip_vs_bruteforce.py

Run via pytest (separate invocation):
    pytest tests/test_geomip_vs_bruteforce.py -v -s

IMPORTANT: Both QNodes and GeoMIP use `src.*` as their root package.
Running both test files in the same pytest process causes import shadowing.
Always invoke them as separate pytest commands.

CONFIGURATION
─────────────
Edit the constants below to change network size, page, or number of tests.
ESTADO_INICIO length determines N (number of nodes). Use N <= 6 with BruteForce.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _TESTS_ROOT.parent
if str(_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CODE_ROOT))

# ─── CONFIGURE HERE ───────────────────────────────────────────────────────────
ESTADO_INICIO: str = "11111111" # length = N nodes — use N <= 6 with BruteForce
PAGINA: str = "A"
N_TESTS: int | None = None        # None = all test cases from Excel (~49)
TOL_PHI: float = 1e-9
# ──────────────────────────────────────────────────────────────────────────────

import numpy as np

from tests.adapters.geomip_adapter import GeoMIPAdapter
from tests.adapters.bruteforce_adapter import GeoMIPBruteForceAdapter
from tests.cache import PyPhiCache
from tests.excel_loader import cargar_casos
from tests.runners.benchmark import BenchmarkRunner

_EXCEL_PATH = _CODE_ROOT / "data" / "DatosPruebas2026_1.xlsx"
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"
_BRUTEFORCE_CACHE = _CODE_ROOT / "tests" / "data" / "bruteforce_cache.json"


def _load_tpm(n: int, pagina: str) -> np.ndarray:
    candidates = (
        _GEOMIP_ROOT / "data" / "samples" / f"N{n}{pagina}.csv",
        _GEOMIP_ROOT / "src" / ".samples" / f"N{n}{pagina}.csv",
    )
    for c in candidates:
        if c.exists():
            return np.genfromtxt(c, delimiter=",")
    raise FileNotFoundError(f"N{n}{pagina}.csv not found in GeoMIP sample paths")


def ejecutar_benchmark() -> None:
    n = len(ESTADO_INICIO)
    tpm = _load_tpm(n, PAGINA)
    casos = cargar_casos(_EXCEL_PATH, n, ESTADO_INICIO, N_TESTS)
    runner = BenchmarkRunner(
        strategy_adapter=GeoMIPAdapter(PAGINA),
        pyphi_adapter=GeoMIPBruteForceAdapter(PAGINA),
        cache=PyPhiCache(_BRUTEFORCE_CACHE),
        tol_phi=TOL_PHI,
        reference_name="bruteforce",
    )
    runner.run(casos, tpm, n, PAGINA, ESTADO_INICIO)


def test_geomip_phi_accuracy_vs_bruteforce() -> None:
    """pytest: GeoMIP phi accuracy vs BruteForce must be 100%."""
    n = len(ESTADO_INICIO)
    tpm = _load_tpm(n, PAGINA)
    casos = cargar_casos(_EXCEL_PATH, n, ESTADO_INICIO, N_TESTS)
    runner = BenchmarkRunner(
        strategy_adapter=GeoMIPAdapter(PAGINA),
        pyphi_adapter=GeoMIPBruteForceAdapter(PAGINA),
        cache=PyPhiCache(_BRUTEFORCE_CACHE),
        tol_phi=TOL_PHI,
        reference_name="bruteforce",
    )
    report = runner.run(casos, tpm, n, PAGINA, ESTADO_INICIO)
    assert report.phi_accuracy_pct >= 100.0, (
        f"GeoMIP phi accuracy vs BruteForce {report.phi_accuracy_pct:.1f}% is below 100%"
    )


if __name__ == "__main__":
    ejecutar_benchmark()
