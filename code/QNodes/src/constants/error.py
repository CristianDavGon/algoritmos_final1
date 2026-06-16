"""Mensajes de error del módulo QNodes.

Centraliza todos los literales de error del sistema para facilitar
la internacionalización y el mantenimiento. Ningún mensaje de error
debe definirse fuera de este módulo.

Typical usage example::

    from src.constants.error import ERROR_ESPACIOS_INCOMPATIBLES

    if len(estado) != espacio:
        raise ValueError(ERROR_ESPACIOS_INCOMPATIBLES(espacio))
"""

from __future__ import annotations


def ERROR_ESPACIOS_INCOMPATIBLES(espacio: int) -> str:
    """Genera el mensaje de error para estados de longitud incorrecta.

    Args:
        espacio: Longitud esperada del vector de estado inicial.

    Returns:
        Cadena de error con la longitud esperada interpolada.

    Example::

        msg = ERROR_ESPACIOS_INCOMPATIBLES(8)
        # "Estado inicial debe tener longitud 8"
    """
    return f"Estado inicial debe tener longitud {espacio}"
