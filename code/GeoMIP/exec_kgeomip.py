"""Punto de entrada para KGeoMIP (k-particiones geométricas).

Configura aquí qué estado, k y variante correr; luego ejecuta:

    cd code/GeoMIP
    uv run exec_kgeomip.py

Se lee la hoja correspondiente al n del Excel de pruebas y se corre KGeoMIP
sobre TODAS las filas (alcance × mecanismo).
Los resultados se guardan en results/kgeomip/resultado__N{n}_{MUESTRA}_{k}.csv
"""

from src.models.base.application import aplicacion
from src.main_kgeomip import iniciar_kgeomip

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:   str = "1" + "0" * 7
K:        int = 4
VARIANTE: str = "E4"
MUESTRA:  str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Inicialización del aplicativo KGeoMIP."""
    aplicacion.profiler_habilitado = False
    aplicacion.pagina_sample_network = MUESTRA

    iniciar_kgeomip(
        estado=ESTADO,
        k=K,
        variante=VARIANTE,
    )


if __name__ == "__main__":
    main()
