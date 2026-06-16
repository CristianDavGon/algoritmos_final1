"""Punto de entrada para KQNodes (k-particiones submodular).

Configura el estado, k y criterio a ejecutar; luego::

    cd code/QNodes
    uv run exec_kqnodes.py

Para el estado dado, lee la hoja del Excel de pruebas y ejecuta KQNodes
sobre TODAS las filas (alcance × mecanismo) con el k y criterio indicados.
Los resultados se guardan en
``results/kqnodes/resultado__N{n}_{MUESTRA}_{K}.csv``.
"""

from __future__ import annotations

from src.main_kqnodes import iniciar_kqnodes
from src.models.base.application import aplicacion

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:   str = "1" + "0" * 19
K:        int = 5
CRITERIO: str = "C4"   # "C4" = corte marginal mínimo, "C1" = tamaño máximo
MUESTRA:  str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Configura el singleton de aplicación e inicia KQNodes."""
    aplicacion.desactivar_profiling()
    aplicacion.set_pagina_red_muestra(MUESTRA)

    iniciar_kqnodes(
        estado=ESTADO,
        k=K,
        criterio=CRITERIO,
    )


if __name__ == "__main__":
    main()
