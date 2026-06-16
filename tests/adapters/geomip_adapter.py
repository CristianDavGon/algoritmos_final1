from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

from tests.adapters.base import PyPhiAdapter, StrategyAdapter
from tests.core.models import PartitionResult, TestCase

_GEOMIP_ROOT = Path(__file__).resolve().parents[2] / "GeoMIP"


def _ensure_geomip_path() -> None:
    """Add GeoMIP root to sys.path[0] if not already present."""
    root_str = str(_GEOMIP_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _resolve_tpm_path(n: int, pagina: str) -> Path:
    """Locate NXY.csv in the GeoMIP samples directory."""
    candidates = (
        _GEOMIP_ROOT / "data" / "samples" / f"N{n}{pagina}.csv",
        _GEOMIP_ROOT / "src" / ".samples" / f"N{n}{pagina}.csv",
    )
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"N{n}{pagina}.csv not found. Searched: {[str(c) for c in candidates]}"
    )


def _empty_result(estrategia: str, error: str) -> PartitionResult:
    return PartitionResult(
        estrategia=estrategia,
        perdida=float("nan"),
        particion="",
        dist_subsistema=np.array([], dtype=np.float32),
        dist_particion=np.array([], dtype=np.float32),
        tiempo=0.0,
        error=error,
    )


class GeoMIPAdapter(StrategyAdapter):
    """Adapter for the GeometricSIA (GeoMIP) algorithm.

    Args:
        pagina: Network page letter, e.g. "A".
    """

    def __init__(self, pagina: str = "A") -> None:
        self._pagina = pagina
        _ensure_geomip_path()
        from src.models.base.application import aplicacion  # noqa: PLC0415
        aplicacion.pagina_sample_network = pagina
        aplicacion.profiler_habilitado = False

    @property
    def strategy_name(self) -> str:
        return "Geometric"

    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Run GeometricSIA for one test case."""
        _ensure_geomip_path()
        n = len(test_case.estado_inicial)
        try:
            tpm_path = _resolve_tpm_path(n, self._pagina)
            # GEOMIP_SAMPLES_DIR forces Manager.__post_init__ to the correct dir.
            os.environ["GEOMIP_SAMPLES_DIR"] = str(tpm_path.parent)
            from src.controllers.manager import Manager  # noqa: PLC0415
            from src.controllers.strategies.geometric import GeometricSIA  # noqa: PLC0415
            config = Manager(estado_inicial=test_case.estado_inicial)
            sol = GeometricSIA(config).aplicar_estrategia(
                test_case.condicion,
                test_case.alcance_bin,
                test_case.mecanismo_bin,
                tpm,
            )
            return PartitionResult(
                estrategia=sol.estrategia,
                perdida=sol.perdida,
                particion=sol.particion,
                dist_subsistema=sol.distribucion_subsistema,
                dist_particion=sol.distribucion_particion,
                tiempo=sol.tiempo_ejecucion,
            )
        except Exception as exc:
            return _empty_result("Geometric", str(exc))


class GeoMIPPyPhiAdapter(PyPhiAdapter):
    """Adapter for PyPhi as called from the GeoMIP module context.

    GeoMIP's Phi.aplicar_estrategia has signature (condiciones, alcance, mecanismo)
    — no estado_inicial parameter; state is read from Manager.estado_inicial.

    Args:
        pagina: Network page letter, e.g. "A".
    """

    def __init__(self, pagina: str = "A") -> None:
        self._pagina = pagina
        _ensure_geomip_path()
        from src.models.base.application import aplicacion  # noqa: PLC0415
        aplicacion.pagina_sample_network = pagina
        aplicacion.profiler_habilitado = False

    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Run GeoMIP-PyPhi reference for one test case."""
        _ensure_geomip_path()
        n = len(test_case.estado_inicial)
        try:
            tpm_path = _resolve_tpm_path(n, self._pagina)
            os.environ["GEOMIP_SAMPLES_DIR"] = str(tpm_path.parent)
            from src.controllers.manager import Manager  # noqa: PLC0415
            from src.controllers.strategies.phi import Phi  # noqa: PLC0415
            config = Manager(estado_inicial=test_case.estado_inicial)
            sol = Phi(config).aplicar_estrategia(
                test_case.condicion,
                test_case.alcance_bin,
                test_case.mecanismo_bin,
            )
            return PartitionResult(
                estrategia=sol.estrategia,
                perdida=sol.perdida,
                particion=sol.particion,
                dist_subsistema=sol.distribucion_subsistema,
                dist_particion=sol.distribucion_particion,
                tiempo=sol.tiempo_ejecucion,
            )
        except Exception as exc:
            return _empty_result("Pyphi", str(exc))
