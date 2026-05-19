"""QNodes para GeoMIP: importa oracle y qnodes desde QNodes/src/strategies/qnodes.py."""
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np

from src.funcs.base import emd_efecto
from src.funcs.format import fmt_biparte_q
from src.controllers.manager import Manager
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.middlewares.slogger import SafeLogger
from src.constants.base import (
    FLOAT_ZERO,
    EFECTO,
    ACTUAL,
)
from src.constants.models import QNODES_LABEL, QNODES_STRAREGY_TAG


def _importar_oracle_qnodes() -> tuple[Callable, Callable]:
    """
    Carga las funciones oracle y qnodes desde QNodes/src/strategies/qnodes.py
    sin contaminar el namespace de GeoMIP.

    Ambos paquetes usan 'src' como raíz, por lo que es necesario hacer un swap
    temporal de sys.modules para que las importaciones internas de qnodes.py
    resuelvan a los módulos de QNodes y no a los de GeoMIP.
    """
    _qnodes_root = str(Path(__file__).resolve().parents[4] / "QNodes")

    # Guardar y evacuar módulos src.* de GeoMIP para evitar colisión de namespace
    _guardado = {k: v for k, v in sys.modules.items()
                 if k == "src" or k.startswith("src.")}
    for k in list(_guardado):
        del sys.modules[k]

    _insertar = _qnodes_root not in sys.path
    if _insertar:
        sys.path.insert(0, _qnodes_root)
    try:
        from src.strategies.qnodes import oracle, qnodes  # type: ignore[import]
        return oracle, qnodes
    finally:
        if _insertar:
            sys.path.remove(_qnodes_root)
        # Limpiar los módulos de QNodes que se cargaron durante el import
        for k in list(sys.modules.keys()):
            if k == "src" or k.startswith("src."):
                del sys.modules[k]
        # Restaurar los módulos originales de GeoMIP
        sys.modules.update(_guardado)


oracle, _ejecutar_qnodes = _importar_oracle_qnodes()


class QNodes(SIA):
    """
    MIP via Queyranne: O(D³·N) con oracle lazy.
    Algoritmo importado desde QNodes/src/strategies/qnodes.py.
    Compatibilidad con la interfaz de GeoMIP: Manager, System.dims_ncubos, NCube.data.
    """

    def __init__(self, gestor: Manager):
        super().__init__(gestor)
        self.logger = SafeLogger(QNODES_STRAREGY_TAG)

    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray,
    ) -> Solution:
        self.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm)

        sistema = self.sia_subsistema
        D = int(sistema.dims_ncubos.size)
        N = len(sistema.ncubos)

        if D == 0 or N == 0:
            return Solution(
                estrategia=QNODES_LABEL,
                perdida=FLOAT_ZERO,
                distribucion_subsistema=self.sia_dists_marginales,
                distribucion_particion=self.sia_dists_marginales,
                particion="∅|∅",
                tiempo_total=0.0,
                hablar=False,
            )

        # Tensor de datos desde los NCubes de GeoMIP (.data, no .ndata)
        data_nd = np.stack([c.data for c in sistema.ncubos])  # (N, 2, …, 2)

        # Pivot: estado inicial indexado por las dimensiones del subsistema
        pivot_idx = tuple(int(sistema.estado_inicial[dim]) for dim in sistema.dims_ncubos)
        pivot_vals = data_nd[(slice(None),) + pivot_idx]  # shape (N,)

        # Baseline de concentración: nodo más determinista como candidato trivial
        all_mean = data_nd.reshape(N, -1).mean(axis=1)
        conc_costs = np.abs(all_mean - pivot_vals)
        conc_idx = int(np.argmin(conc_costs))
        C_conc = float(conc_costs[conc_idx])

        if D <= 1:
            alcance_mip: tuple[int, ...] = (sistema.ncubos[conc_idx].indice,)
            mecanismo_mip: tuple[int, ...] = ()
        else:
            full_mask = (1 << D) - 1
            f, means = oracle(N, D, data_nd, pivot_idx, pivot_vals, full_mask)
            best_val, best_mask_a = _ejecutar_qnodes(D, f, full_mask)

            if C_conc <= best_val:
                alcance_mip = (sistema.ncubos[conc_idx].indice,)
                mecanismo_mip = ()
            else:
                mean_a, mean_b = means(best_mask_a)
                node_in_a = np.abs(mean_b - pivot_vals) <= np.abs(mean_a - pivot_vals)
                alcance_mip = tuple(
                    c.indice for i, c in enumerate(sistema.ncubos) if node_in_a[i]
                )
                # dims_ncubos es un ndarray: usamos índice de posición para el bitmask
                mecanismo_mip = tuple(
                    int(sistema.dims_ncubos[d]) for d in range(D) if (best_mask_a >> d) & 1
                )

        particion_sistema = sistema.bipartir(
            np.array(alcance_mip, dtype=np.int8),
            np.array(mecanismo_mip, dtype=np.int8),
        )
        dm = particion_sistema.distribucion_marginal()
        perdida = float(emd_efecto(dm, self.sia_dists_marginales))

        # Convertir a formato de vértices (tiempo, índice) que espera fmt_biparte_q
        mip_vertices = (
            [(EFECTO, int(idx)) for idx in alcance_mip]
            + [(ACTUAL, int(dim)) for dim in mecanismo_mip]
        )
        comp_vertices = (
            [(EFECTO, int(idx)) for idx in sistema.indices_ncubos if idx not in alcance_mip]
            + [(ACTUAL, int(dim)) for dim in sistema.dims_ncubos if dim not in mecanismo_mip]
        )
        texto_particion = fmt_biparte_q(mip_vertices, comp_vertices)

        return Solution(
            estrategia=QNODES_LABEL,
            perdida=perdida,
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=dm,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=texto_particion,
            hablar=False,
        )
