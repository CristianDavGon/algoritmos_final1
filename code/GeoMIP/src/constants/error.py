"""Mensajes de error del módulo GeoMIP.

Centraliza todos los literales de error del sistema para facilitar
la internacionalización y el mantenimiento. Ningún mensaje de error
debe definirse fuera de este módulo.

Typical usage example::

    from src.constants.error import ERROR_INCOMPATIBLE_SIZES

    if len(estado) != esperado:
        raise ValueError(ERROR_INCOMPATIBLE_SIZES)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Errores de dimensión / compatibilidad
# ---------------------------------------------------------------------------

# Se emite cuando el vector de estado inicial no coincide en longitud
# con las condiciones, el alcance o el mecanismo definidos en el sistema.
ERROR_INCOMPATIBLE_SIZES: str = (
    "El estado inicial tiene una dimensión diferente con las "
    "condiciones, alcance o mecanismo."
)
