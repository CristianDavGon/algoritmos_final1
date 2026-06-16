"""Punto de entrada para GeoMIP (bipartición geométrica).

Configura el estado de inicio y la muestra de red; luego ejecuta::

    cd code/GeoMIP
    uv run exec.py

Lee la hoja del Excel de pruebas correspondiente al n del estado y ejecuta
GeoMIP sobre TODAS las filas (alcance × mecanismo).
Los resultados se guardan en ``results/geomip/resultados_N{n}{MUESTRA}.csv``.
"""

from __future__ import annotations

from src.main import iniciar
from src.models.base.application import aplicacion

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:  str = "1" + "0" * 19
MUESTRA: str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Configura el singleton de aplicación e inicia GeoMIP."""
    aplicacion.profiler_habilitado = False
    aplicacion.pagina_sample_network = MUESTRA

    iniciar(estado=ESTADO)


if __name__ == "__main__":
    main()
