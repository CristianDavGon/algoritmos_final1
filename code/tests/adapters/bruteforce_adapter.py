from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

from tests.adapters.base import PyPhiAdapter
from tests.models import PartitionResult, TestCase

_QNODES_ROOT = Path(__file__).resolve().parents[2] / "QNodes"
_GEOMIP_ROOT = Path(__file__).resolve().parents[2] / "GeoMIP"


def _ensure_qnodes_path() -> None:
    """Add QNodes root to sys.path[0] if not already present."""
    root_str = str(_QNODES_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _ensure_geomip_path() -> None:
    """Add GeoMIP root to sys.path[0] if not already present."""
    root_str = str(_GEOMIP_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _resolve_geomip_tpm_path(n: int, pagina: str) -> Path:
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


class QNodesBruteForceAdapter(PyPhiAdapter):
    """Adaptador de BruteForce como oráculo de referencia para el módulo QNodes.

    Reemplaza a QNodesPyPhiAdapter: en vez de llamar a Phi(tpm), llama a
    BruteForce(tpm) con la misma firma de aplicar_estrategia.

    Args:
        pagina: Letra de página de red, p.ej. "A".
    """

    def __init__(self, pagina: str = "A") -> None:
        self._pagina = pagina
        _ensure_qnodes_path()
        from src.models.base.application import aplicacion  # noqa: PLC0415
        aplicacion.set_pagina_red_muestra(pagina)
        aplicacion.desactivar_profiling()

    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Ejecuta BruteForce (QNodes) como referencia para un caso de prueba."""
        _ensure_qnodes_path()
        try:
            from src.strategies.force import BruteForce  # noqa: PLC0415
            sol = BruteForce(tpm).aplicar_estrategia(
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
            return _empty_result("BruteForce", str(exc))


class GeoMIPBruteForceAdapter(PyPhiAdapter):
    """Adaptador de BruteForce como oráculo de referencia para el módulo GeoMIP.

    Reemplaza a GeoMIPPyPhiAdapter: en vez de llamar a Phi(config), llama a
    BruteForce(Manager(...)) con la misma firma de aplicar_estrategia.

    Args:
        pagina: Letra de página de red, p.ej. "A".
    """

    def __init__(self, pagina: str = "A") -> None:
        self._pagina = pagina
        _ensure_geomip_path()
        from src.models.base.application import aplicacion  # noqa: PLC0415
        aplicacion.pagina_sample_network = pagina
        aplicacion.profiler_habilitado = False

    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Ejecuta BruteForce (GeoMIP) como referencia para un caso de prueba."""
        _ensure_geomip_path()
        n = len(test_case.estado_inicial)
        try:
            tpm_path = _resolve_geomip_tpm_path(n, self._pagina)
            os.environ["GEOMIP_SAMPLES_DIR"] = str(tpm_path.parent)
            from src.controllers.manager import Manager  # noqa: PLC0415
            from src.controllers.strategies.force import BruteForce  # noqa: PLC0415
            config = Manager(estado_inicial=test_case.estado_inicial)
            sol = BruteForce(config).aplicar_estrategia(
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
            return _empty_result("BruteForce", str(exc))
