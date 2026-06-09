"""Tests de KGeoMIP: regresión k=2, monotonicidad, gap vs BruteForce y A/B E4 vs A.

DoD criteria covered:
    C1  — Regresión k=2 == GeoMIP (tolerancia 1e-9)
    C2  — Monotonicidad φ(k+1) ≥ φ(k) para k ∈ {1,2,3,4}
    C3/C4 — Gap vs BruteForce ≥ 0 para k ∈ {3,4}, n ≤ 6
    C5  — Tasa de acierto exacto KGeoMIP vs BruteForce k-partición
    C6  — A/B testing E4 vs Estrategia A: gap medio y % acierto

Run standalone (from code/ directory):
    python tests/suites/kgeomip/test_kgeomip.py

Run via pytest (separate invocation, GeoMIP module only):
    pytest tests/suites/kgeomip/test_kgeomip.py -v -s
"""
from __future__ import annotations

import os
import sys
from itertools import product as itertools_product
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parents[2]
_CODE_ROOT = _TESTS_ROOT.parent
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"
if str(_GEOMIP_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOMIP_ROOT))

import numpy as np
import pytest

# --------------------------------------------------------------------------
# Helpers de infraestructura
# --------------------------------------------------------------------------

def _set_env(n: int, pagina: str = "A") -> np.ndarray:
    """Configura GeoMIP, carga TPM y retorna la matriz."""
    from src.models.base.application import aplicacion  # noqa: PLC0415
    aplicacion.pagina_sample_network = pagina
    aplicacion.profiler_habilitado = False

    candidates = (
        _GEOMIP_ROOT / "data" / "samples" / f"N{n}{pagina}.csv",
        _GEOMIP_ROOT / "src" / ".samples" / f"N{n}{pagina}.csv",
    )
    for c in candidates:
        if c.exists():
            os.environ["GEOMIP_SAMPLES_DIR"] = str(c.parent)
            return np.genfromtxt(c, delimiter=",")
    raise FileNotFoundError(f"N{n}{pagina}.csv no encontrado")


def _make_kgeomip(estado: str):
    """Crea KGeoMIP con Manager usando `estado` como estado inicial."""
    from src.controllers.manager import Manager  # noqa: PLC0415
    from src.controllers.strategies.kgeomip import KGeoMIP  # noqa: PLC0415
    return KGeoMIP(Manager(estado_inicial=estado))


def _make_geomip(estado: str):
    """Crea GeometricSIA con Manager."""
    from src.controllers.manager import Manager  # noqa: PLC0415
    from src.controllers.strategies.geometric import GeometricSIA  # noqa: PLC0415
    return GeometricSIA(Manager(estado_inicial=estado))


def _full_mask(n: int) -> str:
    return "1" * n


def _all_k_partitions(n: int, k: int):
    """Genera todas las k-particiones canónicas de {0,..,n-1}.

    Usa cadenas de crecimiento restringido (restricted growth strings).
    Para n=5, k=3: 25 particiones. Para n=6, k=4: 65 particiones.
    """
    if k > n or k < 1:
        return

    # _rgs(i, max_used): max_used = highest group label assigned so far.
    # Element i can join any existing group 0..max_used OR start group max_used+1.
    # Hence range(min(max_used + 2, k)): +1 for new-group option, range() excludes end.
    def _rgs(i: int, max_used: int):
        if i == n:
            yield ()
            return
        for val in range(min(max_used + 2, k)):
            for rest in _rgs(i + 1, max(max_used, val)):
                yield (val,) + rest

    for rest in _rgs(1, 0):
        assignment = (0,) + rest
        if len(set(assignment)) == k:
            yield [frozenset(i for i in range(n) if assignment[i] == g) for g in range(k)]


def _bruteforce_phi_k(kg, k: int) -> float:
    """φ* óptimo para k-partición por búsqueda exhaustiva."""
    from src.controllers.strategies.kgeomip import _calcular_phi_total  # noqa: PLC0415
    n = len(kg.sia_subsistema.dims_ncubos)
    best = float("inf")
    for parts in _all_k_partitions(n, k):
        phi = _calcular_phi_total(parts, kg.sia_subsistema)
        if phi < best:
            best = phi
    return best


# --------------------------------------------------------------------------
# C1 — Regresión k=2: KGeoMIP(k=2) == GeoMIP exactamente
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n,estado", [
    (5, "10000"),
    (5, "11111"),
    (8, "10000000"),
])
def test_regresion_k2_igual_geomip(n: int, estado: str) -> None:
    """KGeoMIP(k=2).perdida debe ser idéntica a GeoMIP.perdida (C1, tolerancia 1e-9)."""
    mask = _full_mask(n)
    tpm = _set_env(n)

    geo = _make_geomip(estado)
    sol_geo = geo.aplicar_estrategia(mask, mask, mask, tpm)

    kg = _make_kgeomip(estado)
    sol_kg2 = kg.aplicar_estrategia(mask, mask, mask, tpm, k=2)

    assert abs(sol_kg2.perdida - sol_geo.perdida) < 1e-9, (
        f"n={n} estado={estado}: KGeoMIP(k=2)={sol_kg2.perdida:.10f} "
        f"vs GeoMIP={sol_geo.perdida:.10f} Δ={abs(sol_kg2.perdida-sol_geo.perdida):.2e}"
    )


# --------------------------------------------------------------------------
# C2 — Monotonicidad: φ(k+1) ≥ φ(k) para k ∈ {1,2,3,4}
# --------------------------------------------------------------------------

_MONO_TOL = 1e-9

@pytest.mark.parametrize("n,estado", [
    (5, "10000"),
    (5, "11111"),
])
def test_monotonicidad_creciente(n: int, estado: str) -> None:
    """φ(k+1) ≥ φ(k) − ε para k ∈ {1,2,3,4}: más particiones = mayor EMD (C2)."""
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip(estado)

    phis = {}
    for k in range(1, 6):
        sol = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k)
        phis[k] = sol.perdida

    for k in range(1, 5):
        assert phis[k + 1] >= phis[k] - _MONO_TOL, (
            f"Monotonicidad violada: φ({k+1})={phis[k+1]:.8f} < φ({k})={phis[k]:.8f} "
            f"(Δ={phis[k]-phis[k+1]:.2e}) para n={n} estado={estado}"
        )


# --------------------------------------------------------------------------
# C3/C4/C5 — Gap vs BruteForce k-partición: n ≤ 6
# --------------------------------------------------------------------------

@pytest.mark.parametrize("k,estado", [
    (3, "10000"),
    (3, "11111"),
    (4, "10000"),
    (4, "11111"),
])
def test_gap_vs_bruteforce(k: int, estado: str) -> None:
    """φ_E4 − φ* ≥ 0: E4 no puede dar valor menor al óptimo (C3/C4).

    Adicionalmente reporta tasa de acierto exacto (C5) en la salida.
    """
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg = _make_kgeomip(estado)
    sol_e4 = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k)

    phi_e4 = sol_e4.perdida
    phi_opt = _bruteforce_phi_k(kg, k)

    gap = phi_e4 - phi_opt
    acierto_exacto = gap < 1e-9

    print(
        f"\nn={n} k={k} estado={estado}: "
        f"phi_E4={phi_e4:.6f}  phi*={phi_opt:.6f}  gap={gap:.2e}  "
        f"exacto={'SI' if acierto_exacto else 'NO'}"
    )

    assert gap >= -1e-9, (
        f"Gap negativo: φ_E4={phi_e4:.8f} < φ*={phi_opt:.8f} "
        f"(gap={gap:.2e}) para k={k} n={n} estado={estado}"
    )


# --------------------------------------------------------------------------
# C6 — A/B testing E4 vs Estrategia A
# --------------------------------------------------------------------------

@pytest.mark.parametrize("k,estado", [
    (3, "10000"),
    (4, "10000"),
])
def test_ab_e4_vs_estrategia_a(k: int, estado: str) -> None:
    """E4 y Estrategia A son válidas (gap ≥ 0); reporta cuál tiene menor gap (C6)."""
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)

    kg_e4 = _make_kgeomip(estado)
    sol_e4 = kg_e4.aplicar_estrategia(mask, mask, mask, tpm, k=k, variante="E4")
    phi_opt = _bruteforce_phi_k(kg_e4, k)

    kg_a = _make_kgeomip(estado)
    sol_a = kg_a.aplicar_estrategia(mask, mask, mask, tpm, k=k, variante="A")

    gap_e4 = sol_e4.perdida - phi_opt
    gap_a = sol_a.perdida - phi_opt

    print(
        f"\nA/B k={k} estado={estado}: "
        f"gap_E4={gap_e4:.6f}  gap_A={gap_a:.6f}  "
        f"ganador={'E4' if gap_e4 <= gap_a else 'A'}"
    )

    assert gap_e4 >= -1e-9, (
        f"E4 gap negativo: {gap_e4:.2e} para k={k}"
    )
    assert gap_a >= -1e-9, (
        f"Estrategia A gap negativo: {gap_a:.2e} para k={k}"
    )


# --------------------------------------------------------------------------
# Smoke test: k=1 devuelve φ=0
# --------------------------------------------------------------------------

def test_k1_phi_cero() -> None:
    """k=1 = sin partición → EMD=0 (sistema unificado)."""
    n = 5
    tpm = _set_env(n)
    kg = _make_kgeomip("10000")
    sol = kg.aplicar_estrategia(_full_mask(n), _full_mask(n), _full_mask(n), tpm, k=1)
    assert sol.perdida == 0.0, f"k=1 debe ser φ=0, got {sol.perdida}"


# --------------------------------------------------------------------------
# Punto de entrada standalone
# --------------------------------------------------------------------------

if __name__ == "__main__":
    for n, estado in [(5, "10000"), (5, "11111"), (8, "10000000")]:
        _set_env(n)
        mask = _full_mask(n)
        tpm = np.genfromtxt(
            next(
                p for p in (
                    _GEOMIP_ROOT / "data" / "samples" / f"N{n}A.csv",
                    _GEOMIP_ROOT / "src" / ".samples" / f"N{n}A.csv",
                ) if p.exists()
            ),
            delimiter=",",
        )

        geo = _make_geomip(estado)
        phi_geo = geo.aplicar_estrategia(mask, mask, mask, tpm).perdida

        kg = _make_kgeomip(estado)
        phis = {}
        for k in range(1, 6):
            phis[k] = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k).perdida

        print(f"\n=== n={n} estado={estado} ===")
        print(f"  GeoMIP(k=2) φ = {phi_geo:.6f}")
        for k, phi in phis.items():
            match = " OK (regression)" if k == 2 and abs(phi - phi_geo) < 1e-9 else ""
            print(f"  KGeoMIP(k={k}) phi = {phi:.6f}{match}")
        print(f"  Monotonicidad: {all(phis[k+1] >= phis[k] - 1e-9 for k in range(1, 5))}")
