import os
import multiprocessing
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parents[1]
    os.environ["GEOMIP_INPUT_XLSX"] = str(project_root / "data" / "DatosPruebas2026_1.xlsx")
    os.environ["GEOMIP_OUTPUT_CSV"] = str(Path(__file__).resolve().parent / "results" / "resultados_N10A.csv")
    os.environ["GEOMIP_ESTADO_INICIO"] = "1000000000"

    from src.models.base.application import aplicacion
    aplicacion.profiler_habilitado = False

    from src.main import iniciar
    iniciar()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
