"""Enumeración de notaciones de indexado binario para la estrategia GeoMIP.

Define las notaciones binarias soportadas al indexar los estados de la TPM.
La notación seleccionada determina el orden en que se asignan los índices a
los estados del hipercubo de estados.

Typical usage example::

    from src.models.enums.notation import Notation

    notacion = Notation.LIL_ENDIAN
    print(notacion.value)  # "little-endian"
"""

from __future__ import annotations

from enum import Enum


class Notation(Enum):
    """Notaciones de indexado binario admitidas por la estrategia GeoMIP.

    Cada miembro expone un identificador de cadena a través de ``.value``
    que es el valor almacenado en
    :attr:`~src.models.base.application.Application.notacion`.

    Attributes:
        LIL_ENDIAN: Orden little-endian; el bit menos significativo
            corresponde a la primera variable (índice 0).
        BIG_ENDIAN: Orden big-endian; el bit más significativo corresponde
            a la primera variable (índice 0).
        GRAY_CODE: Código Gray; estados adyacentes difieren en un único bit.
        SIGN_MAGNITUDE: Representación signo-magnitud.
        TWOS_COMPLEMENT: Complemento a dos.

    Example::

        from src.models.enums.notation import Notation

        notacion = Notation.BIG_ENDIAN
        assert notacion.value == "big-endian"
    """

    LIL_ENDIAN = "little-endian"
    BIG_ENDIAN = "big-endian"
    GRAY_CODE = "gray-code"
    SIGN_MAGNITUDE = "sign-magnitude"
    TWOS_COMPLEMENT = "two's-complement"
