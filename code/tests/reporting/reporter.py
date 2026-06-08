from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from tests.core.models import BenchmarkReport, RunRecord

_RESULTS_ROOT = Path(__file__).parent.parent / "results"

_STRATEGY_SUBDIR: dict[str, str] = {
    "qnodes": "qnodes",
    "geometric": "geomip",
}


def _results_dir(strategy_name: str, reference_name: str = "pyphi") -> Path:
    name_lower = strategy_name.lower()
    if name_lower.startswith("kgeomip"):
        subdir = "kgeomip"
    else:
        subdir = _STRATEGY_SUBDIR.get(name_lower, name_lower)
    return _RESULTS_ROOT / subdir / f"vs_{reference_name.lower()}"


def _sanitize_name(name: str) -> str:
    return re.sub(r"[^\w]+", "_", name.lower()).strip("_")


def _base_stem(report: BenchmarkReport) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    estado = report.estado_inicial
    page = report.tpm_page
    ref = report.reference_name.lower()
    return (
        f"N{report.n_nodes}{page}"
        f"_estado{estado}"
        f"_sample{page}"
        f"_{_sanitize_name(report.strategy_name)}_vs_{ref}_{date_str}"
    )


def guardar_csv(report: BenchmarkReport) -> Path:
    """Write benchmark results to a dated CSV file in tests/results/<algo>/vs_<ref>/."""
    out_dir = _results_dir(report.strategy_name, report.reference_name)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_base_stem(report)}.csv"
    fieldnames = [
        "Prueba", "Alcance", "Mecanismo",
        "phi_Pyphi", "phi_Candidato", "delta_phi", "error_relativo_pct", "phi_match",
        "particion_Pyphi", "particion_Candidato", "particion_match",
        "t_Pyphi_s", "t_Candidato_s", "speedup",
        "desde_cache", "error_Pyphi", "error_Candidato",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in report.records:
            writer.writerow({
                "Prueba": r.test_case.index,
                "Alcance": r.test_case.alcance_letras,
                "Mecanismo": r.test_case.mecanismo_letras,
                "phi_Pyphi": r.referencia.perdida if not r.referencia.error else "ERROR",
                "phi_Candidato": r.candidato.perdida if not r.candidato.error else "ERROR",
                "delta_phi": f"{r.phi_delta:.6f}" if r.phi_delta is not None else "",
                "error_relativo_pct": f"{r.phi_relative_error_pct:.2f}" if r.phi_relative_error_pct is not None else "N/A",
                "phi_match": r.phi_match,
                "particion_Pyphi": (r.referencia.particion or "").replace("\n", " | "),
                "particion_Candidato": (r.candidato.particion or "").replace("\n", " | "),
                "particion_match": r.partition_match,
                "t_Pyphi_s": f"{r.referencia.tiempo:.4f}" if r.referencia.tiempo else "",
                "t_Candidato_s": f"{r.candidato.tiempo:.4f}" if r.candidato.tiempo else "",
                "speedup": f"{r.speedup:.2f}" if r.speedup is not None else "",
                "desde_cache": r.from_cache,
                "error_Pyphi": r.referencia.error or "",
                "error_Candidato": r.candidato.error or "",
            })
    return path


def guardar_markdown(report: BenchmarkReport) -> Path:
    """Write a detailed per-case Markdown comparison report in tests/results/<algo>/vs_<ref>/."""
    out_dir = _results_dir(report.strategy_name, report.reference_name)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_base_stem(report)}.md"

    red = f"N{report.n_nodes}{report.tpm_page}"
    ref_label = report.reference_name.upper()
    lines: list[str] = []

    # ── Encabezado ──────────────────────────────────────────────────────────
    lines += [
        f"# Comparación {report.strategy_name} vs {ref_label} — Red {red}",
        f"",
        f"Estado inicial: `{report.estado_inicial}`  |  "
        f"Tolerancia φ: `1e-4`  |  "
        f"Fecha: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`",
        f"",
    ]

    # ── Resumen ejecutivo ────────────────────────────────────────────────────
    avg_s = report.avg_speedup
    avg_d = report.avg_delta_phi
    max_d = report.max_delta_phi
    lines += [
        f"## Resumen ejecutivo",
        f"",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Exactitud φ | {report.phi_matches}/{report.total_tests} ({report.phi_accuracy_pct:.1f}%) |",
        f"| Exactitud partición | {report.partition_matches}/{report.total_tests} ({report.partition_accuracy_pct:.1f}%) |",
        f"| Speedup promedio | {f'{avg_s:.2f}x' if avg_s is not None else 'N/A'} |",
        f"| Δφ promedio | {f'{avg_d:.6f}' if avg_d is not None else 'N/A'} |",
        f"| Δφ máximo | {f'{max_d:.6f}' if max_d is not None else 'N/A'} |",
        f"",
    ]

    # ── Tabla resumen por caso ───────────────────────────────────────────────
    lines += [
        f"## Tabla comparativa",
        f"",
        f"| # | Alcance | Mec. | φ {ref_label} | φ {report.strategy_name} | Δφ | Error% | φ✓ | Part✓ |",
        f"|---|---------|------|---------|------------|-----|--------|-----|-------|",
    ]
    for r in report.records:
        phi_ref = f"{r.referencia.perdida:.4f}" if not r.referencia.error else "ERR"
        phi_cand = f"{r.candidato.perdida:.4f}" if not r.candidato.error else "ERR"
        delta = f"{r.phi_delta:.4f}" if r.phi_delta is not None else "-"
        err_pct = f"{r.phi_relative_error_pct:.1f}%" if r.phi_relative_error_pct is not None else "N/A"
        phi_ok = "✓" if r.phi_match else "✗"
        part_ok = "✓" if r.partition_match else "✗"
        lines.append(
            f"| {r.test_case.index} | {r.test_case.alcance_letras} | {r.test_case.mecanismo_letras} "
            f"| {phi_ref} | {phi_cand} | {delta} | {err_pct} | {phi_ok} | {part_ok} |"
        )
    lines.append("")

    # ── Detalle por caso ─────────────────────────────────────────────────────
    lines += ["## Detalle por caso", ""]
    for r in report.records:
        _append_case_detail(lines, r, report.strategy_name, ref_label)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _append_case_detail(
    lines: list[str], r: RunRecord, strategy_name: str, ref_label: str = "PYPHI"
) -> None:
    """Append the detailed comparison block for one RunRecord."""
    tc = r.test_case
    phi_ok = "COINCIDE" if r.phi_match else "DIFIERE"
    part_ok = "COINCIDE" if r.partition_match else "DIFIERE"

    lines.append(f"### Caso #{tc.index} — Alcance: `{tc.alcance_letras}` | Mecanismo: `{tc.mecanismo_letras}`")
    lines.append("")

    if r.referencia.error or r.candidato.error:
        lines.append(f"> ERROR — {ref_label}: `{r.referencia.error}` | {strategy_name}: `{r.candidato.error}`")
        lines.append("")
        return

    phi_ref = r.referencia.perdida
    phi_cand = r.candidato.perdida
    delta = r.phi_delta
    err_pct = r.phi_relative_error_pct

    err_str = f"{err_pct:.2f}%" if err_pct is not None else "N/A (φ=0)"
    lines += [
        f"**φ (pérdida)**",
        f"",
        f"| | {ref_label} | {strategy_name} | Diferencia |",
        f"|--|-------|--------|------------|",
        f"| φ | `{phi_ref:.6f}` | `{phi_cand:.6f}` | Δ=`{delta:.6f}` ({err_str}) — **{phi_ok}** |",
        f"",
    ]

    lines.append(f"**Partición** — {part_ok}")
    lines.append("")

    part_ref = r.referencia.particion or ""
    part_cand = r.candidato.particion or ""

    if r.partition_match:
        lines += [
            "```",
            part_ref.strip(),
            "```",
            "",
        ]
    else:
        lines += [
            f"<details><summary>Ver particiones (diferentes)</summary>",
            f"",
            f"**{ref_label}:**",
            "```",
            part_ref.strip(),
            "```",
            f"",
            f"**{strategy_name}:**",
            "```",
            part_cand.strip(),
            "```",
            f"",
            f"</details>",
            "",
        ]

    lines.append("---")
    lines.append("")


def imprimir_resumen(report: BenchmarkReport) -> None:
    """Print a formatted summary table to stdout."""
    w = 66
    red = f"N{report.n_nodes}{report.tpm_page}"
    ref_label = report.reference_name.upper()
    print(f"\n{'=' * w}")
    print(f"  RESUMEN  {report.strategy_name} vs {ref_label}  |  Red: {red}  |  {report.total_tests} pruebas")
    print(f"{'=' * w}")
    print(f"  Exactitud phi         : {report.phi_matches}/{report.total_tests}  ({report.phi_accuracy_pct:.1f}%)")
    print(f"  Exactitud particion   : {report.partition_matches}/{report.total_tests}  ({report.partition_accuracy_pct:.1f}%)")
    avg_s = report.avg_speedup
    print(f"  Speedup promedio      : {f'{avg_s:.2f}x' if avg_s is not None else 'N/A'}")
    avg_d = report.avg_delta_phi
    print(f"  Delta-phi promedio    : {f'{avg_d:.6f}' if avg_d is not None else 'N/A'}")
    max_d = report.max_delta_phi
    print(f"  Delta-phi maximo      : {f'{max_d:.6f}' if max_d is not None else 'N/A'}")
    print(f"{'=' * w}\n")
