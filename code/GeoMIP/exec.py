"""Punto de entrada para GeoMIP (partición geométrica).

Configura aquí el estado de inicio y la muestra; luego ejecuta:

    cd code/GeoMIP
    uv run exec.py

Se lee la hoja correspondiente al n del Excel de pruebas y se corre GeoMIP
sobre TODAS las filas (alcance x mecanismo).
Los resultados se guardan en results/geomip/resultados_N{n}{MUESTRA}.csv
"""

from src.models.base.application import aplicacion
from src.main import iniciar

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:  str = "1" + "0" * 19
MUESTRA: str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Inicialización del aplicativo GeoMIP."""
    aplicacion.profiler_habilitado = False
    aplicacion.pagina_sample_network = MUESTRA

    iniciar(estado=ESTADO)


if __name__ == "__main__":
    main()
