"""Estrategia Phi: wrapper sobre PyPhi para ground-truth de MIP.

Calcula la bipartición de mínima información integrada (φ) usando la
librería PyPhi como referencia de verdad. Soporta tanto el repertorio
de efecto (``EMD_EFECTO``) como el de causa (``cause_mip``).

Compatibilidad: parche de ``collections`` incluido para PyPhi con
Python 3.10+, donde los alias ``Iterable``, ``Mapping``,
``MutableMapping`` y ``Sequence`` fueron movidos a
``collections.abc``.

Typical usage example::

    estrategia = Phi(tpm)
    solucion = estrategia.aplicar_estrategia(
        estado_inicial="100",
        condiciones="111",
        alcance="110",
        mecanismo="101",
    )
    print(solucion.perdida)
"""

from __future__ import annotations

import collections
import math
import time
from collections.abc import Iterable, Mapping, MutableMapping, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Parche de compatibilidad para PyPhi en Python 3.10+
# ---------------------------------------------------------------------------
# PyPhi aún importa alias desde ``collections`` (movidos a
# ``collections.abc`` en 3.10). Se restauran si no existen.
if not hasattr(collections, "Iterable"):
    setattr(collections, "Iterable", Iterable)
if not hasattr(collections, "Mapping"):
    setattr(collections, "Mapping", Mapping)
if not hasattr(collections, "MutableMapping"):
    setattr(collections, "MutableMapping", MutableMapping)
if not hasattr(collections, "Sequence"):
    setattr(collections, "Sequence", Sequence)

from pyphi import Network, Subsystem  # noqa: E402
from pyphi.labels import NodeLabels  # noqa: E402
from pyphi.models.cuts import Bipartition, Part  # noqa: E402

from src.constants.base import (  # noqa: E402
    COLS_IDX,
    NET_LABEL,
    STR_ONE,
    TYPE_TAG,
)
from src.constants.models import (  # noqa: E402
    DUMMY_ARR,
    DUMMY_PARTITION,
    PYPHI_ANALYSIS_TAG,
    PYPHI_LABEL,
    PYPHI_STRAREGY_TAG,
)
from src.funcs.format import fmt_biparticion_fuerza_bruta  # noqa: E402
from src.funcs.iit import ABECEDARY, lil_endian  # noqa: E402
from src.middlewares.profile import (  # noqa: E402
    gestor_perfilado,
    profile,
)
from src.middlewares.slogger import SafeLogger  # noqa: E402
from src.models.base.application import aplicacion  # noqa: E402
from src.models.base.sia import SIA  # noqa: E402
from src.models.core.solution import Solution  # noqa: E402
from src.models.enums.temporal_emd import TimeEMD  # noqa: E402

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

#: Separador usado al formatear particiones multi-parte dinámicamente.
_SEP_PARTES: str = " | "


class Phi(SIA):
    """Wrapper sobre PyPhi para cálculo de ground-truth de φ (MIP).

    Delega el cálculo de la bipartición mínima a
    :func:`pyphi.Subsystem.effect_mip` o
    :func:`pyphi.Subsystem.cause_mip` según la configuración de
    ``aplicacion.tiempo_emd``.

    El decorador ``@profile`` está activo en ``aplicar_estrategia``;
    los resultados de profiling se guardan en ``review/profiling/``.

    Attributes:
        logger: Logger configurado con la etiqueta de la estrategia.

    Example::

        estrategia = Phi(tpm)
        sol = estrategia.aplicar_estrategia("10", "11", "10", "11")
        print(sol.perdida)
    """

    def __init__(self, tpm: np.ndarray) -> None:
        super().__init__(tpm)
        gestor_perfilado.start_session(
            f"{NET_LABEL}"
            f"{len(tpm[COLS_IDX])}"
            f"{aplicacion.pagina_red_muestra}"
        )
        self.logger = SafeLogger(PYPHI_STRAREGY_TAG)

    @profile(context={TYPE_TAG: PYPHI_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        estado_inicial: str,
        condiciones: str,
        alcance: str,
        mecanismo: str,
    ) -> Solution:
        """Calcula el MIP usando PyPhi como referencia de ground-truth.

        Construye la red y subsistema PyPhi, selecciona el tipo de MIP
        (efecto o causa) según ``aplicacion.tiempo_emd`` y extrae el φ
        y los repertorios resultantes.

        Soporta dos formatos de partición devueltos por PyPhi:

        - **Bipartición clásica** (``parts[True/False]``): formateada
          con ``fmt_biparticion_fuerza_bruta``.
        - **Multi-partición** (``parts`` como lista o dict con más de
          dos entradas): formateada dinámicamente como
          ``"(mec)/(pur) | ..."``.

        Decorador ``@profile`` activo; ver ``review/profiling/``.

        Args:
            estado_inicial: Estado inicial del sistema en binario,
                p. ej. ``"100"``.
            condiciones: Condiciones de fondo; bit ``'1'`` = nodo
                activo.
            alcance: Elementos futuros del subsistema;
                bit ``'1'`` = incluir.
            mecanismo: Elementos presentes del subsistema;
                bit ``'1'`` = incluir.

        Returns:
            Objeto :class:`~src.models.core.solution.Solution` con el
            φ, los repertorios subsistema y partición, y la
            representación textual de la bipartición.

        Example::

            sol = Phi(tpm).aplicar_estrategia("100", "111", "110", "101")
            assert sol.perdida >= 0.0
        """
        self.sia_tiempo_inicio = time.time()
        alcance_idx, mecanismo_idx, subsistema = self.preparar_subsistema(
            estado_inicial, condiciones, alcance, mecanismo
        )

        emd_tiempo = (
            aplicacion.tiempo_emd.value
            if isinstance(aplicacion.tiempo_emd, TimeEMD)
            else str(aplicacion.tiempo_emd)
        )
        mip = (
            subsistema.effect_mip(mecanismo_idx, alcance_idx)
            if emd_tiempo == TimeEMD.EMD_EFECTO.value
            else subsistema.cause_mip(mecanismo_idx, alcance_idx)
        )

        small_phi: float = mip.phi
        repertorio = repertorio_partido = DUMMY_ARR
        formato = DUMMY_PARTITION

        if mip.repertoire is not None:
            repertorio = mip.repertoire.flatten()
            repertorio_partido = mip.partitioned_repertoire.flatten()

            states = int(math.log2(mip.repertoire.size))
            sub_estados: np.ndarray = lil_endian(states)

            repertorio.put(sub_estados, repertorio)
            repertorio_partido.put(sub_estados, repertorio_partido)

            partition_obj = mip.partition
            try:
                # Ruta BI: bipartición clásica con partes True/False
                prim: Part = partition_obj.parts[True]
                dual: Part = partition_obj.parts[False]
                formato = fmt_biparticion_fuerza_bruta(
                    [dual.mechanism, dual.purview],
                    [prim.mechanism, prim.purview],
                )
            except (TypeError, KeyError, AttributeError):
                # Ruta ALL / multi-partición: formatear dinámicamente
                try:
                    raw_parts = (
                        list(partition_obj.parts.values())
                        if hasattr(partition_obj.parts, "values")
                        else list(partition_obj.parts)
                    )
                    formato = _SEP_PARTES.join(
                        f"({','.join(str(n) for n in p.mechanism)})"
                        f"/({','.join(str(n) for n in p.purview)})"
                        for p in raw_parts
                    )
                except Exception:
                    formato = DUMMY_PARTITION

        return Solution(
            estrategia=PYPHI_LABEL,
            perdida=small_phi,
            distribucion_subsistema=repertorio,
            distribucion_particion=repertorio_partido,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=formato,
        )

    def preparar_subsistema(
        self,
        estado_inicio: str,
        condiciones: str,
        futuros: str,
        presentes: str,
    ) -> tuple[tuple[int, ...], tuple[int, ...], Subsystem]:
        """Construye la red PyPhi y el subsistema condicionado.

        Aplica las condiciones de fondo para filtrar los nodos activos y
        construye el :class:`pyphi.Subsystem` con los nodos candidatos.

        Args:
            estado_inicio: Estado inicial del sistema en binario,
                p. ej. ``"100"``.
            condiciones: Condiciones de fondo; bit ``'1'`` = nodo activo
                en el candidato.
            futuros: Elementos futuros; bit ``'1'`` = incluir en alcance,
                condicionado a que ``condiciones`` también sea ``'1'``.
            presentes: Elementos presentes; bit ``'1'`` = incluir en
                mecanismo, condicionado a que ``condiciones`` sea ``'1'``.

        Returns:
            Tupla ``(alcance, mecanismo, subsistema)`` donde:

            - ``alcance``: índices de nodos futuros seleccionados.
            - ``mecanismo``: índices de nodos presentes seleccionados.
            - ``subsistema``: instancia :class:`pyphi.Subsystem` lista
              para ``effect_mip`` / ``cause_mip``.

        Example::

            alc, mec, sub = phi.preparar_subsistema(
                "100", "111", "110", "101"
            )
        """
        estado_inicial = tuple(int(s) for s in estado_inicio)
        longitud = len(estado_inicial)

        indices = tuple(range(longitud))
        etiquetas = tuple(ABECEDARY[:longitud])

        completo = NodeLabels(etiquetas, indices)
        mpt_estados_nodos_on = self.tpm

        red = Network(tpm=mpt_estados_nodos_on, node_labels=completo)

        candidato = tuple(
            completo[i]
            for i, bit in enumerate(condiciones)
            if bit == STR_ONE
        )

        subsistema = Subsystem(
            network=red, state=estado_inicial, nodes=candidato
        )
        self.logger.critic("Subsistema creado.")

        alcance = tuple(
            ind
            for ind, (bit, cond) in enumerate(
                zip(futuros, condiciones)
            )
            if (bit == STR_ONE) and (cond == STR_ONE)
        )
        mecanismo = tuple(
            ind
            for ind, (bit, cond) in enumerate(
                zip(presentes, condiciones)
            )
            if (bit == STR_ONE) and (cond == STR_ONE)
        )

        return alcance, mecanismo, subsistema
