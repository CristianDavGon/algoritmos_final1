"""Punto de entrada para QNodes (bipartición submodular).

Configura el estado de inicio y la muestra de red; luego ejecuta::

    cd code/QNodes
    uv run exec.py

Lee la hoja del Excel de pruebas correspondiente al n del estado y ejecuta
QNodes sobre TODAS las filas (alcance × mecanismo).
Los resultados se guardan en ``results/qnodes/resultado__N{n}_{MUESTRA}.csv``.
"""

from __future__ import annotations

from src.main import iniciar
from src.models.base.application import aplicacion

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:  str = "1" + "0" * 19
MUESTRA: str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Configura el singleton de aplicación e inicia QNodes."""
    aplicacion.desactivar_profiling()
    aplicacion.set_pagina_red_muestra(MUESTRA)

    iniciar(estado=ESTADO)


if __name__ == "__main__":
    main()
