from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from tests.core.models import PartitionResult, TestCase


class StrategyAdapter(ABC):
    """Abstract adapter presenting a uniform interface to BenchmarkRunner.

    Concrete subclasses wrap QNodes or GeoMIP, handling sys.path anchoring,
    Application singleton configuration, and signature translation.

    Extension point for k-partition: implement a new adapter that wraps a
    k-partition algorithm without modifying any other code.
    """

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Human-readable name, e.g. "QNodes" or "Geometric"."""

    @abstractmethod
    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Execute the algorithm for one test case.

        Args:
            test_case: Contains estado_inicial, condicion, alcance_bin, mecanismo_bin.
            tpm: Pre-loaded TPM array (loaded once per benchmark run by the runner).

        Returns:
            PartitionResult with all fields populated, or error set on exception.
        """


class PyPhiAdapter(ABC):
    """Abstract adapter for the PyPhi reference strategy.

    Separate from StrategyAdapter because each module (QNodes, GeoMIP) has
    its own PyPhi wrapper with a different call signature.
    """

    @property
    def partition_type(self) -> str:
        """PARTITION_TYPE used for PyPhi calls. Included in cache key."""
        return "BI"

    @abstractmethod
    def run(self, test_case: TestCase, tpm: np.ndarray) -> PartitionResult:
        """Execute PyPhi for one test case and return the result."""
