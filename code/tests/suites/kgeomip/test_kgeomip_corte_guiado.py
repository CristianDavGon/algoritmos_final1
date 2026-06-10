"""Tests para `estrategia_corte = "guiado_S"` en KGeoMIP (D4-05).

S propone candidatos de bipartición (afinidad cruzada ascendente), EMD
confirma el mejor. Cubre:

    - `_candidatos_por_afinidad`: ordenamiento y límite de candidatos.
    - `_mejor_corte` despacha según `self.estrategia_corte`.
    - `guiado_S` equivale a `exhaustivo` cuando |P| es pequeño (n=5).
    - Regresión k=2, monotonicidad y gap vs BruteForce con `guiado_S`.
    - A/B `exhaustivo` vs `guiado_S` para n=8 (bloques pueden superar el
      límite de candidatos).

Run via pytest (separate invocation, GeoMIP module only):
    pytest tests/suites/kgeomip/test_kgeomip_corte_guiado.py -v -s
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parents[2]
_CODE_ROOT = _TESTS_ROOT.parent
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"
if str(_GEOMIP_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOMIP_ROOT))

import numpy as np
import pytest

from .test_kgeomip import _bruteforce_phi_k, _full_mask, _make_kgeomip, _set_env


# --------------------------------------------------------------------------
# _candidatos_por_afinidad: ordenamiento y límite
# --------------------------------------------------------------------------

def test_candidatos_por_afinidad_ordena_por_afinidad_cruzada() -> None:
    """Bloques con baja afinidad cruzada deben ir primero."""
    from src.controllers.strategies.kgeomip import _candidatos_por_afinidad

    # Nodos 0,1 muy afines entre sí; nodos 2,3 muy afines entre sí;
    # afinidad cruzada {0,1}-{2,3} es baja -> debe ser el primer candidato.
    S = np.array([
        [10.0, 9.0, 1.0, 1.0],
        [9.0, 10.0, 1.0, 1.0],
        [1.0, 1.0, 10.0, 9.0],
        [1.0, 1.0, 9.0, 10.0],
    ])
    P = frozenset({0, 1, 2, 3})

    candidatos = _candidatos_por_afinidad(P, S, max_candidatos=20)

    # 2^(4-1) - 1 = 7 biparticiones posibles, todas <= 20 -> todas presentes
    assert len(candidatos) == 7

    A0, B0 = candidatos[0]
    assert {A0, B0} == {frozenset({0, 1}), frozenset({2, 3})}


def test_candidatos_por_afinidad_respeta_limite() -> None:
    """Para |P|=6 hay 31 biparticiones; el resultado se trunca a max_candidatos."""
    from src.controllers.strategies.kgeomip import _candidatos_por_afinidad

    n = 6
    rng = np.random.RandomState(42)
    S = rng.rand(n, n)
    S = (S + S.T) / 2.0
    P = frozenset(range(n))

    candidatos = _candidatos_por_afinidad(P, S, max_candidatos=20)
    assert len(candidatos) == 20


# --------------------------------------------------------------------------
# Dispatcher _mejor_corte y bandera estrategia_corte
# --------------------------------------------------------------------------

def test_estrategia_corte_default_exhaustivo() -> None:
    n = 5
    _set_env(n)
    kg = _make_kgeomip("10000")
    assert kg.estrategia_corte == "exhaustivo"


def test_mejor_corte_dispatcher_equivale_para_bloques_pequenos() -> None:
    """Para |P|<=5 (<=20 candidatos), guiado_S coincide exactamente con exhaustivo."""
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg = _make_kgeomip("10000")
    kg.aplicar_estrategia(mask, mask, mask, tpm, k=3)  # poblar self._S, self._dm_orig

    P = frozenset(range(len(kg.sia_subsistema.dims_ncubos)))
    assert len(P) <= 5

    kg.estrategia_corte = "exhaustivo"
    a_exh, b_exh, d_exh = kg._mejor_corte(P, kg._S)

    kg.estrategia_corte = "guiado_S"
    a_s, b_s, d_s = kg._mejor_corte(P, kg._S)

    assert {a_exh, b_exh} == {a_s, b_s}
    assert abs(d_exh - d_s) < 1e-9


# --------------------------------------------------------------------------
# guiado_S equivale a exhaustivo end-to-end para n=5 (bloques <= 5)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("k,estado", [
    (3, "10000"),
    (4, "10000"),
    (3, "11111"),
    (4, "11111"),
])
def test_guiado_S_equivale_exhaustivo_n5(k: int, estado: str) -> None:
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg_exh = _make_kgeomip(estado)
    sol_exh = kg_exh.aplicar_estrategia(
        mask, mask, mask, tpm, k=k, estrategia_corte="exhaustivo"
    )

    kg_s = _make_kgeomip(estado)
    sol_s = kg_s.aplicar_estrategia(
        mask, mask, mask, tpm, k=k, estrategia_corte="guiado_S"
    )

    assert abs(sol_exh.perdida - sol_s.perdida) < 1e-9, (
        f"k={k} estado={estado}: exhaustivo={sol_exh.perdida:.10f} "
        f"vs guiado_S={sol_s.perdida:.10f}"
    )


# --------------------------------------------------------------------------
# Regresión k=2 no afectada por estrategia_corte
# --------------------------------------------------------------------------

def test_regresion_k2_no_afectada_por_estrategia_corte() -> None:
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)
    estado = "10000"

    kg_exh = _make_kgeomip(estado)
    sol_exh = kg_exh.aplicar_estrategia(
        mask, mask, mask, tpm, k=2, estrategia_corte="exhaustivo"
    )

    kg_s = _make_kgeomip(estado)
    sol_s = kg_s.aplicar_estrategia(
        mask, mask, mask, tpm, k=2, estrategia_corte="guiado_S"
    )

    assert abs(sol_exh.perdida - sol_s.perdida) < 1e-9


# --------------------------------------------------------------------------
# Monotonicidad y gap vs BruteForce con guiado_S
# --------------------------------------------------------------------------

@pytest.mark.parametrize("estado", ["10000", "11111"])
def test_monotonicidad_guiado_S(estado: str) -> None:
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip(estado)

    phis = {}
    for k in range(1, 6):
        sol = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k, estrategia_corte="guiado_S")
        phis[k] = sol.perdida

    for k in range(1, 5):
        assert phis[k + 1] >= phis[k] - 1e-9, (
            f"Monotonicidad violada con guiado_S: φ({k+1})={phis[k+1]:.8f} "
            f"< φ({k})={phis[k]:.8f}"
        )


@pytest.mark.parametrize("k,estado", [
    (3, "10000"),
    (4, "11111"),
])
def test_gap_vs_bruteforce_guiado_S(k: int, estado: str) -> None:
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg = _make_kgeomip(estado)
    sol = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k, estrategia_corte="guiado_S")
    phi_opt = _bruteforce_phi_k(kg, k)

    gap = sol.perdida - phi_opt
    assert gap >= -1e-9, f"Gap negativo con guiado_S: {gap:.2e} para k={k}"


# --------------------------------------------------------------------------
# A/B exhaustivo vs guiado_S para n=8 (bloques pueden superar el límite)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("k", [3, 4])
def test_ab_exhaustivo_vs_guiado_S_n8(k: int) -> None:
    """Ambas estrategias deben producir phi >= phi(k=2) (no empeorar la cota inferior)."""
    n = 8
    mask = _full_mask(n)
    tpm = _set_env(n)
    estado = "10000000"

    kg_exh = _make_kgeomip(estado)
    sol_exh = kg_exh.aplicar_estrategia(mask, mask, mask, tpm, k=k, estrategia_corte="exhaustivo")

    kg_s = _make_kgeomip(estado)
    sol_s = kg_s.aplicar_estrategia(mask, mask, mask, tpm, k=k, estrategia_corte="guiado_S")

    print(
        f"\nA/B corte n=8 k={k}: "
        f"phi_exhaustivo={sol_exh.perdida:.6f}  phi_guiado_S={sol_s.perdida:.6f}"
    )

    assert sol_exh.perdida >= -1e-9
    assert sol_s.perdida >= -1e-9
