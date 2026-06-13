"""Tests para `estrategia_corte = "auto"` y candidatos no exponenciales (OPT-K1).

El modo "auto" despacha por tamaño de bloque: exhaustivo cuando el número de
biparticiones (2^(|P|-1) - 1) no supera `_UMBRAL_EXHAUSTIVO`, guiado_S cuando
sí. `_candidatos_por_afinidad` deja de enumerar las 2^(m-1) biparticiones para
bloques grandes: usa generación constructiva O(m²) por semillas de mínima
afinidad y cortes de prefijo.

Cubre:
    - Default "auto" y despacho por tamaño de bloque.
    - "auto" ≡ "exhaustivo" end-to-end para n ∈ {5, 8} (bloques pequeños).
    - Scoring vectorizado ≡ scoring naive para bloques pequeños.
    - Generación constructiva: validez, límite y separación de clusters.

Run via pytest (separate invocation, GeoMIP module only):
    pytest tests/suites/kgeomip/test_kgeomip_corte_auto.py -v -s
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parents[2]
_CODE_ROOT = _TESTS_ROOT.parent
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"
if str(_GEOMIP_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOMIP_ROOT))

import numpy as np
import pytest

from .test_kgeomip import _full_mask, _make_kgeomip, _set_env


def _score_naive(A: frozenset[int], B: frozenset[int], S: np.ndarray) -> float:
    """Afinidad cruzada media, implementación de referencia (pre-OPT-K1)."""
    return float(S[np.ix_(sorted(A), sorted(B))].mean())


# --------------------------------------------------------------------------
# Default "auto" y despacho por tamaño
# --------------------------------------------------------------------------

def test_estrategia_corte_default_auto() -> None:
    n = 5
    _set_env(n)
    kg = _make_kgeomip("10000")
    assert kg.estrategia_corte == "auto"


def test_auto_coincide_con_exhaustivo_en_bloque_pequeno() -> None:
    """Bloques con 2^(|P|-1)-1 <= umbral deben resolverse igual que exhaustivo."""
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg = _make_kgeomip("10000")
    kg.aplicar_estrategia(mask, mask, mask, tpm, k=3)  # poblar _S y _dm_orig

    P = frozenset(range(len(kg.sia_subsistema.dims_ncubos)))

    kg.estrategia_corte = "exhaustivo"
    a_exh, b_exh, d_exh = kg._mejor_corte(P, kg._S)

    kg.estrategia_corte = "auto"
    a_auto, b_auto, d_auto = kg._mejor_corte(P, kg._S)

    assert {a_exh, b_exh} == {a_auto, b_auto}
    assert abs(d_exh - d_auto) < 1e-9


# --------------------------------------------------------------------------
# "auto" ≡ "exhaustivo" end-to-end (todos los bloques de n<=8 son pequeños)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n,estado", [(5, "10000"), (5, "11111"), (8, "10000000")])
@pytest.mark.parametrize("k", [3, 4, 5])
def test_auto_equivale_exhaustivo_end_to_end(n: int, estado: str, k: int) -> None:
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg_exh = _make_kgeomip(estado)
    sol_exh = kg_exh.aplicar_estrategia(
        mask, mask, mask, tpm, k=k, estrategia_corte="exhaustivo"
    )

    kg_auto = _make_kgeomip(estado)
    sol_auto = kg_auto.aplicar_estrategia(
        mask, mask, mask, tpm, k=k, estrategia_corte="auto"
    )

    assert abs(sol_exh.perdida - sol_auto.perdida) < 1e-9, (
        f"n={n} k={k} estado={estado}: exhaustivo={sol_exh.perdida:.10f} "
        f"vs auto={sol_auto.perdida:.10f}"
    )


# --------------------------------------------------------------------------
# Scoring vectorizado ≡ naive (bloques pequeños)
# --------------------------------------------------------------------------

def test_candidatos_scoring_vectorizado_equivale_naive() -> None:
    """El orden por afinidad debe coincidir con el cálculo naive de referencia."""
    from src.controllers.strategies.kgeomip import _candidatos_por_afinidad

    m = 7
    rng = np.random.RandomState(73)
    S = rng.rand(m, m)
    S = (S + S.T) / 2.0
    P = frozenset(range(m))

    candidatos = _candidatos_por_afinidad(P, S, max_candidatos=2 ** (m - 1))

    assert len(candidatos) == 2 ** (m - 1) - 1
    scores = [_score_naive(A, B, S) for A, B in candidatos]
    assert all(scores[i] <= scores[i + 1] + 1e-12 for i in range(len(scores) - 1))
    # Todas son biparticiones válidas de P, sin repetidos
    vistos = set()
    for A, B in candidatos:
        assert A and B and not (A & B) and (A | B) == P
        clave = frozenset((A, B))
        assert clave not in vistos
        vistos.add(clave)


def test_candidatos_subconjunto_global() -> None:
    """P con índices globales no contiguos: candidatos válidos sobre esos índices."""
    from src.controllers.strategies.kgeomip import _candidatos_por_afinidad

    D = 9
    rng = np.random.RandomState(11)
    S = rng.rand(D, D)
    S = (S + S.T) / 2.0
    P = frozenset({1, 3, 4, 7, 8})

    candidatos = _candidatos_por_afinidad(P, S, max_candidatos=20)
    assert len(candidatos) == 2 ** (len(P) - 1) - 1
    for A, B in candidatos:
        assert (A | B) == P and not (A & B)


# --------------------------------------------------------------------------
# Generación constructiva para bloques grandes (sin enumeración 2^m)
# --------------------------------------------------------------------------

def test_candidatos_bloque_grande_validos_y_acotados() -> None:
    """|P|=18: 2^17 biparticiones; el constructivo debe retornar pocos y válidos."""
    from src.controllers.strategies.kgeomip import _candidatos_por_afinidad

    m = 18
    rng = np.random.RandomState(7)
    S = rng.rand(m, m)
    S = (S + S.T) / 2.0
    P = frozenset(range(m))

    t0 = time.perf_counter()
    candidatos = _candidatos_por_afinidad(P, S, max_candidatos=20)
    dt = time.perf_counter() - t0

    assert 1 <= len(candidatos) <= 20
    for A, B in candidatos:
        assert A and B and not (A & B) and (A | B) == P
    # Sin enumeración exponencial esto corre en milisegundos
    assert dt < 1.0, f"Generación constructiva tardó {dt:.3f}s — ¿enumeración 2^m?"


def test_candidatos_bloque_grande_separa_clusters() -> None:
    """Con dos clusters de afinidad clara, el mejor candidato debe separarlos."""
    from src.controllers.strategies.kgeomip import _candidatos_por_afinidad

    m = 16
    S = np.full((m, m), 1.0)
    c1 = list(range(8))
    c2 = list(range(8, 16))
    S[np.ix_(c1, c1)] = 10.0
    S[np.ix_(c2, c2)] = 10.0
    np.fill_diagonal(S, 10.0)
    P = frozenset(range(m))

    candidatos = _candidatos_por_afinidad(P, S, max_candidatos=20)
    A0, B0 = candidatos[0]
    assert {A0, B0} == {frozenset(c1), frozenset(c2)}
