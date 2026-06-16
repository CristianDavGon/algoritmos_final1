"""Punto de entrada para KGeoMIP (k-particiones geométricas).

Configura el estado, k y variante a ejecutar; luego::

    cd code/GeoMIP
    uv run exec_kgeomip.py

Lee la hoja del Excel de pruebas correspondiente al n del estado y ejecuta
KGeoMIP sobre TODAS las filas (alcance × mecanismo).
Los resultados se guardan en
``results/kgeomip/resultado__N{n}_{MUESTRA}_{k}.csv``.
"""

from __future__ import annotations

from src.main_kgeomip import iniciar_kgeomip
from src.models.base.application import aplicacion

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:   str = "1" + "0" * 19
K:        int = 5
VARIANTE: str = "E4"   # "E4" = divisivo (recomendado), "A" = aglomerativo
MUESTRA:  str = "A"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Configura el singleton de aplicación e inicia KGeoMIP."""
    aplicacion.profiler_habilitado = False
    aplicacion.pagina_sample_network = MUESTRA

    iniciar_kgeomip(
        estado=ESTADO,
        k=K,
        variante=VARIANTE,
    )


if __name__ == "__main__":
    main()
