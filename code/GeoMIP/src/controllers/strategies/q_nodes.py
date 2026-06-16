"""Estrategia QNodes para GeoMIP: MIP vía algoritmo de Queyranne (1998).

Implementa ``QNodes``, que extiende ``SIA`` con el algoritmo de ordenamiento
por máxima adyacencia (MAO, *Maximum Adjacency Ordering*) de Queyranne para
encontrar la bipartición de mínima información (MIP) en ``O(D³·N)``.

El algoritmo se importa desde el sub-proyecto ``QNodes/src/strategies/qnodes.py``
mediante ``_importar_oracle_qnodes``, que realiza un swap temporal de
``sys.modules`` para evitar colisiones de namespace entre los paquetes GeoMIP
y QNodes (ambos usan ``src`` como raíz).

Typical usage example::

    gestor = Manager(...)
    estrategia = QNodes(gestor)
    solucion = estrategia.aplicar_estrategia(condicion, alcance, mecanismo, tpm)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np

from src.constants.base import (
    ACTUAL,
    EFECTO,
    FLOAT_ZERO,
)
from src.constants.models import QNODES_LABEL, QNODES_STRAREGY_TAG
from src.controllers.manager import Manager
from src.funcs.base import emd_efecto
from src.funcs.format import fmt_biparte_q
from src.middlewares.slogger import SafeLogger
from src.models.base.sia import SIA
from src.models.core.solution import Solution

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Número de niveles hacia arriba en la jerarquía de directorios para
#: llegar a la raíz del workspace desde este archivo.
_NIVELES_HASTA_WORKSPACE: int = 4

#: Nombre del sub-proyecto que contiene el algoritmo de Queyranne.
_QNODES_SUBPROYECTO: str = "QNodes"

#: Partición vacía para subsistemas degenerados (D=0 o N=0).
_PARTICION_VACIA: str = "∅|∅"


# ---------------------------------------------------------------------------
# Carga dinámica del algoritmo de Queyranne (aislamiento de namespace)
# ---------------------------------------------------------------------------

def _importar_oracle_qnodes() -> tuple[Callable, Callable]:
    """Carga ``oracle`` y ``qnodes`` desde ``QNodes/src/strategies/qnodes.py``.

    Ambos paquetes (GeoMIP y QNodes) usan ``src`` como raíz de importación,
    por lo que es necesario hacer un swap temporal de ``sys.modules`` para que
    las importaciones internas de ``qnodes.py`` resuelvan a los módulos de
    QNodes y no a los de GeoMIP.

    El swap funciona en tres pasos:

    1. Guardar y eliminar de ``sys.modules`` todos los módulos ``src.*``
       de GeoMIP.
    2. Insertar temporalmente la ruta de QNodes en ``sys.path`` e importar.
    3. Eliminar los módulos de QNodes cargados y restaurar los de GeoMIP.

    Returns:
        Par ``(oracle, qnodes)`` donde ``oracle`` construye la función de
        coste y ``qnodes`` ejecuta el algoritmo MAO de Queyranne.

    Raises:
        ImportError: Si no se puede localizar ``QNodes/src/strategies/qnodes.py``.

    Example::

        oracle_fn, qnodes_fn = _importar_oracle_qnodes()
    """
    _qnodes_root = str(
        Path(__file__).resolve().parents[_NIVELES_HASTA_WORKSPACE]
        / _QNODES_SUBPROYECTO
    )

    # Paso 1: guardar y evacuar módulos src.* de GeoMIP
    _guardado = {
        k: v
        for k, v in sys.modules.items()
        if k == "src" or k.startswith("src.")
    }
    for k in list(_guardado):
        del sys.modules[k]

    _insertar = _qnodes_root not in sys.path
    if _insertar:
        sys.path.insert(0, _qnodes_root)
    try:
        # Paso 2: importar desde el namespace de QNodes
        from src.strategies.qnodes import oracle, qnodes  # type: ignore[import]
        return oracle, qnodes
    finally:
        # Paso 3: limpiar módulos de QNodes y restaurar los de GeoMIP
        if _insertar:
            sys.path.remove(_qnodes_root)
        for k in list(sys.modules.keys()):
            if k == "src" or k.startswith("src."):
                del sys.modules[k]
        sys.modules.update(_guardado)


oracle, _ejecutar_qnodes = _importar_oracle_qnodes()


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class QNodes(SIA):
    """MIP vía algoritmo de Queyranne (MAO): ``O(D³·N)`` con oracle lazy.

    Envuelve el algoritmo importado desde ``QNodes/src/strategies/qnodes.py``
    adaptando la interfaz de GeoMIP (``Manager``, ``System.dims_ncubos``,
    ``NCube.data``).

    Attributes:
        logger: Logger seguro con tag ``QNODES_STRAREGY_TAG``.

    Example::

        gestor = Manager(estado_inicial="101", pagina=0)
        sia = QNodes(gestor)
        sol = sia.aplicar_estrategia("111", "101", "011", tpm)
        print(sol.perdida, sol.particion)
    """

    def __init__(self, gestor: Manager) -> None:
        super().__init__(gestor)
        self.logger = SafeLogger(QNODES_STRAREGY_TAG)

    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray,
    ) -> Solution:
        """Ejecuta el algoritmo de Queyranne y retorna la solución MIP.

        Pasos principales:

        1. Preparar el subsistema condicionado.
        2. Manejar casos degenerados (``D=0`` o ``N=0``).
        3. Construir el tensor de datos ``data_nd`` desde los NCubes.
        4. Computar el pivot (estado inicial indexado por dims del subsistema).
        5. Calcular la línea base de concentración como candidato trivial.
        6. Invocar ``oracle`` + ``_ejecutar_qnodes`` (MAO de Queyranne).
        7. Resolver la bipartición y calcular EMD real.
        8. Retornar ``Solution``.

        Note:
            ``oracle`` y ``_ejecutar_qnodes`` se cargan en el nivel de módulo
            mediante ``_importar_oracle_qnodes``; no se re-importan en cada
            llamada.

        Args:
            condicion: Cadena binaria que indica qué dimensiones condicionar.
            alcance: Cadena binaria que selecciona elementos futuros (NCubes).
            mecanismo: Cadena binaria que selecciona elementos presentes (dims).
            tpm: Matriz de transición de probabilidades completa ``(2^N, N)``.

        Returns:
            Objeto ``Solution`` con la bipartición MIP, su pérdida (EMD),
            distribuciones del subsistema y de la partición, y tiempo total.

        Raises:
            ValueError: Si ``tpm`` no es compatible con el tamaño del sistema.

        Example::

            sol = sia.aplicar_estrategia("111", "101", "011", tpm)
            assert sol.perdida >= 0.0
        """
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
                particion=_PARTICION_VACIA,
                tiempo_total=FLOAT_ZERO,
                hablar=False,
            )

        # Tensor de datos desde los NCubes de GeoMIP (.data, no .ndata)
        data_nd = np.stack([c.data for c in sistema.ncubos])  # (N, 2, …, 2)

        # Pivot: estado inicial indexado por las dimensiones del subsistema
        pivot_idx = tuple(
            int(sistema.estado_inicial[dim])
            for dim in sistema.dims_ncubos
        )
        pivot_vals = data_nd[(slice(None),) + pivot_idx]   # shape (N,)

        # Línea base: nodo más determinista como candidato trivial
        all_mean = data_nd.reshape(N, -1).mean(axis=1)
        conc_costs = np.abs(all_mean - pivot_vals)
        conc_idx = int(np.argmin(conc_costs))
        C_conc = float(conc_costs[conc_idx])

        if D <= 1:
            alcance_mip: tuple[int, ...] = (
                sistema.ncubos[conc_idx].indice,
            )
            mecanismo_mip: tuple[int, ...] = ()
        else:
            full_mask = (1 << D) - 1
            f, means = oracle(
                N, D, data_nd, pivot_idx, pivot_vals, full_mask
            )
            best_val, best_mask_a = _ejecutar_qnodes(D, f, full_mask)

            if C_conc <= best_val:
                alcance_mip = (sistema.ncubos[conc_idx].indice,)
                mecanismo_mip = ()
            else:
                mean_a, mean_b = means(best_mask_a)
                node_in_a = (
                    np.abs(mean_b - pivot_vals)
                    <= np.abs(mean_a - pivot_vals)
                )
                alcance_mip = tuple(
                    c.indice
                    for i, c in enumerate(sistema.ncubos)
                    if node_in_a[i]
                )
                # dims_ncubos es ndarray: usamos posición para el bitmask
                mecanismo_mip = tuple(
                    int(sistema.dims_ncubos[d])
                    for d in range(D)
                    if (best_mask_a >> d) & 1
                )

        particion_sistema = sistema.bipartir(
            np.array(alcance_mip, dtype=np.int8),
            np.array(mecanismo_mip, dtype=np.int8),
        )
        dm = particion_sistema.distribucion_marginal()
        perdida = float(emd_efecto(dm, self.sia_dists_marginales))

        # Convertir a vértices (tiempo, índice) para fmt_biparte_q
        mip_vertices = (
            [(EFECTO, int(idx)) for idx in alcance_mip]
            + [(ACTUAL, int(dim)) for dim in mecanismo_mip]
        )
        comp_vertices = (
            [
                (EFECTO, int(idx))
                for idx in sistema.indices_ncubos
                if idx not in alcance_mip
            ]
            + [
                (ACTUAL, int(dim))
                for dim in sistema.dims_ncubos
                if dim not in mecanismo_mip
            ]
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
