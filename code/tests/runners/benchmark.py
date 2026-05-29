from __future__ import annotations

import numpy as np

from tests.adapters.base import PyPhiAdapter, StrategyAdapter
from tests.cache import PyPhiCache
from tests.metrics import agregar_reporte, compute_run_record
from tests.models import BenchmarkReport, TestCase
from tests.reporter import guardar_csv, guardar_markdown, imprimir_resumen


class BenchmarkRunner:
    """Orchestrates one strategy vs PyPhi benchmark run.

    Template Method: steps are fixed (cache check → PyPhi → candidate →
    metrics → report), adapters are injected.

    Args:
        strategy_adapter: Adapter for the algorithm under test.
        pyphi_adapter: Adapter for the PyPhi reference.
        cache: Shared PyPhi result cache.
        tol_phi: Tolerance for declaring phi values equal.
    """

    def __init__(
        self,
        strategy_adapter: StrategyAdapter,
        pyphi_adapter: PyPhiAdapter,
        cache: PyPhiCache,
        tol_phi: float = 1e-4,
    ) -> None:
        self._strategy = strategy_adapter
        self._pyphi = pyphi_adapter
        self._cache = cache
        self._tol_phi = tol_phi

    def run(
        self,
        test_cases: list[TestCase],
        tpm: np.ndarray,
        n_nodes: int,
        tpm_page: str,
        estado_inicial: str,
    ) -> BenchmarkReport:
        """Execute the full benchmark and return an aggregate report.

        Args:
            test_cases: List of test cases loaded from Excel.
            tpm: Pre-loaded TPM ndarray shared across all test cases.
            n_nodes: Network size (number of nodes).
            tpm_page: Network page letter, e.g. "A".
            estado_inicial: Initial state binary string.

        Returns:
            BenchmarkReport with all RunRecords and aggregate statistics.
            A CSV is written to tests/results/ and a summary printed to stdout.
        """
        records = []
        total = len(test_cases)

        print(f"\n  Ejecutando {self._strategy.strategy_name} vs PyPhi  —  N{n_nodes}{tpm_page}  ({total} casos)\n")

        for tc in test_cases:
            cached = self._cache.get(
                n_nodes, tpm_page, tc.estado_inicial, tc.alcance_bin, tc.mecanismo_bin
            )
            from_cache = cached is not None

            if cached is None:
                ref_result = self._pyphi.run(tc, tpm)
                if ref_result.error is None:
                    self._cache.put(
                        n_nodes,
                        tpm_page,
                        tc.estado_inicial,
                        tc.alcance_bin,
                        tc.mecanismo_bin,
                        ref_result,
                    )
            else:
                ref_result = cached

            cand_result = self._strategy.run(tc, tpm)

            record = compute_run_record(tc, ref_result, cand_result, self._tol_phi, from_cache)
            records.append(record)

            self._print_progress(tc, ref_result, cand_result, record, from_cache)

        report = agregar_reporte(
            records, self._strategy.strategy_name, n_nodes, tpm_page, estado_inicial
        )
        csv_path = guardar_csv(report)
        md_path = guardar_markdown(report)
        imprimir_resumen(report)
        print(f"  CSV: {csv_path}")
        print(f"  MD:  {md_path}\n")
        return report

    @staticmethod
    def _print_progress(tc, ref, cand, record, from_cache: bool) -> None:
        cache_tag = "[C]" if from_cache else "   "
        phi_sym = "ok" if record.phi_match else "!!"
        phi_ref = f"{ref.perdida:.4f}" if ref.error is None else "ERR"
        phi_cand = f"{cand.perdida:.4f}" if cand.error is None else "ERR"
        spd = f"  spd={record.speedup:.1f}x" if record.speedup is not None else ""
        print(
            f"  {cache_tag} #{tc.index:>3}"
            f"  A:{tc.alcance_letras:<8}"
            f"  M:{tc.mecanismo_letras:<8}"
            f"  phi={phi_ref}/{phi_cand} {phi_sym}"
            f"{spd}"
        )
