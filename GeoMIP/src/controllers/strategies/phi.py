"""Estrategia Phi: wrapper sobre PyPhi para cálculo de ground-truth de MIP.

Implementa ``Phi``, que extiende ``SIA`` delegando el cálculo de la bipartición
de mínima información (MIP) a la biblioteca ``pyphi`` (Tononi et al., IIT 4.0).

Se usa exclusivamente para **validación** (``k=2``, sistemas pequeños) ya que
PyPhi tiene complejidad exponencial.  Los resultados sirven como referencia de
exactitud para las demás estrategias (``GeometricSIA``, ``QNodes``,
``BruteForce``).

Nota de compatibilidad: PyPhi todavía importa ``Iterable``, ``Mapping``,
``MutableMapping`` y ``Sequence`` desde ``collections`` (Python ≤ 3.9). Este
módulo inyecta los alias necesarios en ``collections`` antes de importar pyphi
para mantener compatibilidad con Python 3.10+.

Typical usage example::

    gestor = Manager(...)
    estrategia = Phi(gestor)
    solucion = estrategia.aplicar_estrategia(condicion, alcance, mecanismo)
"""

from __future__ import annotations

import collections
import math
import time
from collections.abc import Iterable, Mapping, MutableMapping, Sequence

import numpy as np
from pyphi import Network, Subsystem
from pyphi.labels import NodeLabels
from pyphi.models.cuts import Bipartition, Part

from src.constants.base import (
    NET_LABEL,
    STR_ONE,
    TYPE_TAG,
)
from src.constants.models import (
    DUMMY_ARR,
    DUMMY_PARTITION,
    PYPHI_ANALYSIS_TAG,
    PYPHI_LABEL,
    PYPHI_STRAREGY_TAG,
)
from src.controllers.manager import Manager
from src.funcs.base import ABECEDARY, lil_endian
from src.funcs.format import fmt_biparticion
from src.middlewares.profile import profile, profiler_manager
from src.middlewares.slogger import SafeLogger
from src.models.base.application import aplicacion
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.enums.distance import MetricDistance

# ---------------------------------------------------------------------------
# Compatibilidad con Python 3.10+: pyphi aún usa collections.Iterable, etc.
# ---------------------------------------------------------------------------
if not hasattr(collections, "Iterable"):
    setattr(collections, "Iterable", Iterable)
if not hasattr(collections, "Mapping"):
    setattr(collections, "Mapping", Mapping)
if not hasattr(collections, "MutableMapping"):
    setattr(collections, "MutableMapping", MutableMapping)
if not hasattr(collections, "Sequence"):
    setattr(collections, "Sequence", Sequence)


class Phi(SIA):
    """Wrapper sobre PyPhi para cálculo de MIP como ground-truth (IIT 4.0).

    Delega el cálculo de efecto MIP o causa MIP a ``pyphi.Subsystem``
    según la métrica configurada en ``aplicacion.distancia_metrica``.

    Solo apto para sistemas pequeños (``k=2``); PyPhi tiene complejidad
    exponencial en el número de nodos.

    Attributes:
        logger: Logger seguro con tag ``PYPHI_STRAREGY_TAG``.

    Example::

        gestor = Manager(estado_inicial="101", pagina=0)
        sia = Phi(gestor)
        sol = sia.aplicar_estrategia("111", "101", "011")
        print(sol.perdida, sol.particion)
    """

    def __init__(self, config: Manager) -> None:
        super().__init__(config)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(config.estado_inicial)}{config.pagina}"
        )
        self.logger = SafeLogger(PYPHI_STRAREGY_TAG)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @profile(context={TYPE_TAG: PYPHI_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condiciones: str,
        alcance: str,
        mecanismo: str,
    ) -> Solution:
        """Calcula la MIP usando PyPhi y retorna la solución.

        Selecciona ``effect_mip`` o ``cause_mip`` según
        ``aplicacion.distancia_metrica``.  Si PyPhi no puede calcular
        repertorios (p.ej. mecanismo vacío), retorna distribuciones centinela.

        Note:
            Decorado con ``@profile``: registra tiempos en
            ``review/profiling/`` como HTML de pyinstrument.

        Args:
            condiciones: Cadena binaria de condiciones de fondo; los ``"1"``
                indican nodos que forman parte del candidato.
            alcance: Cadena binaria que selecciona el purview (alcance) del
                mecanismo; solo los bits ``"1"`` con condición ``"1"`` se
                incluyen.
            mecanismo: Cadena binaria que selecciona el mecanismo; solo los
                bits ``"1"`` con condición ``"1"`` se incluyen.

        Returns:
            Objeto ``Solution`` con la bipartición MIP encontrada por PyPhi,
            pérdida ``phi``, repertorios del subsistema y de la partición, y
            tiempo total.

        Example::

            sol = sia.aplicar_estrategia("111", "101", "011")
            assert sol.perdida >= 0.0
        """
        self.sia_tiempo_inicio = time.time()
        alcance_idx, mecanismo_idx, subsistema = self.preparar_subsistema(
            condiciones, alcance, mecanismo
        )
        mip = (
            subsistema.effect_mip(mecanismo_idx, alcance_idx)
            if aplicacion.distancia_metrica == MetricDistance.EMD_EFECTO.value
            else subsistema.cause_mip(mecanismo_idx, alcance_idx)
        )

        small_phi: float = mip.phi
        repertorio = np.array(DUMMY_ARR, dtype=np.float32)
        repertorio_partido = np.array(DUMMY_ARR, dtype=np.float32)
        formato_particion: str = DUMMY_PARTITION

        if (
            mip.repertoire is not None
            and mip.partitioned_repertoire is not None
        ):
            repertorio = mip.repertoire.flatten()
            repertorio_partido = mip.partitioned_repertoire.flatten()

            states = int(math.log2(mip.repertoire.size))
            sub_estados: np.ndarray = lil_endian(states)

            repertorio.put(sub_estados, repertorio)
            repertorio_partido.put(sub_estados, repertorio_partido)

            mejor_biparticion: Bipartition = mip.partition
            prim: Part = mejor_biparticion.parts[True]
            dual: Part = mejor_biparticion.parts[False]

            prim_mech, prim_purv = prim.mechanism, prim.purview
            dual_mech, dual_purv = dual.mechanism, dual.purview
            formato_particion = fmt_biparticion(
                [dual_mech, dual_purv],
                [prim_mech, prim_purv],
            )

        return Solution(
            estrategia=PYPHI_LABEL,
            perdida=small_phi,
            distribucion_subsistema=repertorio,
            distribucion_particion=repertorio_partido,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=formato_particion,
        )

    # ------------------------------------------------------------------
    # Preparación del subsistema PyPhi
    # ------------------------------------------------------------------

    def preparar_subsistema(
        self,
        condiciones: str,
        futuros: str,
        presentes: str,
    ) -> tuple[tuple[int, ...], tuple[int, ...], Subsystem]:
        """Construye la red y el subsistema PyPhi a partir de las cadenas binarias.

        Pasos:

        1. Construir la red completa con ``pyphi.Network`` a partir de la TPM.
        2. Seleccionar los nodos candidatos según ``condiciones``.
        3. Crear el ``pyphi.Subsystem`` con el estado inicial y los candidatos.
        4. Derivar los índices de alcance y mecanismo cruzando ``futuros`` /
           ``presentes`` con ``condiciones``.

        Args:
            condiciones: Cadena binaria; ``"1"`` en posición ``i`` indica que
                el nodo ``i`` pertenece al sistema candidato.
            futuros: Cadena binaria del purview (alcance futuro); solo los
                bits ``"1"`` con condición ``"1"`` se incluyen.
            presentes: Cadena binaria del mecanismo (presente); solo los bits
                ``"1"`` con condición ``"1"`` se incluyen.

        Returns:
            Tupla ``(alcance_idx, mecanismo_idx, subsistema)`` donde
            ``alcance_idx`` y ``mecanismo_idx`` son tuplas de enteros con
            los índices globales de nodos, y ``subsistema`` es el
            ``pyphi.Subsystem`` listo para calcular MIP.

        Example::

            alc, mec, sub = sia.preparar_subsistema("111", "101", "011")
        """
        estado_inicial = tuple(
            int(s) for s in self.sia_gestor.estado_inicial
        )
        longitud = len(estado_inicial)

        indices = tuple(range(longitud))
        etiquetas = tuple(ABECEDARY[:longitud])

        completo = NodeLabels(etiquetas, indices)
        mpt_estados_nodos_on = self.sia_cargar_tpm()
        red = Network(tpm=mpt_estados_nodos_on, node_labels=completo)
        self.sia_logger.critic("Original creado.")

        candidato = tuple(
            completo[i]
            for i, bit in enumerate(condiciones)
            if bit == STR_ONE
        )
        self.sia_logger.critic("Candidato creado.")

        subsistema = Subsystem(
            network=red, state=estado_inicial, nodes=candidato
        )
        self.sia_logger.critic("Subsistema creado.")

        alcance = tuple(
            ind
            for ind, (bit, cond) in enumerate(zip(futuros, condiciones))
            if (bit == STR_ONE) and (cond == STR_ONE)
        )
        mecanismo = tuple(
            ind
            for ind, (bit, cond) in enumerate(zip(presentes, condiciones))
            if (bit == STR_ONE) and (cond == STR_ONE)
        )

        return alcance, mecanismo, subsistema
