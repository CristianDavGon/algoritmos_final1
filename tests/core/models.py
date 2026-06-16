from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class TestCase:
    """A single (alcance, mecanismo) pair loaded from the Excel file."""

    index: int
    alcance_letras: str
    mecanismo_letras: str
    alcance_bin: str
    mecanismo_bin: str
    estado_inicial: str
    condicion: str


@dataclass
class PartitionResult:
    """Normalized result from any strategy or PyPhi — k-partition ready."""

    estrategia: str
    perdida: float
    particion: str
    dist_subsistema: np.ndarray
    dist_particion: np.ndarray
    tiempo: float
    error: Optional[str] = None


@dataclass
class RunRecord:
    """Pairing of a reference result with a candidate result for one test case."""

    test_case: TestCase
    referencia: PartitionResult
    candidato: PartitionResult
    phi_delta: Optional[float] = None
    phi_relative_error_pct: Optional[float] = None
    phi_match: Optional[bool] = None
    partition_match: Optional[bool] = None
    speedup: Optional[float] = None
    from_cache: bool = False


@dataclass
class BenchmarkReport:
    """Aggregate statistics for a complete benchmark run."""

    strategy_name: str
    n_nodes: int
    tpm_page: str
    estado_inicial: str
    total_tests: int
    phi_matches: int
    partition_matches: int
    reference_name: str = "pyphi"
    speedups: list[float] = field(default_factory=list)
    delta_phis: list[float] = field(default_factory=list)
    records: list[RunRecord] = field(default_factory=list)

    @property
    def phi_accuracy_pct(self) -> float:
        return 100.0 * self.phi_matches / self.total_tests if self.total_tests else 0.0

    @property
    def partition_accuracy_pct(self) -> float:
        return 100.0 * self.partition_matches / self.total_tests if self.total_tests else 0.0

    @property
    def avg_speedup(self) -> Optional[float]:
        return sum(self.speedups) / len(self.speedups) if self.speedups else None

    @property
    def avg_delta_phi(self) -> Optional[float]:
        return sum(self.delta_phis) / len(self.delta_phis) if self.delta_phis else None

    @property
    def max_delta_phi(self) -> Optional[float]:
        return max(self.delta_phis) if self.delta_phis else None
