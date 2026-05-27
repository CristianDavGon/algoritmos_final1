from src.models.base.application import aplicacion
from src.main import ejecutar_desde_excel
from pathlib import Path


def main():
    aplicacion.desactivar_profiling()
    aplicacion.set_pagina_red_muestra("A")

    project_root = Path(__file__).resolve().parents[1]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    ruta_salida = Path(__file__).resolve().parent / "results" / "resultados_N10A.csv"
    estado_inicio = "1000000000"

    ejecutar_desde_excel(ruta_excel, ruta_salida, estado_inicio)


if __name__ == "__main__":
    main()
