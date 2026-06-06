"""Generic single-run benchmark driver.

Usage (from the code/ directory):
    python tests/run_benchmark.py --algo qnodes  --estado 10000 --pagina A
    python tests/run_benchmark.py --algo geomip  --estado 10000 --pagina A
    python tests/run_benchmark.py --algo qnodes  --estado 10000 --pagina A --reference bruteforce
    python tests/run_benchmark.py --algo qnodes  --estado 10000 --pagina A --n-tests 5

--reference pyphi      (default) compare against PyPhi
--reference bruteforce           compare against BruteForce (use only N <= 6)

Each invocation handles ONLY one algorithm so there is no src.* import shadowing
between QNodes and GeoMIP.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _TESTS_ROOT.parent
if str(_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CODE_ROOT))

import numpy as np

from tests.cache import PyPhiCache
from tests.excel_loader import cargar_casos
from tests.runners.benchmark import BenchmarkRunner

_EXCEL_PATH = _CODE_ROOT / "data" / "DatosPruebas2026_1.xlsx"
_BRUTEFORCE_CACHE = _CODE_ROOT / "tests" / "data" / "bruteforce_cache.json"


def _load_tpm_qnodes(n: int, pagina: str) -> np.ndarray:
    path = _CODE_ROOT / "QNodes" / "src" / ".samples" / f"N{n}{pagina}.csv"
    if not path.exists():
        raise FileNotFoundError(f"QNodes TPM not found: {path}")
    return np.genfromtxt(path, delimiter=",")


def _load_tpm_geomip(n: int, pagina: str) -> np.ndarray:
    for candidate in (
        _CODE_ROOT / "GeoMIP" / "data" / "samples" / f"N{n}{pagina}.csv",
        _CODE_ROOT / "GeoMIP" / "src" / ".samples" / f"N{n}{pagina}.csv",
    ):
        if candidate.exists():
            return np.genfromtxt(candidate, delimiter=",")
    raise FileNotFoundError(f"GeoMIP TPM N{n}{pagina}.csv not found")


def run_qnodes(estado: str, pagina: str, n_tests: int | None, reference: str) -> None:
    from tests.adapters.qnodes_adapter import QNodesAdapter, QNodesPyPhiAdapter

    n = len(estado)
    tpm = _load_tpm_qnodes(n, pagina)
    casos = cargar_casos(_EXCEL_PATH, n, estado, n_tests)

    if reference == "bruteforce":
        from tests.adapters.bruteforce_adapter import QNodesBruteForceAdapter
        ref_adapter = QNodesBruteForceAdapter(pagina)
        cache = PyPhiCache(_BRUTEFORCE_CACHE)
    else:
        ref_adapter = QNodesPyPhiAdapter(pagina)
        cache = PyPhiCache()

    runner = BenchmarkRunner(
        strategy_adapter=QNodesAdapter(pagina),
        pyphi_adapter=ref_adapter,
        cache=cache,
        tol_phi=1e-4,
        reference_name=reference,
    )
    runner.run(casos, tpm, n, pagina, estado)


def run_geomip(estado: str, pagina: str, n_tests: int | None, reference: str) -> None:
    from tests.adapters.geomip_adapter import GeoMIPAdapter, GeoMIPPyPhiAdapter

    n = len(estado)
    tpm = _load_tpm_geomip(n, pagina)
    casos = cargar_casos(_EXCEL_PATH, n, estado, n_tests)

    if reference == "bruteforce":
        from tests.adapters.bruteforce_adapter import GeoMIPBruteForceAdapter
        ref_adapter = GeoMIPBruteForceAdapter(pagina)
        cache = PyPhiCache(_BRUTEFORCE_CACHE)
    else:
        ref_adapter = GeoMIPPyPhiAdapter(pagina)
        cache = PyPhiCache()

    runner = BenchmarkRunner(
        strategy_adapter=GeoMIPAdapter(pagina),
        pyphi_adapter=ref_adapter,
        cache=cache,
        tol_phi=1e-4,
        reference_name=reference,
    )
    runner.run(casos, tpm, n, pagina, estado)


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-algorithm benchmark runner")
    parser.add_argument("--algo", required=True, choices=["qnodes", "geomip"],
                        help="Algorithm to benchmark")
    parser.add_argument("--estado", required=True,
                        help="Binary initial state string, e.g. 10000")
    parser.add_argument("--pagina", required=True,
                        help="Network page letter, e.g. A or B")
    parser.add_argument("--reference", default="pyphi", choices=["pyphi", "bruteforce"],
                        help="Reference oracle (default: pyphi)")
    parser.add_argument("--n-tests", type=int, default=None,
                        help="Limit number of test cases (default: all)")
    args = parser.parse_args()

    if args.algo == "qnodes":
        run_qnodes(args.estado, args.pagina, args.n_tests, args.reference)
    else:
        run_geomip(args.estado, args.pagina, args.n_tests, args.reference)


if __name__ == "__main__":
    main()
