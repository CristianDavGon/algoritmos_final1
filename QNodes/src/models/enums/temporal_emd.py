"""Enumeración de direcciones temporales de la EMD para la estrategia QNodes.

Define las tres modalidades de Earth Mover's Distance según la dirección
temporal del análisis causal: efecto (presente → futuro), causa
(futuro → presente) e integrada (ambas direcciones).

Typical usage example::

    from src.models.enums.temporal_emd import TimeEMD

    tiempo = TimeEMD.EMD_EFECTO
    print(tiempo.value)  # "emd-effect"
"""

from __future__ import annotations

from enum import Enum


class TimeEMD(Enum):
    """Direcciones temporales de la EMD admitidas por la estrategia QNodes.

    Cada miembro expone un identificador de cadena a través de ``.value``
    que es el valor almacenado en
    :attr:`~src.models.base.application.Application.tiempo_emd`.

    Attributes:
        EMD_EFECTO: EMD orientada al efecto; compara distribuciones del
            presente al futuro (``t → t+1``).
        EMD_CAUSA: EMD orientada a la causa; compara distribuciones del
            futuro al presente (``t+1 → t``).
        EMD_INTEGRADA: EMD integrada causa-efecto; combina ambas
            direcciones para calcular información integrada bidireccional.

    Example::

        from src.models.enums.temporal_emd import TimeEMD

        modalidad = TimeEMD.EMD_INTEGRADA
        assert modalidad.value == "emd-cause-effect"
    """

    EMD_EFECTO = "emd-effect"
    EMD_CAUSA = "emd-cause"
    EMD_INTEGRADA = "emd-cause-effect"
