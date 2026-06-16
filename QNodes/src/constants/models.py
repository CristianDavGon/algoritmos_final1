"""Etiquetas y tags de estrategias del módulo QNodes.

Define los identificadores de texto usados en objetos ``Solution``,
reportes y registros para cada estrategia de análisis de
irreducibilidad de sistemas (SIA).

Typical usage example::

    from src.constants.models import QNODES_ANALYSIS_TAG

    solucion.tag = QNODES_ANALYSIS_TAG
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Sistema (valores centinela)
# ---------------------------------------------------------------------------
DUMMY_EMD: int = -1                     # Valor centinela para EMD no calculado
DUMMY_ARR: list[int] = [0]              # Array centinela para partición vacía
ERROR_PARTITION: str = (
    "No hay suficientes elementos para particionar.\n"
)
DUMMY_PARTITION: str = "NO-PARTITION\n"  # Etiqueta de partición nula

# ---------------------------------------------------------------------------
# SIA — System Irreducibility Analysis
# ---------------------------------------------------------------------------
SIA_LABEL: str = "sia"
SIA_PREPARATION_TAG: str = f"{SIA_LABEL}_preparation"

# ---------------------------------------------------------------------------
# Fuerza Bruta
# ---------------------------------------------------------------------------
BRUTEFORCE_LABEL: str = "BruteForce"
BRUTEFORCE_STRAREGY_TAG: str = f"{BRUTEFORCE_LABEL}_strategy"
BRUTEFORCE_ANALYSIS_TAG: str = f"{BRUTEFORCE_LABEL}_analysis"
BRUTEFORCE_FULL_ANALYSIS_TAG: str = f"{BRUTEFORCE_LABEL}_full_analysis"

# ---------------------------------------------------------------------------
# Pyphi
# ---------------------------------------------------------------------------
PYPHI_LABEL: str = "Pyphi"
PYPHI_STRAREGY_TAG: str = f"{PYPHI_LABEL}_strategy"
PYPHI_ANALYSIS_TAG: str = f"{PYPHI_LABEL}_analysis"

# ---------------------------------------------------------------------------
# Q-Nodes
# ---------------------------------------------------------------------------
QNODES_LABEL: str = "Q-Nodes"
QNODES_STRAREGY_TAG: str = f"{QNODES_LABEL}_strategy"
QNODES_ANALYSIS_TAG: str = f"{QNODES_LABEL}_analysis"

# ---------------------------------------------------------------------------
# Geometric (GeoMIP)
# ---------------------------------------------------------------------------
GEOMETRIC_LABEL: str = "Geometric"
GEOMETRIC_STRAREGY_TAG: str = f"{GEOMETRIC_LABEL}_strategy"
GEOMETRIC_ANALYSIS_TAG: str = f"{GEOMETRIC_LABEL}_analysis"
