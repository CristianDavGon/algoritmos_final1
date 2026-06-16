"""Enumeración de distancias métricas disponibles en la estrategia GeoMIP.

Define los identificadores de cadena que seleccionan el tipo de distancia
empleada en los cálculos de Earth Mover's Distance (EMD) y otras métricas
de comparación de distribuciones de probabilidad.

Typical usage example::

    from src.models.enums.distance import MetricDistance

    distancia = MetricDistance.EMD_EFECTO
    print(distancia.value)  # "emd-effect"
"""

from __future__ import annotations

from enum import Enum


class MetricDistance(Enum):
    """Distancias métricas admitidas por la estrategia GeoMIP.

    Cada miembro expone un identificador de cadena a través de ``.value``
    que es el valor almacenado en
    :attr:`~src.models.base.application.Application.distancia_metrica`.

    Attributes:
        EMD_EFECTO: EMD causal orientada al efecto (presente → futuro).
        EMD_CAUSA: EMD causal orientada a la causa (futuro → presente).
        MANHATTAN: Distancia de Manhattan (norma L1).
        EUCLIDIANA: Distancia euclídea (norma L2).

    Example::

        from src.models.enums.distance import MetricDistance

        metrica = MetricDistance.MANHATTAN
        assert metrica.value == "distancia-manhattan"
    """

    EMD_EFECTO = "emd-effect"
    EMD_CAUSA = "emd-cause"
    MANHATTAN = "distancia-manhattan"
    EUCLIDIANA = "distancia-euclidiana"
