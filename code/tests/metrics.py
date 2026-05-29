from __future__ import annotations

from typing import Optional

from tests.models import BenchmarkReport, PartitionResult, RunRecord, TestCase

TOL_PHI_DEFAULT: float = 1e-4


def compute_run_record(
    test_case: TestCase,
    referencia: PartitionResult,
    candidato: PartitionResult,
    tol_phi: float = TOL_PHI_DEFAULT,
    from_cache: bool = False,
) -> RunRecord:
    """Compute all metrics for one test case pair.

    Args:
        test_case: The input parameters for this test.
        referencia: PyPhi (ground-truth) result.
        candidato: Algorithm result being evaluated.
        tol_phi: Tolerance for declaring phi values equal.
        from_cache: Whether referencia came from the persistent cache.

    Returns:
        RunRecord with phi_delta, phi_match, partition_match, speedup populated.
        Metric fields are None if either result has an error.
    """
    record = RunRecord(
        test_case=test_case,
        referencia=referencia,
        candidato=candidato,
        from_cache=from_cache,
    )

    if referencia.error or candidato.error:
        return record

    record.phi_delta = abs(referencia.perdida - candidato.perdida)
    record.phi_match = record.phi_delta < tol_phi
    record.partition_match = _particiones_iguales(referencia.particion, candidato.particion)
    if referencia.perdida != 0:
        record.phi_relative_error_pct = (record.phi_delta / abs(referencia.perdida)) * 100.0

    if referencia.tiempo > 0 and candidato.tiempo > 0:
        record.speedup = referencia.tiempo / candidato.tiempo

    return record


def _particiones_iguales(p1: str, p2: str) -> bool:
    """Compare two partition strings considering symmetric bipartition representation.

    A bipartition (A||B) is identical to (B||A). This function normalises both
    strings to a canonical form before comparing so that swapped-side
    representations are counted as equal.

    Extension point for k-partition: update _canonical_partition to parse
    k-way splits (more than one `||` delimiter per line).
    """
    return _canonical_partition(p1) == _canonical_partition(p2)


def _canonical_partition(text: str) -> frozenset[frozenset[str]]:
    """Convert a partition string to a canonical frozenset-of-frozensets.

    Each line of the partition has the form ``| PART_A || PART_B |``.
    Elements inside each part are comma-separated. Returns a frozenset of
    (frozenset_A, frozenset_B) pairs — one per line — so order within and
    between the two sides is irrelevant.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if "||" in ln]
    rows: list[frozenset[frozenset[str]]] = []
    for line in lines:
        # Remove outer pipes and split on ||
        clean = line.strip("|").strip()
        halves = clean.split("||")
        if len(halves) != 2:
            continue
        left = frozenset(e.strip().lower() for e in halves[0].split(",") if e.strip())
        right = frozenset(e.strip().lower() for e in halves[1].split(",") if e.strip())
        rows.append(frozenset({left, right}))
    return frozenset(rows)


def agregar_reporte(
    records: list[RunRecord],
    strategy_name: str,
    n_nodes: int,
    tpm_page: str,
    estado_inicial: str,
) -> BenchmarkReport:
    """Aggregate a list of RunRecords into a BenchmarkReport.

    Args:
        records: All run records for one benchmark run.
        strategy_name: Name of the algorithm under test.
        n_nodes: Number of nodes.
        tpm_page: Network page letter (e.g. "A").
        estado_inicial: Initial state binary string.

    Returns:
        BenchmarkReport with cumulative statistics.
    """
    report = BenchmarkReport(
        strategy_name=strategy_name,
        n_nodes=n_nodes,
        tpm_page=tpm_page,
        estado_inicial=estado_inicial,
        total_tests=len(records),
        phi_matches=0,
        partition_matches=0,
        records=records,
    )
    for r in records:
        if r.phi_match:
            report.phi_matches += 1
        if r.partition_match:
            report.partition_matches += 1
        if r.speedup is not None:
            report.speedups.append(r.speedup)
        if r.phi_delta is not None:
            report.delta_phis.append(r.phi_delta)
    return report
