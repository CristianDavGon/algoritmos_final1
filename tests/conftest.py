"""pytest configuration for the IIT benchmark test suite.

ARCHITECTURE CONSTRAINT — sys.path isolation:
    Both QNodes and GeoMIP use `src.*` as their root package.
    Running test_qnodes_vs_pyphi.py and test_geomip_vs_pyphi.py in the same
    pytest process will cause one module's `src` to shadow the other.

    Run each file in a separate process:
        pytest tests/test_qnodes_vs_pyphi.py -v -s
        pytest tests/test_geomip_vs_pyphi.py -v -s

    Do NOT use `pytest tests/` (collects both in one process).
"""
import pytest
from pathlib import Path

_CODE_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _CODE_ROOT.parent


@pytest.fixture(scope="session")
def excel_path() -> Path:
    return _PROJECT_ROOT / "data" / "DatosPruebas2026_1.xlsx"


@pytest.fixture(scope="session")
def code_root() -> Path:
    return _CODE_ROOT
