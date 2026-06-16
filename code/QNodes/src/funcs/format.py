"""Funciones de formateo visual de biparticiones para QNodes.

Convierte la representación interna de una bipartición (mecanismo +
purview para cada parte) en cadenas de texto listas para mostrar en
consola o guardar en registros. Se usan caracteres Unicode de corchetes
extendidos (``⎛ ⎝ ⎞ ⎠``) para representar la fracción estándar de IIT.

Aunque cada función puede reutilizarse en nuevos algoritmos, se
recomienda crear una función nueva si la adaptación implica cambios
profundos en los argumentos.

Typical usage example::

    from src.funcs.format import fmt_biparticion_fuerza_bruta

    texto = fmt_biparticion_fuerza_bruta(
        parte_uno=([0, 2], [1]),
        parte_dos=([1], [0, 2]),
    )
    print(texto)
"""

from __future__ import annotations

from src.constants.base import BASE_TWO, COLON_DELIM, VOID_STR
from src.funcs.iit import ABECEDARY, LOWER_ABECEDARY


def fmt_biparticion_fuerza_bruta(
    parte_uno: list[tuple[int, ...], tuple[int, ...]],
    parte_dos: list[tuple[int, ...], tuple[int, ...]],
) -> str:
    """Formatea una bipartición de fuerza bruta en notación de fracción.

    Cada parte contiene un mecanismo (letras minúsculas, tiempo ``t``)
    y un purview (letras mayúsculas, tiempo ``t+1``). El resultado es
    un bloque de dos líneas con la forma::

        ⎛ purview_prim ⎞⎛ purview_dual ⎞
        ⎝ mech_prim    ⎠⎝ mech_dual    ⎠

    Args:
        parte_uno: Par ``(mecanismo, purview)`` de la parte primaria.
            Cada elemento es una secuencia de índices de nodos.
        parte_dos: Par ``(mecanismo, purview)`` de la parte dual.

    Returns:
        Cadena de dos líneas con la bipartición formateada.

    Example::

        print(fmt_biparticion_fuerza_bruta(([0], [1, 2]), ([1, 2], [0])))
        # ⎛  B,C  ⎞⎛  A    ⎞
        # ⎝  a    ⎠⎝  b,c  ⎠
    """
    mech_p, pur_p = parte_uno
    mech_d, purv_d = parte_dos

    # Convertir índices a letras o símbolo vacío
    purv_prim = (
        COLON_DELIM.join(ABECEDARY[j] for j in pur_p)
        if pur_p
        else VOID_STR
    )
    mech_prim = (
        COLON_DELIM.join(LOWER_ABECEDARY[i] for i in mech_p)
        if mech_p
        else VOID_STR
    )
    purv_dual = (
        COLON_DELIM.join(ABECEDARY[i] for i in purv_d)
        if purv_d
        else VOID_STR
    )
    mech_dual = (
        COLON_DELIM.join(LOWER_ABECEDARY[j] for j in mech_d)
        if mech_d
        else VOID_STR
    )

    width_prim = max(len(purv_prim), len(mech_prim)) + BASE_TWO
    width_dual = max(len(purv_dual), len(mech_dual)) + BASE_TWO

    return (
        f"⎛{purv_prim:^{width_prim}}⎞⎛{purv_dual:^{width_dual}}⎞\n"
        f"⎝{mech_prim:^{width_prim}}⎠⎝{mech_dual:^{width_dual}}⎠\n"
    )


def fmt_biparticion_q(
    prim: list[tuple[int, int]],
    dual: list[tuple[int, int]],
    to_sort: bool = True,
) -> str:
    """Formatea una bipartición Q (pares tiempo-índice) en dos columnas.

    Delega el formateo de cada parte a :func:`fmt_parte_q` y concatena
    los resultados horizontalmente.

    Args:
        prim: Lista de pares ``(tiempo, índice)`` de la parte primaria.
            ``tiempo == 1`` indica purview; ``tiempo == 0`` indica
            mecanismo.
        dual: Lista de pares ``(tiempo, índice)`` de la parte dual.
        to_sort: Si es ``True`` ordena cada parte por índice antes de
            formatear. Por defecto ``True``.

    Returns:
        Cadena de dos líneas terminada en ``"\\n"`` con ambas partes
        lado a lado.

    Example::

        print(fmt_biparticion_q([(1, 0), (0, 1)], [(1, 2)]))
        # ⎛ A ⎞⎛ C ⎞
        # ⎝ b ⎠⎝   ⎠
    """
    top_prim, bottom_prim = fmt_parte_q(prim, to_sort)
    top_dual, bottom_dual = fmt_parte_q(dual, to_sort)

    return f"{top_prim}{top_dual}\n{bottom_prim}{bottom_dual}\n"


def fmt_parte_q(
    parte: list[tuple[int, int]],
    a_ordenar: bool = True,
) -> tuple[str, str]:
    """Formatea una sola parte Q como par ``(línea_superior, línea_inferior)``.

    Separa los elementos de ``parte`` en purview (``tiempo == 1``,
    letras mayúsculas) y mecanismo (``tiempo == 0``, letras minúsculas)
    y los encuadra en corchetes extendidos Unicode.

    Args:
        parte: Lista de pares ``(tiempo, índice)`` donde ``tiempo``
            vale ``1`` para purview y ``0`` para mecanismo.
        a_ordenar: Si es ``True`` ordena por ``índice`` antes de
            formatear.

    Returns:
        Par de cadenas ``(línea_superior, línea_inferior)`` con los
        corchetes Unicode incluidos.

    Example::

        top, bottom = fmt_parte_q([(1, 0), (0, 2)])
        # top    → "⎛ A ⎞"
        # bottom → "⎝ c ⎠"
    """
    if a_ordenar:
        # Ordenar elementos por índice de nodo
        parte.sort(key=lambda x: x[1])

    purv: list[str] = []
    mech: list[str] = []
    for time, idx in parte:
        if time:
            purv.append(ABECEDARY[idx])
        else:
            mech.append(LOWER_ABECEDARY[idx])

    str_purv = COLON_DELIM.join(purv) if purv else VOID_STR
    str_mech = COLON_DELIM.join(mech) if mech else VOID_STR
    width = max(len(str_purv), len(str_mech)) + 2

    return f"⎛{str_purv:^{width}}⎞", f"⎝{str_mech:^{width}}⎠"
