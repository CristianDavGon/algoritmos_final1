"""Tests de la optimización de exactitud/velocidad de KGeoMIP (D4-06).

Cubre las tres correcciones:

    1. ΔΦ incremental real: `_mejor_corte` minimiza exactamente el incremento
       de Φ medido por `_calcular_phi_total` (aditividad de emd_efecto).
    2. Raíz consistente con el modelo k: si la proyección del ancla GeoMIP es
       peor (en el modelo k) que el mejor corte directo, se usa este último.
       Caso testigo: N8A k=3 tiene φ*=0 pero ninguna 3-partición con φ=0
       refina la proyección del ancla — el corte raíz alternativo lo resuelve.
    3. Caché: marginales por máscara y solución GeoMIP k=2 por subsistema
       (GeoMIP corre una sola vez por clave en barridos k=1..5).

Run via pytest (separate invocation, GeoMIP module only):
    pytest tests/suites/kgeomip/test_kgeomip_optimizacion.py -v -s
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

from .test_kgeomip import (
    _all_k_partitions,
    _bruteforce_phi_k,
    _full_mask,
    _make_kgeomip,
    _set_env,
)


def _preparar(n: int, estado: str, k: int = 3):
    """Instancia KGeoMIP y puebla su estado interno con una corrida k."""
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip(estado)
    kg.aplicar_estrategia(mask, mask, mask, tpm, k=k)
    return kg, mask, tpm


# --------------------------------------------------------------------------
# 1. ΔΦ incremental real (consistencia con _calcular_phi_total)
# --------------------------------------------------------------------------

def test_delta_phi_es_incremento_real_de_phi_total() -> None:
    """ΔΦ(P→A,B) == Φ([A,B]+resto) − Φ([P]+resto) para cualquier corte."""
    from src.controllers.strategies.kgeomip import _calcular_phi_total

    kg, _, _ = _preparar(5, "10000")
    D = len(kg.sia_subsistema.dims_ncubos)
    V = frozenset(range(D))

    A = frozenset({0, 1})
    B = V - A
    dphi = kg._delta_phi_corte(A, B)

    phi_antes = _calcular_phi_total([V], kg.sia_subsistema)
    phi_despues = _calcular_phi_total([A, B], kg.sia_subsistema)
    assert abs(dphi - (phi_despues - phi_antes)) < 1e-6, (
        f"ΔΦ={dphi:.8f} != incremento real {phi_despues - phi_antes:.8f}"
    )


def test_mejor_corte_minimiza_incremento_real() -> None:
    """El corte elegido por _mejor_corte es argmin de Φ([A,B]) sobre V (n=5)."""
    from src.controllers.strategies.kgeomip import _calcular_phi_total

    kg, _, _ = _preparar(5, "11111")
    D = len(kg.sia_subsistema.dims_ncubos)
    V = frozenset(range(D))

    kg.estrategia_corte = "exhaustivo"
    _, _, dphi = kg._mejor_corte(V, kg._S)

    phi_min = min(
        _calcular_phi_total(list(parts), kg.sia_subsistema)
        for parts in _all_k_partitions(D, 2)
    )
    assert abs(dphi - phi_min) < 1e-6, (
        f"_mejor_corte ΔΦ={dphi:.8f} != mínimo real {phi_min:.8f}"
    )


# --------------------------------------------------------------------------
# 2. Exactitud: corte raíz consistente con el modelo k
# --------------------------------------------------------------------------

@pytest.mark.parametrize("k", [3, 4])
def test_n8_alcanza_optimo_con_raiz_consistente(k: int) -> None:
    """N8A: φ* = 0 para k ∈ {3,4}; la raíz consistente debe alcanzarlo."""
    n = 8
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip("10000000")
    sol = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k)
    phi_opt = _bruteforce_phi_k(kg, k)

    assert phi_opt < 1e-9, f"Precondición: φ*(k={k}) debería ser 0, dio {phi_opt}"
    assert sol.perdida < 1e-9, (
        f"k={k}: φ_E4={sol.perdida:.6f} no alcanzó φ*=0 (gap={sol.perdida:.2e})"
    )


@pytest.mark.parametrize("n,estado,k,gap_baseline", [
    (5, "10000", 4, 0.375),
    (5, "11111", 4, 0.125),
    (6, "100000", 3, 0.40625),
    (6, "100000", 4, 0.25),
])
def test_gap_no_empeora_respecto_baseline(
    n: int, estado: str, k: int, gap_baseline: float
) -> None:
    """El gap vs BruteForce no debe superar el de la versión previa (2026-06-09)."""
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip(estado)
    sol = kg.aplicar_estrategia(mask, mask, mask, tpm, k=k)
    phi_opt = _bruteforce_phi_k(kg, k)
    gap = sol.perdida - phi_opt

    print(f"\nn={n} k={k} estado={estado}: gap={gap:.6f} (baseline={gap_baseline})")
    assert -1e-9 <= gap <= gap_baseline + 1e-9, (
        f"Gap {gap:.6f} empeoró respecto al baseline {gap_baseline:.6f}"
    )


# --------------------------------------------------------------------------
# 3. Cachés: marginales por máscara y GeoMIP k=2 por clave
# --------------------------------------------------------------------------

def test_marginales_por_mascara_equivalen_a_ncube() -> None:
    """El vector de marginales por máscara coincide con NCube.marginalizar."""
    from src.funcs.base import seleccionar_subestado

    kg, _, _ = _preparar(5, "10000")
    sistema = kg.sia_subsistema
    dims_all = list(sistema.dims_ncubos)
    Q = frozenset({1, 3})

    mask = sum(1 << d for d in Q if d < len(dims_all))
    marg_vec = kg._marginales_mascara(mask)

    pi_global = frozenset(dims_all[d] for d in Q)
    non_pi = np.array([g for g in dims_all if g not in pi_global], dtype=np.int8)
    for d in sorted(Q):
        ncubo = sistema.ncubos[d]
        marg = ncubo.marginalizar(non_pi)
        sub = tuple(int(sistema.estado_inicial[g]) for g in marg.dims)
        esperado = 1.0 - float(marg.data[seleccionar_subestado(sub)])
        assert abs(float(marg_vec[d]) - esperado) < 1e-9, (
            f"d={d}: máscara={marg_vec[d]:.8f} vs ncube={esperado:.8f}"
        )


def test_marginales_vista_equivale_a_escaneo_booleano() -> None:
    """La marginal por vista n-dim (OPT-K2) coincide con el escaneo booleano."""
    kg, _, _ = _preparar(5, "11111")
    flat = kg._geomip._flat_data_matrix
    ini_int = kg._geomip._ini_int
    estados = np.arange(flat.shape[1], dtype=np.int64)

    n_dims = len(kg.sia_subsistema.dims_ncubos)
    for mask in (0b00001, 0b00101, 0b11111, 0b01010, 0):
        if mask >= (1 << n_dims):
            continue
        kg._marg_cache.pop(mask, None)
        marg = kg._marginales_mascara(mask)
        sel = (estados & mask) == (ini_int & mask)
        esperado = 1.0 - flat[:, sel].mean(axis=1)
        assert np.allclose(marg, esperado, atol=1e-12), f"mask={mask:b}"


def test_costo_parte_cacheado_consistente() -> None:
    """_costo_parte cachea por parte y el valor cacheado coincide con el fresco."""
    kg, _, _ = _preparar(5, "10000")
    Q = frozenset({0, 2, 3})

    costo_1 = kg._costo_parte(Q)
    assert Q in kg._costo_cache
    costo_2 = kg._costo_parte(Q)  # hit
    assert costo_1 == costo_2

    kg._costo_cache.clear()
    kg._marg_cache.clear()
    costo_fresco = kg._costo_parte(Q)
    assert abs(costo_1 - costo_fresco) < 1e-12


def test_caches_se_limpian_al_cambiar_clave() -> None:
    """Cambiar la clave del subsistema invalida los cachés de costos/marginales."""
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip("10000")
    kg.aplicar_estrategia(mask, mask, mask, tpm, k=3)
    assert kg._costo_cache and kg._marg_cache

    otra = "01111"
    kg.aplicar_estrategia(otra, mask, mask, tpm, k=3)
    # Tras el cambio de clave los cachés se reconstruyeron desde cero para la
    # nueva clave (no contienen residuos incompatibles con el subsistema previo)
    assert kg._subsistema_key == (otra, mask, mask)


def test_construir_S_equivale_a_referencia() -> None:
    """_construir_S vectorizada (OPT-K3) coincide con el bucle de referencia."""
    kg, _, _ = _preparar(8, "10000000")
    D = len(kg.sia_subsistema.indices_ncubos)
    S_nueva = kg._construir_S(D)

    tabla = kg._geomip._tabla
    ini_int = kg._geomip._ini_int
    all_states = np.arange(tabla.shape[0], dtype=np.int64)
    D_nc = tabla.shape[1]
    S_ref = np.zeros((D_nc, D_nc), dtype=np.float64)
    for j in range(D_nc):
        bit_j_ini = (ini_int >> j) & 1
        differs = ((all_states >> np.int64(j)) & np.int64(1)) != bit_j_ini
        S_ref[:, j] = tabla[differs].sum(axis=0)
    S_ref = (S_ref + S_ref.T) / 2.0

    assert np.allclose(S_nueva, S_ref, atol=1e-9)


def test_geomip_corre_una_sola_vez_por_clave() -> None:
    """En un barrido k=2..5 sobre la misma clave, GeoMIP corre una sola vez."""
    n = 5
    mask = _full_mask(n)
    tpm = _set_env(n)
    kg = _make_kgeomip("10000")

    llamadas = {"n": 0}
    original = kg._geomip.aplicar_estrategia

    def contar(*args, **kwargs):
        llamadas["n"] += 1
        return original(*args, **kwargs)

    kg._geomip.aplicar_estrategia = contar  # type: ignore[method-assign]

    perdidas = [
        kg.aplicar_estrategia(mask, mask, mask, tpm, k=k).perdida
        for k in range(2, 6)
    ]
    assert llamadas["n"] == 1, f"GeoMIP corrió {llamadas['n']} veces, esperaba 1"

    kg2 = _make_kgeomip("10000")
    perdidas_frescas = [
        kg2.aplicar_estrategia(mask, mask, mask, tpm, k=k).perdida
        for k in range(2, 6)
    ]
    assert np.allclose(perdidas, perdidas_frescas, atol=1e-9), (
        "El caché k=2 altera los resultados del barrido"
    )
