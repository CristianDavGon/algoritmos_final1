from __future__ import annotations

import re
from typing import Optional

from tests.core.models import BenchmarkReport, PartitionResult, RunRecord, TestCase

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
    # k≥3 format: "⎛A⎞ / ⎝∅⎠ | ⎛B, C⎞ / ⎝∅⎠ | ⎛D⎞ / ⎝∅⎠"
    # Detected by ⎛ + ' | ' (space-pipe-space delimiter between parts)
    if '⎛' in text and ' | ' in text:
        parts = text.split(' | ')
        result = []
        for part in parts:
            nodes = re.findall(r'⎛([^⎞]*)⎞', part)
            combined = frozenset(
                e.strip().lower()
                for s in nodes
                for e in s.split(',')
                if e.strip() and e.strip() != '∅'
            )
            result.append(combined)
        return frozenset(result)
    # QNodes bipartition format: ⎛purv0⎞⎛purv1⎞ / ⎝mec0⎠⎝mec1⎠
    if '⎛' in text:
        tops = re.findall(r'⎛([^⎞]*)⎞', text)
        bottoms = re.findall(r'⎝([^⎠]*)⎠', text)
        if len(tops) < 2 or len(bottoms) < 2:
            return frozenset()
        parts = []
        for i in range(2):
            purv = frozenset(
                e.strip().lower()
                for e in tops[i].split(',')
                if e.strip() and e.strip() != '∅'
            )
            mech = frozenset(
                e.strip().lower()
                for e in bottoms[i].split(',')
                if e.strip() and e.strip() != '∅'
            )
            parts.append(frozenset({purv, mech}))
        return frozenset(parts)
    # PyPhi format: row0 = | purv_L || purv_R |, row1 = | mec_L || mec_R |
    # k≥3: row0 = | purv_0 || purv_1 || purv_2 |, etc.
    lines = [ln.strip() for ln in text.strip().splitlines() if '||' in ln]
    if not lines:
        return frozenset()
    # k≥3: each line encodes all parts; aggregate columns across lines
    first_line = lines[0]
    n_parts = first_line.count('||') + 1
    if n_parts >= 3 or len(lines) == 1:
        # Represent each column (part) as union of nodes across all lines
        result = []
        for ln in lines:
            cols = [c.strip().strip('|').strip() for c in ln.split('||')]
            for i, col in enumerate(cols):
                nodes = frozenset(e.strip().lower() for e in col.split(',') if e.strip() and e.strip() != '∅')
                if i < len(result):
                    result[i] = result[i] | nodes
                else:
                    result.append(nodes)
        return frozenset(result)
    # Bipartition (2 parts, 2 lines)
    if len(lines) < 2:
        return frozenset()

    def _parse_row(line):
        clean = line.strip('|').strip()
        halves = clean.split('||')
        if len(halves) != 2:
            return None, None
        left = frozenset(e.strip().lower() for e in halves[0].split(',') if e.strip() and e.strip() != '∅')
        right = frozenset(e.strip().lower() for e in halves[1].split(',') if e.strip() and e.strip() != '∅')
        return left, right

    purv_l, purv_r = _parse_row(lines[0])
    mech_l, mech_r = _parse_row(lines[1])
    if purv_l is None or mech_l is None:
        return frozenset()
    return frozenset({frozenset({purv_l, mech_l}), frozenset({purv_r, mech_r})})


def agregar_reporte(
    records: list[RunRecord],
    strategy_name: str,
    n_nodes: int,
    tpm_page: str,
    estado_inicial: str,
    reference_name: str = "pyphi",
) -> BenchmarkReport:
    """Aggregate a list of RunRecords into a BenchmarkReport.

    Args:
        records: All run records for one benchmark run.
        strategy_name: Name of the algorithm under test.
        n_nodes: Number of nodes.
        tpm_page: Network page letter (e.g. "A").
        estado_inicial: Initial state binary string.
        reference_name: Name of the reference oracle ("pyphi" or "bruteforce").

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
        reference_name=reference_name,
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
