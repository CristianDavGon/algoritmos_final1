"""Enumeración de distancias métricas disponibles en la estrategia QNodes.

Define los identificadores de cadena que seleccionan el tipo de distancia
empleada en las comparaciones de distribuciones de probabilidad (EMD,
Hamming, etc.).

Typical usage example::

    from src.models.enums.distance import MetricDistance

    distancia = MetricDistance.HAMMING
    print(distancia.value)  # "distancia-hamming"
"""

from __future__ import annotations

from enum import Enum


class MetricDistance(Enum):
    """Distancias métricas admitidas por la estrategia QNodes.

    Cada miembro expone un identificador de cadena a través de ``.value``
    que es el valor almacenado en
    :attr:`~src.models.base.application.Application.distancia_metrica`.

    Attributes:
        HAMMING: Distancia de Hamming; cuenta las posiciones en que dos
            cadenas de igual longitud difieren.
        MANHATTAN: Distancia de Manhattan (norma L1).
        EUCLIDIANA: Distancia euclídea (norma L2).

    Example::

        from src.models.enums.distance import MetricDistance

        metrica = MetricDistance.HAMMING
        assert metrica.value == "distancia-hamming"
    """

    HAMMING = "distancia-hamming"
    MANHATTAN = "distancia-manhattan"
    EUCLIDIANA = "distancia-euclidiana"
