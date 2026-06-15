"""Punto de entrada para KQNodes (k-particiones submodular).

Configura aquí qué n, k y criterios correr; luego ejecuta:

    cd code/QNodes
    uv run exec_kqnodes.py

Para cada n se lee la hoja correspondiente del Excel de pruebas y se corre
KQNodes sobre TODAS las filas (alcance × mecanismo) con cada k y criterio.
Los resultados se guardan en results/kqnodes/resultado__N{n}_{MUESTRA}_{K}.csv
con una fila por (prueba, k, criterio).
"""

from src.models.base.application import aplicacion
from src.main_kqnodes import iniciar_kqnodes

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:   str = "1" + "0" * 19
K:        int = 4
CRITERIO: str = "C4"   # "C4" = corte marginal mínimo, "C1" = tamaño máximo
MUESTRA:  str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Inicialización del aplicativo KQNodes."""
    aplicacion.desactivar_profiling()
    aplicacion.set_pagina_red_muestra(MUESTRA)

    iniciar_kqnodes(
        estado=ESTADO,
        k=K,
        criterio=CRITERIO,
    )


if __name__ == "__main__":
    main()
