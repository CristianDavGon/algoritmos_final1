"""
Genera 5 figuras para §2.7.5 del Manual Técnico K-QGMIP.
Sin dependencias externas — solo Python estándar.

Figuras:
  fig_scatter_calidad_velocidad.png  — Bubble: phi_avg vs t_avg (18 configs)
  fig_escalabilidad_tiempo.png       — Líneas: t_avg vs n con múltiples k
  fig_delta_phi_incremental.png      — Barras: DeltaPhi por paso de partición
  fig_tiempo_total_experimentos.png  — Barras horiz.: t_total de los 18 experimentos
  fig_efecto_muestra_red.png         — Barras: efecto de muestra A vs B (n=15)

Uso:
  python generar_graficas_manual.py
  Abre cada .html en el navegador → clic "Descargar PNG" → mueve PNG a figures/
"""

import json
import pathlib

FIGURES_DIR = pathlib.Path(__file__).parent / "docs" / "manual_tecnico" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{
      background: white;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
      font-family: Arial, sans-serif;
    }}
    canvas {{ background: white; }}
    button {{
      margin-top: 14px;
      padding: 10px 26px;
      font-size: 14px;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
    }}
    button:hover {{ background: #1d4ed8; }}
    p {{ color: #666; font-size: 12px; margin: 4px; }}
  </style>
</head>
<body>
  <canvas id="chart" width="{width}" height="{height}"></canvas>
  <button onclick="dl()">&#11015; Descargar PNG &rarr; {filename}</button>
  <p>Mover el PNG descargado a <code>docs/manual_tecnico/figures/</code></p>
  <script>
    const ctx = document.getElementById('chart');
    new Chart(ctx, {config});
    function dl() {{
      const a = document.createElement('a');
      a.href = ctx.toDataURL('image/png');
      a.download = '{filename}';
      a.click();
    }}
  </script>
</body>
</html>"""


def escribir_html(config_str: str, filename: str, title: str,
                  width: int = 860, height: int = 500):
    html = TEMPLATE.format(
        title=title, width=width, height=height,
        config=config_str, filename=filename,
    )
    out = FIGURES_DIR / filename.replace(".png", ".html")
    out.write_text(html, encoding="utf-8")
    print(f"OK  {out.name}")


def j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Paleta de colores
# ─────────────────────────────────────────────────────────────────────────────
BLUE_F  = "rgba(37,99,235,0.65)"
BLUE_B  = "rgba(37,99,235,1.0)"
ORG_F   = "rgba(234,88,12,0.65)"
ORG_B   = "rgba(234,88,12,1.0)"
GREEN_F = "rgba(22,163,74,0.65)"
GREEN_B = "rgba(22,163,74,1.0)"
PUR_F   = "rgba(147,51,234,0.65)"
PUR_B   = "rgba(147,51,234,1.0)"


# =============================================================================
# Fig 1 — Bubble: Calidad (phi_avg) vs Velocidad (t_avg)  —  18 experimentos
# =============================================================================
# Tamaño de burbuja (r): k=3→6, k=4→10, k=5→14  (visible en leyenda del título)

kq = [
    {"x": 0.0038, "y": 1.7959, "r":14, "label": "N8  A k=5"},
    {"x": 0.0055, "y": 1.4647, "r": 6, "label": "N10 A k=3"},
    {"x": 0.0061, "y": 1.5185, "r":10, "label": "N10 A k=4"},
    {"x": 0.0068, "y": 1.5444, "r":14, "label": "N10 A k=5"},
    {"x": 0.0278, "y": 0.1458, "r": 6, "label": "N15 A k=3"},
    {"x": 0.0305, "y": 0.1760, "r":10, "label": "N15 A k=4"},
    {"x": 0.0578, "y": 0.2029, "r":14, "label": "N15 A k=5"},
    {"x": 0.0264, "y": 0.0129, "r": 6, "label": "N15 B k=3"},
    {"x": 0.0301, "y": 0.0156, "r":10, "label": "N15 B k=4"},
    {"x": 0.0627, "y": 0.0180, "r":14, "label": "N15 B k=5"},
    {"x": 1.4985, "y": 2.6611, "r":10, "label": "N20 A k=4"},
    {"x": 3.1746, "y": 2.6467, "r":14, "label": "N20 A k=5"},
]
kg = [
    {"x": 0.0252, "y": 1.0156, "r": 6, "label": "N10 A k=3"},
    {"x": 0.4556, "y": 0.0074, "r": 6, "label": "N15 B k=3"},
    {"x": 0.7986, "y": 0.0105, "r":10, "label": "N15 B k=4"},
    {"x": 0.4633, "y": 0.0138, "r":14, "label": "N15 B k=5"},
    {"x": 6.1883, "y": 2.2177, "r": 6, "label": "N20 A k=3"},
    {"x": 3.4927, "y": 2.3926, "r":10, "label": "N20 A k=4"},
]

fig1 = {
    "type": "bubble",
    "data": {
        "datasets": [
            {"label": "KQNodes C4", "data": kq,
             "backgroundColor": BLUE_F, "borderColor": BLUE_B, "borderWidth": 1.5},
            {"label": "KGeoMIP E4", "data": kg,
             "backgroundColor": ORG_F,  "borderColor": ORG_B,  "borderWidth": 1.5},
        ]
    },
    "options": {
        "animation": {"duration": 0},
        "plugins": {
            "title": {
                "display": True,
                "text": [
                    "K-QGMIP — Trade-off: Calidad (phi) vs Velocidad (t_avg)",
                    "Tamano de burbuja = k  (pequeno=k3, mediano=k4, grande=k5)"
                ],
                "font": {"size": 13, "weight": "bold"},
            },
            "legend": {"position": "top"},
            "tooltip": {"callbacks": {"label": "TOOLTIP_FN"}},
        },
        "scales": {
            "x": {
                "type": "logarithmic",
                "title": {"display": True, "text": "Tiempo promedio por caso (s) — escala log"},
                "ticks": {"callback": "TICK_X"},
            },
            "y": {
                "beginAtZero": True,
                "title": {"display": True, "text": "phi promedio (EMD-Effect)"},
            },
        },
    },
}

fig1_str = (
    j(fig1)
    .replace('"TOOLTIP_FN"',
             'function(c){var d=c.raw;'
             'return (d.label||"")+": phi="+d.y.toFixed(4)+", t="+d.x.toFixed(4)+"s";}')
    .replace('"TICK_X"',
             'function(v){return v>=1?v.toFixed(1)+"s"'
             ':v>=0.01?(v*1000).toFixed(0)+"ms":v.toFixed(4)+"s";}')
)
escribir_html(fig1_str, "fig_scatter_calidad_velocidad.png",
              "Fig 1 — Calidad vs Velocidad", 880, 540)


# =============================================================================
# Fig 2 — Líneas: t_avg vs n  (múltiples k, escala log y)
# =============================================================================
fig2 = {
    "type": "line",
    "data": {
        "labels": ["n=8", "n=10", "n=15", "n=20"],
        "datasets": [
            {
                "label": "KQNodes A  k=5",
                "data": [0.0038, 0.0068, 0.0578, 3.1746],
                "borderColor": BLUE_B, "backgroundColor": "rgba(37,99,235,0.08)",
                "pointRadius": 7, "pointBackgroundColor": BLUE_B,
                "tension": 0.2, "fill": True,
            },
            {
                "label": "KQNodes A  k=4",
                "data": [None, 0.0061, 0.0305, 1.4985],
                "borderColor": GREEN_B, "backgroundColor": "transparent",
                "pointRadius": 7, "pointBackgroundColor": GREEN_B,
                "tension": 0.2, "borderDash": [6, 3],
            },
            {
                "label": "KQNodes A  k=3",
                "data": [None, 0.0055, 0.0278, None],
                "borderColor": PUR_B, "backgroundColor": "transparent",
                "pointRadius": 7, "pointBackgroundColor": PUR_B,
                "tension": 0.2, "borderDash": [3, 3],
            },
            {
                "label": "KGeoMIP A  k=3",
                "data": [None, 0.0252, None, 6.1883],
                "borderColor": ORG_B, "backgroundColor": "transparent",
                "pointRadius": 7, "pointBackgroundColor": ORG_B,
                "tension": 0.2, "borderDash": [8, 4],
            },
        ],
    },
    "options": {
        "animation": {"duration": 0},
        "spanGaps": False,
        "plugins": {
            "title": {
                "display": True,
                "text": "K-QGMIP — Escalabilidad: t_avg vs n (escala log)",
                "font": {"size": 14, "weight": "bold"},
            },
            "legend": {"position": "top"},
        },
        "scales": {
            "y": {
                "type": "logarithmic",
                "title": {"display": True, "text": "Tiempo promedio (s) — escala log"},
                "ticks": {"callback": "TICK_Y"},
            },
            "x": {"title": {"display": True, "text": "Tamanio de red n"}},
        },
    },
}

fig2_str = j(fig2).replace(
    '"TICK_Y"',
    'function(v){return v>=1?v.toFixed(2)+"s":v>=0.001?(v*1000).toFixed(1)+"ms":(v*1000).toFixed(2)+"ms";}',
)
escribir_html(fig2_str, "fig_escalabilidad_tiempo.png",
              "Fig 2 — Escalabilidad temporal", 880, 500)


# =============================================================================
# Fig 3 — Barras agrupadas: ΔΦ incremental por paso de k
# =============================================================================
fig3 = {
    "type": "bar",
    "data": {
        "labels": ["KQNodes\nN10 A", "KQNodes\nN15 A",
                   "KQNodes\nN15 B", "KGeoMIP\nN15 B"],
        "datasets": [
            {
                "label": "DeltaPhi (k=3 a k=4)",
                "data": [
                    round(1.5185 - 1.4647, 4),   # KQNodes N10 A
                    round(0.1760 - 0.1458, 4),   # KQNodes N15 A
                    round(0.0156 - 0.0129, 4),   # KQNodes N15 B
                    round(0.0105 - 0.0074, 4),   # KGeoMIP N15 B
                ],
                "backgroundColor": "rgba(37,99,235,0.75)",
                "borderColor": BLUE_B, "borderWidth": 1.5,
            },
            {
                "label": "DeltaPhi (k=4 a k=5)",
                "data": [
                    round(1.5444 - 1.5185, 4),   # KQNodes N10 A
                    round(0.2029 - 0.1760, 4),   # KQNodes N15 A
                    round(0.0180 - 0.0156, 4),   # KQNodes N15 B
                    round(0.0138 - 0.0105, 4),   # KGeoMIP N15 B
                ],
                "backgroundColor": "rgba(234,88,12,0.75)",
                "borderColor": ORG_B, "borderWidth": 1.5,
            },
        ],
    },
    "options": {
        "animation": {"duration": 0},
        "plugins": {
            "title": {
                "display": True,
                "text": [
                    "K-QGMIP — Ganancia de informacion por particion adicional",
                    "DeltaPhi = phi(k+1) - phi(k)  (rendimientos decrecientes)"
                ],
                "font": {"size": 13, "weight": "bold"},
            },
            "legend": {"position": "top"},
        },
        "scales": {
            "y": {
                "beginAtZero": True,
                "title": {"display": True, "text": "DeltaPhi = phi(k+1) - phi(k)"},
            },
            "x": {"title": {"display": True, "text": "Configuracion"}},
        },
    },
}
escribir_html(j(fig3), "fig_delta_phi_incremental.png",
              "Fig 3 — DeltaPhi incremental", 820, 480)


# =============================================================================
# Fig 4 — Barras horizontales: tiempo TOTAL del experimento (50 casos)
# =============================================================================
# Ordenadas de menor a mayor t_total
entries = sorted([
    ("KQNodes  N8  A  k5",   0.1869,  BLUE_F, BLUE_B),
    ("KQNodes  N10 A  k3",   0.2685,  BLUE_F, BLUE_B),
    ("KQNodes  N10 A  k4",   0.2977,  BLUE_F, BLUE_B),
    ("KQNodes  N10 A  k5",   0.3353,  BLUE_F, BLUE_B),
    ("KGeoMIP  N10 A  k3",   1.2359,  ORG_F,  ORG_B),
    ("KQNodes  N15 B  k3",   1.3185,  BLUE_F, BLUE_B),
    ("KQNodes  N15 A  k3",   1.3918,  BLUE_F, BLUE_B),
    ("KQNodes  N15 B  k4",   1.5074,  BLUE_F, BLUE_B),
    ("KQNodes  N15 A  k4",   1.5263,  BLUE_F, BLUE_B),
    ("KQNodes  N15 A  k5",   2.8903,  BLUE_F, BLUE_B),
    ("KQNodes  N15 B  k5",   3.1372,  BLUE_F, BLUE_B),
    ("KGeoMIP  N15 B  k3",  22.7784,  ORG_F,  ORG_B),
    ("KGeoMIP  N15 B  k5",  23.1665,  ORG_F,  ORG_B),
    ("KGeoMIP  N15 B  k4",  39.9315,  ORG_F,  ORG_B),
    ("KQNodes  N20 A  k4",  74.9265,  BLUE_F, BLUE_B),
    ("KQNodes  N20 A  k5", 158.7319,  BLUE_F, BLUE_B),
    ("KGeoMIP  N20 A  k4", 174.6360,  ORG_F,  ORG_B),
    ("KGeoMIP  N20 A  k3", 309.4142,  ORG_F,  ORG_B),
], key=lambda e: e[1])

fig4 = {
    "type": "bar",
    "data": {
        "labels": [e[0] for e in entries],
        "datasets": [{
            "data":            [e[1] for e in entries],
            "backgroundColor": [e[2] for e in entries],
            "borderColor":     [e[3] for e in entries],
            "borderWidth": 1,
        }],
    },
    "options": {
        "indexAxis": "y",
        "animation": {"duration": 0},
        "plugins": {
            "title": {
                "display": True,
                "text": [
                    "K-QGMIP — Tiempo total del experimento (~50 casos por config)",
                    "Azul = KQNodes C4  |  Naranja = KGeoMIP E4"
                ],
                "font": {"size": 13, "weight": "bold"},
            },
            "legend": {"display": False},
            "tooltip": {"callbacks": {"label": "TICK_TT"}},
        },
        "scales": {
            "x": {
                "type": "logarithmic",
                "title": {"display": True, "text": "Tiempo total (s) — escala log"},
                "ticks": {"callback": "TICK_TX"},
            },
            "y": {"ticks": {"font": {"size": 10}}},
        },
    },
}

fig4_str = (
    j(fig4)
    .replace('"TICK_TT"',
             'function(c){return c.dataset.data[c.dataIndex].toFixed(2)+" s total";}')
    .replace('"TICK_TX"',
             'function(v){return v>=60?Math.round(v/60)+"min":v>=1?v.toFixed(1)+"s":(v*1000).toFixed(0)+"ms";}')
)
escribir_html(fig4_str, "fig_tiempo_total_experimentos.png",
              "Fig 4 — Tiempo total por experimento", 920, 660)


# =============================================================================
# Fig 5 — Barras agrupadas: efecto de la muestra de red  (n=15, k=3,4,5)
# =============================================================================
fig5 = {
    "type": "bar",
    "data": {
        "labels": ["k=3", "k=4", "k=5"],
        "datasets": [
            {
                "label": "KQNodes C4  n=15 Muestra A",
                "data": [0.1458, 0.1760, 0.2029],
                "backgroundColor": "rgba(37,99,235,0.75)",
                "borderColor": BLUE_B, "borderWidth": 1.5,
            },
            {
                "label": "KQNodes C4  n=15 Muestra B",
                "data": [0.0129, 0.0156, 0.0180],
                "backgroundColor": "rgba(37,99,235,0.30)",
                "borderColor": BLUE_B, "borderWidth": 1.5,
                "borderDash": [4, 2],
            },
            {
                "label": "KGeoMIP E4  n=15 Muestra B",
                "data": [0.0074, 0.0105, 0.0138],
                "backgroundColor": "rgba(234,88,12,0.70)",
                "borderColor": ORG_B, "borderWidth": 1.5,
            },
        ],
    },
    "options": {
        "animation": {"duration": 0},
        "plugins": {
            "title": {
                "display": True,
                "text": [
                    "K-QGMIP — Efecto de la muestra de red sobre phi (n=15)",
                    "Muestra A vs B: diferencia de ~11x independiente de k"
                ],
                "font": {"size": 13, "weight": "bold"},
            },
            "legend": {"position": "top"},
        },
        "scales": {
            "y": {
                "beginAtZero": True,
                "title": {"display": True, "text": "phi promedio (EMD-Effect)"},
            },
            "x": {"title": {"display": True, "text": "Numero de particiones k"}},
        },
    },
}
escribir_html(j(fig5), "fig_efecto_muestra_red.png",
              "Fig 5 — Efecto de la muestra de red", 820, 500)


# ─────────────────────────────────────────────────────────────────────────────
print()
print("Generados 5 archivos HTML en:")
print(f"  {FIGURES_DIR}")
print()
print("Abrir en navegador y descargar PNG:")
print("  fig_scatter_calidad_velocidad.png   <- NUEVO")
print("  fig_escalabilidad_tiempo.png        <- ACTUALIZADO")
print("  fig_delta_phi_incremental.png       <- NUEVO")
print("  fig_tiempo_total_experimentos.png   <- NUEVO")
print("  fig_efecto_muestra_red.png          <- NUEVO")
