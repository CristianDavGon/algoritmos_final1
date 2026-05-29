from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

from tests.adapters.base import PyPhiAdapter, StrategyAdapter
from tests.models import PartitionResult, TestCase

_QNODES_ROOT = Path(__file__).resolve().parents[2] / "QNodes"


def _ensure_qnodes_path() -> None:
    """Add QNodes root to sys.path[0] if not already present."""
    root_str = str(_QNODES_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


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


class QNodesAdapter(StrategyAdapter):
    """Adapter for the QNodes (Queyranne) algorithm.

    Args:
        pagina: Network page letter, e.g. "A".
    """

    def __init__(self, pagina: str = "A") -> None:
        self._pagina = pagina
        _ensure_qnodes_path()
        from src.models.base.application import aplicacion  # noqa: PLC0415
        aplicacion.set_pagina_red_muestra(pagina)
        aplicacion.desactivar_profiling()

    @property
    def strategy_name(self) -> str:
        return "QNodes"

    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Run QNodes strategy for one test case."""
        _ensure_qnodes_path()
        try:
            from src.strategies.qnodes import QNodes  # noqa: PLC0415
            sol = QNodes(tpm).aplicar_estrategia(
                test_case.estado_inicial,
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
            return _empty_result("QNodes", str(exc))


class QNodesPyPhiAdapter(PyPhiAdapter):
    """Adapter for PyPhi as called from the QNodes module context.

    Args:
        pagina: Network page letter, e.g. "A".
    """

    def __init__(self, pagina: str = "A") -> None:
        self._pagina = pagina
        _ensure_qnodes_path()
        from src.models.base.application import aplicacion  # noqa: PLC0415
        aplicacion.set_pagina_red_muestra(pagina)
        aplicacion.desactivar_profiling()

    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Run QNodes-PyPhi reference for one test case."""
        _ensure_qnodes_path()
        try:
            from src.strategies.phi import Phi  # noqa: PLC0415
            sol = Phi(tpm).aplicar_estrategia(
                test_case.estado_inicial,
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
