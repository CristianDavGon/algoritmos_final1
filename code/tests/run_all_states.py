"""Run QNodes and GeoMIP benchmarks across all valid initial states.

Each (algo, reference, estado, pagina) combination is executed in its own
subprocess so that QNodes and GeoMIP never share the same Python process
(avoids src.* import shadowing).

Usage (from the code/ directory):
    python tests/run_all_states.py                        # all combos
    python tests/run_all_states.py --algo qnodes          # only QNodes
    python tests/run_all_states.py --algo geomip          # only GeoMIP
    python tests/run_all_states.py --reference pyphi       # only vs PyPhi
    python tests/run_all_states.py --reference bruteforce  # only vs BruteForce
    python tests/run_all_states.py --n-tests 5            # limit cases per run
    python tests/run_all_states.py --dry-run              # print commands only

Reference matrix:
    pyphi      — all networks (N5A, N5B, N8A, N10A)
    bruteforce — only N <= 6  (N5A, N5B)

Valid states per network are taken from code/tests/estados_validos.md.
N8A and N10A use the representative examples listed in that document.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ── Valid states per (N, page) — sourced from estados_validos.md ─────────────

VALID_STATES: dict[tuple[int, str], list[str]] = {
    # N5 page A — 8 of 32 reachable
    (5, "A"): [
        "00000", "00100", "10000", "10001",
        "10100", "10101", "11001", "11100",
    ],
    # N5 page B — 13 of 32 reachable
    (5, "B"): [
        "00000", "00010", "00100", "00110", "00111",
        "01010", "01100", "01110", "01111",
        "10110", "10111", "11010", "11110",
    ],
    # N8 page A — all 256 reachable; representatives by # of 1-bits
    (8, "A"): [
        "00000000",
        "10000000", "00000001",
        "11000000", "10000001", "00000011",
        "11100000", "10100001", "00000111",
        "11110000", "10101010", "00001111",
        "11111000", "10101011", "00011111",
        "11111100", "10110111", "00111111",
        "11111110", "01111111",
        "11111111",
    ],
    # N10 page A — 645 of 1024 reachable; representative examples per # of 1-bits
    (10, "A"): [
        "0000000000",
        "0000000001", "0000000100", "0000010000", "1000000000",
        "0000000101", "0000000110", "0000001100",
        "0000000111", "0000001011", "0000001101", "1010000001",
        "0000001111", "0000010111", "0000110101", "1010000101",
        "0000110111", "0001111001", "1010101101", "1111000001",
        "0001110111", "0110111111", "1010111101", "1111000011",
        "0101110111", "0111011011", "1011011111", "1110011111",
        "0110111111", "0111101111", "1010111111", "1110110111",
        "0111111111", "1111011111", "1111110111",
    ],
}

# BruteForce is viable up to N = 8 (exponential cost, avoid N > 8)
_BRUTEFORCE_MAX_N = 8

_ALGOS = ["qnodes", "geomip"]
_REFERENCES = ["pyphi", "bruteforce"]
_THIS_DIR = Path(__file__).resolve().parent
_CODE_ROOT = _THIS_DIR.parent
_RUNNER = _THIS_DIR / "core" / "run_benchmark.py"


def build_jobs(
    algos: list[str],
    references: list[str],
    n_tests: int | None,
) -> list[tuple[str, str, str, str, list[str]]]:
    """Return list of (algo, reference, estado, pagina, cmd) tuples.

    Order: all pyphi jobs first (all networks), then all bruteforce jobs
    (only N <= _BRUTEFORCE_MAX_N), so the heavier reference runs last.
    """
    jobs: list[tuple[str, str, str, str, list[str]]] = []

    for reference in references:  # pyphi before bruteforce
        for (n, pagina), estados in VALID_STATES.items():
            if reference == "bruteforce" and n > _BRUTEFORCE_MAX_N:
                continue
            for estado in estados:
                for algo in algos:
                    cmd = [
                        sys.executable,
                        str(_RUNNER),
                        "--algo", algo,
                        "--estado", estado,
                        "--pagina", pagina,
                        "--reference", reference,
                    ]
                    if n_tests is not None:
                        cmd += ["--n-tests", str(n_tests)]
                    jobs.append((algo, reference, estado, pagina, cmd))

    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all valid-state benchmarks")
    parser.add_argument("--algo", choices=_ALGOS,
                        help="Restrict to one algorithm (default: all)")
    parser.add_argument("--reference", choices=_REFERENCES,
                        help="Restrict to one reference oracle (default: both)")
    parser.add_argument("--n-tests", type=int, default=None,
                        help="Limit test cases per run (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing them")
    args = parser.parse_args()

    algos = [args.algo] if args.algo else _ALGOS
    references = [args.reference] if args.reference else _REFERENCES
    jobs = build_jobs(algos, references, args.n_tests)
    total = len(jobs)

    ref_label = args.reference or "pyphi+bruteforce"
    algo_label = args.algo or "+".join(_ALGOS)

    print(f"\n{'='*72}")
    print(f"  run_all_states — {total} combinaciones")
    print(f"  algos={algo_label}  reference={ref_label}  n_tests={args.n_tests or 'all'}")
    print(f"{'='*72}\n")

    failed: list[str] = []
    for idx, (algo, reference, estado, pagina, cmd) in enumerate(jobs, 1):
        label = (
            f"[{idx:>3}/{total}]  {algo:<8}  vs {reference:<10}"
            f"  N{len(estado)}{pagina}  estado={estado}"
        )
        if args.dry_run:
            print(f"  DRY  {label}")
            print(f"       {' '.join(cmd)}")
            continue

        print(f"  RUN  {label}")
        result = subprocess.run(cmd, cwd=str(_CODE_ROOT))
        if result.returncode != 0:
            failed.append(label)
            print(f"  !! FAILED (exit {result.returncode}): {label}\n")
        else:
            print()

    if args.dry_run:
        return

    print(f"\n{'='*72}")
    if failed:
        print(f"  COMPLETADO con {len(failed)} fallo(s):")
        for f in failed:
            print(f"    - {f}")
    else:
        print(f"  COMPLETADO — todas las {total} combinaciones exitosas")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
