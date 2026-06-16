"""Funciones de corte para KGeoMIP: candidatos de bipartición y cálculo de Φ.

Extraídas de ``kgeomip.py`` para mantener cada módulo dentro del límite de
300 LOC de lógica real. Son compartidas con los tests de regresión y con
cualquier variante BruteForce-k; ``kgeomip.py`` las reexporta al exterior.

Typical usage example::

    from src.controllers.strategies.kgeomip_cortes import (
        _candidatos_por_afinidad,
        _calcular_phi_total,
        _UMBRAL_ENUMERACION,
    )

    candidatos = _candidatos_por_afinidad(bloque, S, max_candidatos=20)
    phi = _calcular_phi_total(particion, sistema)
"""

from __future__ import annotations

import numpy as np

from src.funcs.base import emd_efecto, seleccionar_subestado
from src.models.core.system import System

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------

# Número máximo de biparticiones (2^(m-1) - 1) que se evalúan de forma
# exhaustiva y vectorizada. Por encima de este umbral los candidatos se
# generan constructivamente en O(m²) para evitar la explosión exponencial
# (OPT-K1).
_UMBRAL_ENUMERACION: int = 4096


# ---------------------------------------------------------------------------
# Candidatos enumerados (bloques pequeños)
# ---------------------------------------------------------------------------


def _candidatos_enumerados(
    S_P: np.ndarray,
    m: int,
    max_candidatos: int,
) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Enumera y puntúa TODAS las biparticiones de ``{0..m-1}``, vectorizado.

    ``score(A, B) = mean(S_P[i, j] para i∈A, j∈B)``. La suma cruzada se
    obtiene con álgebra matricial sobre la matriz de membresía de todas
    las máscaras: ``cruzada(A) = 1_A·S_P·1 − 1_A·S_P·1_A`` (``S_P``
    simétrica), sin bucle Python interno.

    Args:
        S_P: Submatriz de similitud ``m×m`` del bloque (índices locales
            ``0..m-1``).
        m: Tamaño del bloque.
        max_candidatos: Número máximo de candidatos a retornar.

    Returns:
        Lista de pares ``(A, B)`` en índices locales ordenada por score
        ascendente y truncada a ``max_candidatos``.

    Example::

        S_P = np.array([[0.0, 0.1], [0.1, 0.0]])
        pares = _candidatos_enumerados(S_P, m=2, max_candidatos=5)
        assert len(pares) == 1
    """
    masks = np.arange(1, 1 << (m - 1), dtype=np.int64)
    M = (
        (masks[:, None] >> np.arange(m, dtype=np.int64)) & 1
    ).astype(np.float64)
    fila_tot = S_P.sum(axis=1)
    cruzada = M @ fila_tot - ((M @ S_P) * M).sum(axis=1)
    tam_A = M.sum(axis=1)
    score = cruzada / (tam_A * (m - tam_A))

    todos = frozenset(range(m))
    pares: list[tuple[frozenset[int], frozenset[int]]] = []
    for t in np.argsort(score, kind="stable")[:max_candidatos]:
        A = frozenset(np.nonzero(M[t])[0].tolist())
        pares.append((A, todos - A))
    return pares


# ---------------------------------------------------------------------------
# Candidatos constructivos (bloques grandes)
# ---------------------------------------------------------------------------


def _candidatos_constructivos(
    S_P: np.ndarray,
    m: int,
    max_candidatos: int,
) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Genera candidatos en O(m²) sin enumeración para bloques grandes (OPT-K1).

    Estrategia en tres pasos:

    1. **Semillas**: el par ``(i, j)`` de mínima afinidad ``S_P[i, j]``
       (los nodos causalmente más independientes deben quedar en lados
       opuestos del corte).
    2. **Ordenamiento**: el resto de nodos se ordena por afinidad relativa
       hacia cada semilla (``delta = S_P[:, i_s] − S_P[:, j_s]``).
    3. **Candidatos**: los ``m-1`` cortes de prefijo del ordenamiento, más
       variaciones de intercambio en la frontera, se puntúan por afinidad
       cruzada media y se truncan a ``max_candidatos``.

    Args:
        S_P: Submatriz de similitud ``m×m`` del bloque (índices locales
            ``0..m-1``).
        m: Tamaño del bloque.
        max_candidatos: Número máximo de candidatos a retornar.

    Returns:
        Lista de pares ``(A, B)`` en índices locales ordenada por score
        ascendente y truncada a ``max_candidatos``.

    Example::

        S_P = np.random.rand(10, 10)
        pares = _candidatos_constructivos(S_P, m=10, max_candidatos=20)
        assert 1 <= len(pares) <= 20
    """
    sin_diag = S_P.copy()
    np.fill_diagonal(sin_diag, np.inf)
    i_s, j_s = (
        int(v)
        for v in np.unravel_index(np.argmin(sin_diag), sin_diag.shape)
    )

    delta = S_P[:, i_s] - S_P[:, j_s]
    resto = sorted(
        (v for v in range(m) if v not in (i_s, j_s)),
        key=lambda v: -float(delta[v]),
    )
    orden = [i_s, *resto, j_s]
    todos = frozenset(range(m))

    def _canon(lado: set[int]) -> frozenset[int]:
        A = frozenset(lado)
        return A if 0 in A else todos - A

    base: set[frozenset[int]] = set()
    for t in range(1, m):
        prefijo = set(orden[:t])
        base.add(_canon(prefijo))
        if t > 1:
            # Variación de frontera: el último elemento de A se intercambia
            # con el primero de B para generar un candidato adicional.
            variacion = (prefijo - {orden[t - 1]}) | {orden[t]}
            if 0 < len(variacion) < m:
                base.add(_canon(variacion))

    puntuados: list[tuple[float, frozenset[int]]] = []
    for A in base:
        A_arr = np.fromiter(A, dtype=np.int64, count=len(A))
        B_arr = np.fromiter(
            todos - A, dtype=np.int64, count=m - len(A)
        )
        puntuados.append(
            (float(S_P[np.ix_(A_arr, B_arr)].mean()), A)
        )
    puntuados.sort(key=lambda c: c[0])
    return [(A, todos - A) for _, A in puntuados[:max_candidatos]]


# ---------------------------------------------------------------------------
# Interfaz pública de candidatos
# ---------------------------------------------------------------------------


def _candidatos_por_afinidad(
    P: frozenset[int],
    S: np.ndarray,
    max_candidatos: int,
) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Biparticiones de ``P`` ordenadas por afinidad cruzada ascendente en ``S``.

    ``score(A, B) = mean(S[i, j] para i ∈ A, j ∈ B)``. Las biparticiones con
    menor afinidad cruzada separan nodos causalmente más independientes y se
    priorizan como candidatos geométricamente plausibles (principio "S
    propone").

    Régimen por tamaño de bloque (OPT-K1):

    - Si ``2^(|P|−1) − 1 ≤ _UMBRAL_ENUMERACION``: se enumeran todas las
      biparticiones con scoring vectorizado (exacto).
    - En caso contrario: se generan candidatos constructivamente en O(m²),
      sin enumeración exponencial.

    Args:
        P: Bloque a bipartir (frozenset de índices locales del ncubo).
        S: Matriz de similitud ``D×D`` del subsistema completo.
        max_candidatos: Número máximo de candidatos a retornar.

    Returns:
        Lista de pares ``(A, B)`` en índices globales del ncubo, ordenada
        por score ascendente y truncada a ``max_candidatos``.

    Example::

        P = frozenset({0, 1, 2})
        S = np.eye(3)
        pares = _candidatos_por_afinidad(P, S, max_candidatos=10)
        assert all(a | b == P for a, b in pares)
    """
    P_sorted = sorted(P)
    m = len(P_sorted)
    if m <= 1:
        return []

    S_P = S[np.ix_(P_sorted, P_sorted)]
    if (1 << (m - 1)) - 1 <= _UMBRAL_ENUMERACION:
        pares_locales = _candidatos_enumerados(S_P, m, max_candidatos)
    else:
        pares_locales = _candidatos_constructivos(S_P, m, max_candidatos)

    return [
        (
            frozenset(P_sorted[i] for i in A_loc),
            frozenset(P_sorted[i] for i in B_loc),
        )
        for A_loc, B_loc in pares_locales
    ]


# ---------------------------------------------------------------------------
# Cálculo de Φ total
# ---------------------------------------------------------------------------


def _calcular_phi_total(
    particion: list[frozenset[int]],
    sistema: System,
) -> float:
    """Calcula ``Φ* = EMD(p_original, ⊗_{Pm} p_{Pm})`` para la k-partición dada.

    Reconstruye la distribución factorizada marginalizando cada NCubo sobre
    las dimensiones fuera de su parte y leyendo el subestado inicial. Una
    sola llamada a ``emd_efecto`` al final (D4-04).

    Args:
        particion: Lista de partes de la k-partición (frozensets de índices
            locales sobre ``sistema.dims_ncubos``).
        sistema: Subsistema preparado (``System``) con sus NCubos y estado
            inicial.

    Returns:
        Valor escalar de Φ* calculado con la misma ``emd_efecto`` que
        GeoMIP en producción.

    Raises:
        IndexError: Si un índice de parte supera el número de NCubos del
            sistema (solo en caso de uso incorrecto).

    Example::

        phi = _calcular_phi_total([frozenset({0}), frozenset({1})], sistema)
        assert phi >= 0.0
    """
    dm_original = sistema.distribucion_marginal()
    todas_dims = list(sistema.dims_ncubos)
    N = len(sistema.ncubos)
    dist_recons = np.empty(N, dtype=np.float32)
    cubiertos: set[int] = set()

    for parte in particion:
        pi_global = frozenset(
            todas_dims[d] for d in parte if d < len(todas_dims)
        )
        non_pi = np.array(
            [g for g in todas_dims if g not in pi_global], dtype=np.int8
        )
        for d in parte:
            if d >= N:
                continue
            cubiertos.add(d)
            ncubo = sistema.ncubos[d]
            marg = ncubo.marginalizar(non_pi) if non_pi.size else ncubo
            if marg.dims.size:
                sub = tuple(
                    int(sistema.estado_inicial[g]) for g in marg.dims
                )
                dist_recons[d] = 1.0 - float(
                    marg.data[seleccionar_subestado(sub)]
                )
            else:
                dist_recons[d] = 1.0 - float(marg.data)

    for d in range(N):
        if d not in cubiertos:
            ncubo = sistema.ncubos[d]
            non_all = np.array(todas_dims, dtype=np.int8)
            marg = ncubo.marginalizar(non_all)
            if marg.dims.size:
                sub = tuple(
                    int(sistema.estado_inicial[g]) for g in marg.dims
                )
                dist_recons[d] = 1.0 - float(
                    marg.data[seleccionar_subestado(sub)]
                )
            else:
                dist_recons[d] = 1.0 - float(marg.data)

    return emd_efecto(dm_original, dist_recons)
