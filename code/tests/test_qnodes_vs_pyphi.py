"""QNodes vs PyPhi benchmark.

Run standalone (from code/ directory):
    python tests/test_qnodes_vs_pyphi.py

Run via pytest (separate invocation — do NOT combine with test_geomip_vs_pyphi.py):
    pytest tests/test_qnodes_vs_pyphi.py -v -s

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
ESTADO_INICIO: str = "1"  + "0" * 4  # length = N nodes  (10 nodes → N10)
PAGINA: str = "A"
N_TESTS: int | None = None        # None = all test cases from Excel (~49)
TOL_PHI: float = 1e-4
# ──────────────────────────────────────────────────────────────────────────────

import numpy as np

from tests.adapters.qnodes_adapter import QNodesAdapter, QNodesPyPhiAdapter
from tests.cache import PyPhiCache
from tests.excel_loader import cargar_casos
from tests.runners.benchmark import BenchmarkRunner

_PROJECT_ROOT = _CODE_ROOT.parent
_EXCEL_PATH = _CODE_ROOT / "data" / "DatosPruebas2026_1.xlsx"
_QNODES_ROOT = _CODE_ROOT / "QNodes"
_SAMPLES_DIR = _QNODES_ROOT / "src" / ".samples"


def _load_tpm(n: int, pagina: str) -> np.ndarray:
    path = _SAMPLES_DIR / f"N{n}{pagina}.csv"
    if not path.exists():
        raise FileNotFoundError(f"TPM file not found: {path}")
    return np.genfromtxt(path, delimiter=",")


def ejecutar_benchmark() -> None:
    n = len(ESTADO_INICIO)
    tpm = _load_tpm(n, PAGINA)
    casos = cargar_casos(_EXCEL_PATH, n, ESTADO_INICIO, N_TESTS)
    runner = BenchmarkRunner(
        strategy_adapter=QNodesAdapter(PAGINA),
        pyphi_adapter=QNodesPyPhiAdapter(PAGINA),
        cache=PyPhiCache(),
        tol_phi=TOL_PHI,
    )
    runner.run(casos, tpm, n, PAGINA, ESTADO_INICIO)


def test_qnodes_phi_accuracy() -> None:
    """pytest: QNodes phi accuracy must meet the minimum threshold."""
    n = len(ESTADO_INICIO)
    tpm = _load_tpm(n, PAGINA)
    casos = cargar_casos(_EXCEL_PATH, n, ESTADO_INICIO, N_TESTS)
    runner = BenchmarkRunner(
        strategy_adapter=QNodesAdapter(PAGINA),
        pyphi_adapter=QNodesPyPhiAdapter(PAGINA),
        cache=PyPhiCache(),
        tol_phi=TOL_PHI,
    )
    report = runner.run(casos, tpm, n, PAGINA, ESTADO_INICIO)
    assert report.phi_accuracy_pct >= 80.0, (
        f"QNodes phi accuracy {report.phi_accuracy_pct:.1f}% is below the 80% threshold"
    )


if __name__ == "__main__":
    ejecutar_benchmark()
