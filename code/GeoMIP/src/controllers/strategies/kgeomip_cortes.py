"""Funciones de módulo de KGeoMIP: candidatos de corte y Φ total (OPT-K1).

Extraídas de `kgeomip.py` para respetar el límite de 300 LOC por archivo.
Compartidas con tests y BruteForce-k; `kgeomip.py` las reexporta.
"""

from __future__ import annotations

import numpy as np

from src.funcs.base import emd_efecto, seleccionar_subestado
from src.models.core.system import System

# Máximo de biparticiones (2^(m-1) - 1) que se enumeran/puntúan de forma
# exhaustiva. Por encima, los candidatos se generan constructivamente en
# O(m²) — sin enumeración exponencial (OPT-K1).
_UMBRAL_ENUMERACION = 4096


def _candidatos_enumerados(
    S_P: np.ndarray,
    m: int,
    max_candidatos: int,
) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Enumera y puntúa TODAS las biparticiones de {0..m-1}, vectorizado.

    score(A, B) = mean(S_P[i, j] para i∈A, j∈B). La suma cruzada se obtiene
    con álgebra matricial sobre la matriz de membresía de todas las máscaras:
    cruzada(A) = 1_A·S_P·1 − 1_A·S_P·1_A (S_P simétrica), sin bucle Python.

    Args:
        S_P: Submatriz de similitud m×m del bloque (índices locales 0..m-1).
        m: Tamaño del bloque.
        max_candidatos: Número máximo de candidatos a retornar.

    Returns:
        Lista de (A, B) locales ordenada por score ascendente, truncada.
    """
    masks = np.arange(1, 1 << (m - 1), dtype=np.int64)
    M = ((masks[:, None] >> np.arange(m, dtype=np.int64)) & 1).astype(np.float64)
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


def _candidatos_constructivos(
    S_P: np.ndarray,
    m: int,
    max_candidatos: int,
) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Candidatos O(m²) sin enumeración para bloques grandes (OPT-K1).

    (i) Semillas: el par (i, j) de mínima afinidad S_P[i, j] (los nodos menos
    relacionados causalmente deben quedar en lados opuestos). (ii) El resto se
    ordena por afinidad relativa hacia cada semilla. (iii) Los m−1 cortes de
    prefijo de ese ordenamiento, más variaciones de intercambio en la
    frontera, forman los candidatos; se puntúan por afinidad cruzada media y
    se trunca a `max_candidatos`.

    Args:
        S_P: Submatriz de similitud m×m del bloque (índices locales 0..m-1).
        m: Tamaño del bloque.
        max_candidatos: Número máximo de candidatos a retornar.

    Returns:
        Lista de (A, B) locales ordenada por score ascendente, truncada.
    """
    sin_diag = S_P.copy()
    np.fill_diagonal(sin_diag, np.inf)
    i_s, j_s = (int(v) for v in np.unravel_index(np.argmin(sin_diag), sin_diag.shape))

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
            # Variación de frontera: el último de A se intercambia con el primero de B
            variacion = (prefijo - {orden[t - 1]}) | {orden[t]}
            if 0 < len(variacion) < m:
                base.add(_canon(variacion))

    puntuados: list[tuple[float, frozenset[int]]] = []
    for A in base:
        A_arr = np.fromiter(A, dtype=np.int64, count=len(A))
        B_arr = np.fromiter(todos - A, dtype=np.int64, count=m - len(A))
        puntuados.append((float(S_P[np.ix_(A_arr, B_arr)].mean()), A))
    puntuados.sort(key=lambda c: c[0])
    return [(A, todos - A) for _, A in puntuados[:max_candidatos]]


def _candidatos_por_afinidad(
    P: frozenset[int],
    S: np.ndarray,
    max_candidatos: int,
) -> list[tuple[frozenset[int], frozenset[int]]]:
    """Biparticiones de P ordenadas por afinidad cruzada ascendente en S.

    score(A, B) = mean(S[i, j] para i en A, j en B). Las biparticiones con
    menor afinidad cruzada separan nodos menos relacionados causalmente y
    se priorizan como candidatos geométricamente plausibles (S propone).

    Régimen por tamaño (OPT-K1): si 2^(|P|−1) − 1 ≤ `_UMBRAL_ENUMERACION`
    se enumeran todas las biparticiones (scoring vectorizado); si no, se
    generan constructivamente en O(m²) sin enumeración exponencial.

    Args:
        P: Bloque a bipartir (frozenset de índices locales).
        S: Matriz de similitud D×D.
        max_candidatos: Número máximo de candidatos a retornar.

    Returns:
        Lista de (A, B) ordenada por score ascendente, truncada a max_candidatos.
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


def _calcular_phi_total(
    particion: list[frozenset[int]],
    sistema: System,
) -> float:
    """Φ* = EMD(p_original, ⊗_Pm p_Pm). Una sola llamada al final.

    Args:
        particion: Lista de partes (frozensets de índices locales).
        sistema: Subsistema preparado.

    Returns:
        Φ* usando la misma emd_efecto que GeoMIP en producción (D4-04).
    """
    dm_original = sistema.distribucion_marginal()
    todas_dims = list(sistema.dims_ncubos)
    N = len(sistema.ncubos)
    dist_recons = np.empty(N, dtype=np.float32)
    cubiertos: set[int] = set()

    for parte in particion:
        pi_global = frozenset(todas_dims[d] for d in parte if d < len(todas_dims))
        non_pi = np.array([g for g in todas_dims if g not in pi_global], dtype=np.int8)
        for d in parte:
            if d >= N:
                continue
            cubiertos.add(d)
            ncubo = sistema.ncubos[d]
            marg = ncubo.marginalizar(non_pi) if non_pi.size else ncubo
            if marg.dims.size:
                sub = tuple(int(sistema.estado_inicial[g]) for g in marg.dims)
                dist_recons[d] = 1.0 - float(marg.data[seleccionar_subestado(sub)])
            else:
                dist_recons[d] = 1.0 - float(marg.data)

    for d in range(N):
        if d not in cubiertos:
            ncubo = sistema.ncubos[d]
            non_all = np.array(todas_dims, dtype=np.int8)
            marg = ncubo.marginalizar(non_all)
            if marg.dims.size:
                sub = tuple(int(sistema.estado_inicial[g]) for g in marg.dims)
                dist_recons[d] = 1.0 - float(marg.data[seleccionar_subestado(sub)])
            else:
                dist_recons[d] = 1.0 - float(marg.data)

    return emd_efecto(dm_original, dist_recons)
