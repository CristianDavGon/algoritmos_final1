from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def guardar_markdown(
    resultados: list[dict],
    ruta_md: Path,
    algoritmo: str,
    estado_inicio: str,
) -> Path:
    """Genera un reporte Markdown amigable al lado del CSV de resultados.

    Args:
        resultados: Lista de dicts usada para el CSV.
                    Claves base: Prueba, Alcance, Mecanismo, Partición, Pérdida (φ), Tiempo (s)
                    Claves KGeoMIP: también k, Criterio
        ruta_md: Ruta de salida del archivo .md.
        algoritmo: Nombre del algoritmo (ej. "GeoMIP", "KGeoMIP").
        estado_inicio: String binario del estado inicial.

    Returns:
        Ruta al archivo .md creado.
    """
    n = len(estado_inicio)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    es_kgeomip = bool(resultados) and "k" in resultados[0]

    validos = [r for r in resultados if r.get("Pérdida (φ)") is not None]
    con_error = len(resultados) - len(validos)
    perdidas = [r["Pérdida (φ)"] for r in validos]
    tiempos = [r["Tiempo (s)"] for r in validos if r.get("Tiempo (s)") is not None]

    avg_phi = sum(perdidas) / len(perdidas) if perdidas else None
    max_phi = max(perdidas) if perdidas else None
    min_phi = min(perdidas) if perdidas else None
    avg_t = sum(tiempos) / len(tiempos) if tiempos else None
    total_t = sum(tiempos) if tiempos else None

    lines: list[str] = []

    # ── Encabezado ──────────────────────────────────────────────────────────
    lines += [
        f"# Resultados {algoritmo} — N{n}",
        f"",
        f"Estado inicial: `{estado_inicio}`  |  Fecha: `{fecha}`",
        f"",
    ]

    # ── Resumen ejecutivo ────────────────────────────────────────────────────
    lines += [
        f"## Resumen ejecutivo",
        f"",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Total pruebas | {len(resultados)} |",
    ]
    if con_error > 0:
        lines.append(f"| Pruebas con error | {con_error} |")
    lines += [
        f"| Pérdida φ promedio | {f'{avg_phi:.6f}' if avg_phi is not None else 'N/A'} |",
        f"| Pérdida φ máxima   | {f'{max_phi:.6f}' if max_phi is not None else 'N/A'} |",
        f"| Pérdida φ mínima   | {f'{min_phi:.6f}' if min_phi is not None else 'N/A'} |",
        f"| Tiempo promedio    | {f'{avg_t:.4f} s' if avg_t is not None else 'N/A'} |",
        f"| Tiempo total       | {f'{total_t:.4f} s' if total_t is not None else 'N/A'} |",
        f"",
    ]

    # ── Tabla de resultados ──────────────────────────────────────────────────
    lines += [f"## Tabla de resultados", f""]
    if es_kgeomip:
        lines += [
            f"| # | Alcance | Mecanismo | k | Criterio | Pérdida (φ) | Tiempo (s) |",
            f"|---|---------|-----------|---|----------|-------------|------------|",
        ]
        for r in resultados:
            phi = f"{r['Pérdida (φ)']:.6f}" if r.get("Pérdida (φ)") is not None else "ERROR"
            t = f"{r['Tiempo (s)']:.4f}" if r.get("Tiempo (s)") is not None else "-"
            lines.append(
                f"| {r['Prueba']} | {r['Alcance']} | {r['Mecanismo']} "
                f"| {r.get('k', '-')} | {r.get('Criterio', '-')} "
                f"| {phi} | {t} |"
            )
    else:
        lines += [
            f"| # | Alcance | Mecanismo | Pérdida (φ) | Tiempo (s) |",
            f"|---|---------|-----------|-------------|------------|",
        ]
        for r in resultados:
            phi = f"{r['Pérdida (φ)']:.6f}" if r.get("Pérdida (φ)") is not None else "ERROR"
            t = f"{r['Tiempo (s)']:.4f}" if r.get("Tiempo (s)") is not None else "-"
            lines.append(
                f"| {r['Prueba']} | {r['Alcance']} | {r['Mecanismo']} | {phi} | {t} |"
            )
    lines.append("")

    # ── Detalle por caso ─────────────────────────────────────────────────────
    lines += [f"## Detalle por caso", f""]
    for r in resultados:
        _append_caso(lines, r, es_kgeomip)

    ruta_md.parent.mkdir(parents=True, exist_ok=True)
    ruta_md.write_text("\n".join(lines), encoding="utf-8")
    return ruta_md


def fmt_particion_amigable(particion: str | None) -> str:
    """Convierte cualquier string de partición al formato compacto (A,∅) | (B,∅) | ...

    Soporta:
    - GeoMIP/QNodes bipartición:  ⎛P0⎞⎛P1⎞\\n⎝M0⎠⎝M1⎠
    - KGeoMIP/KQNodes k-partición: múltiples biparticiones unidas con ' | '

    Las letras del mecanismo (minúsculas) se convierten a mayúsculas.
    """
    if not particion:
        return "(sin partición)"
    s = str(particion).strip()

    if "⎛" in s:
        return _parse_fmt_curvo(s)
    return s


def _norm(x: str) -> str:
    stripped = x.strip()
    return stripped if stripped else "∅"


def _parse_fmt_curvo(s: str) -> str:
    """Parsea el formato ⎛...⎞⎛...⎞\\n⎝...⎠⎝...⎠ (GeoMIP, QNodes y sus variantes k)."""
    tops = [_norm(m) for m in re.findall(r"⎛(.*?)⎞", s)]
    bots = [_norm(m.upper()) for m in re.findall(r"⎝(.*?)⎠", s)]

    n = len(tops)
    if n == 0:
        return s

    # Bipartición estándar (2 columnas): step=1
    # k-partición (2k columnas, 2 por parte): step=2
    step = 1 if n == 2 else 2
    parts = [
        f"({tops[i]},{bots[i]})"
        for i in range(0, n, step)
    ]
    return " | ".join(parts)


def _append_caso(lines: list[str], r: dict, es_kgeomip: bool = False) -> None:
    prueba = r["Prueba"]
    alcance = r["Alcance"]
    mecanismo = r["Mecanismo"]

    if es_kgeomip:
        lines.append(
            f"### Caso #{prueba} — Alcance: `{alcance}` | Mecanismo: `{mecanismo}`"
            f" | k={r.get('k', '?')} | Criterio: {r.get('Criterio', '?')}"
        )
    else:
        lines.append(f"### Caso #{prueba} — Alcance: `{alcance}` | Mecanismo: `{mecanismo}`")
    lines.append("")

    phi = r.get("Pérdida (φ)")
    tiempo = r.get("Tiempo (s)")
    particion = r.get("Partición")

    if phi is None:
        lines += ["> **ERROR** — No se pudo calcular el resultado.", "", "---", ""]
        return

    lines += [
        f"**Pérdida (φ):** `{phi:.6f}`  |  **Tiempo:** `{tiempo:.4f} s`",
        f"",
        f"**Partición:** {fmt_particion_amigable(particion)}",
        f"",
        f"---",
        f"",
    ]
