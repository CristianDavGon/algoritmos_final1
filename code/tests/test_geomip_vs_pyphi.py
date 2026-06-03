"""GeoMIP (GeometricSIA) vs PyPhi benchmark.

Run standalone (from code/ directory):
    python tests/test_geomip_vs_pyphi.py

Run via pytest (separate invocation — do NOT combine with test_qnodes_vs_pyphi.py):
    pytest tests/test_geomip_vs_pyphi.py -v -s

IMPORTANT: Both QNodes and GeoMIP use `src.*` as their root package.
Running both test files in the same pytest process causes import shadowing.
Always invoke them as separate pytest commands.

CONFIGURATION
─────────────
Edit the constants below to change network size, page, or number of tests.
ESTADO_INICIO length determines N (number of nodes).
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _TESTS_ROOT.parent
if str(_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CODE_ROOT))

# ─── CONFIGURE HERE ───────────────────────────────────────────────────────────
ESTADO_INICIO: str = "10000"  # length = N nodes  (10 nodes → N10)
PAGINA: str = "A"
N_TESTS: int | None = None        # None = all test cases from Excel (~49)
TOL_PHI: float = 1e-4
# ──────────────────────────────────────────────────────────────────────────────

import numpy as np

from tests.adapters.geomip_adapter import GeoMIPAdapter, GeoMIPPyPhiAdapter
from tests.cache import PyPhiCache
from tests.excel_loader import cargar_casos
from tests.runners.benchmark import BenchmarkRunner

_EXCEL_PATH = _CODE_ROOT / "data" / "DatosPruebas2026_1.xlsx"
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"


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
        pyphi_adapter=GeoMIPPyPhiAdapter(PAGINA),
        cache=PyPhiCache(),
        tol_phi=TOL_PHI,
    )
    runner.run(casos, tpm, n, PAGINA, ESTADO_INICIO)


def test_geomip_phi_accuracy() -> None:
    """pytest: GeoMIP phi accuracy must meet the minimum threshold."""
    n = len(ESTADO_INICIO)
    tpm = _load_tpm(n, PAGINA)
    casos = cargar_casos(_EXCEL_PATH, n, ESTADO_INICIO, N_TESTS)
    runner = BenchmarkRunner(
        strategy_adapter=GeoMIPAdapter(PAGINA),
        pyphi_adapter=GeoMIPPyPhiAdapter(PAGINA),
        cache=PyPhiCache(),
        tol_phi=TOL_PHI,
    )
    report = runner.run(casos, tpm, n, PAGINA, ESTADO_INICIO)
    assert report.phi_accuracy_pct >= 60.0, (
        f"GeoMIP phi accuracy {report.phi_accuracy_pct:.1f}% is below the 60% threshold"
    )


if __name__ == "__main__":
    ejecutar_benchmark()
