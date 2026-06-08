"""Punto de entrada para QNodes (partición submodular).

Configura aquí el estado de inicio y la muestra; luego ejecuta:

    cd code/QNodes
    uv run exec.py

Se lee la hoja correspondiente al n del Excel de pruebas y se corre QNodes
sobre TODAS las filas (alcance x mecanismo).
Los resultados se guardan en results/qnodes/resultado__N{n}_{MUESTRA}.csv
"""

from src.models.base.application import aplicacion
from src.main import iniciar

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:  str = "1" + "0" * 19
MUESTRA: str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Inicialización del aplicativo QNodes."""
    aplicacion.desactivar_profiling()
    aplicacion.set_pagina_red_muestra(MUESTRA)

    iniciar(estado=ESTADO)


if __name__ == "__main__":
    main()
