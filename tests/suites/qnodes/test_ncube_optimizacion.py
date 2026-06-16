"""Tests de la optimización transversal de la capa TPM/NCube en QNodes (D5-01).

QNodes ya memoizaba `marginalizar()` con clave `tuple(ejes)`; esta
optimización canoniza la clave por máscara de bits (ejes ∩ dims) y cachea
la instancia NCube completa:

    - ejes equivalentes (orden distinto, elementos fuera de dims) comparten
      entrada de memo en vez de duplicarla (tiempo y memoria);
    - el hit devuelve la misma instancia, reutilizando también su memo hijo
      en cadenas incrementales (Queyranne crece conjuntos de a un elemento).

Garantía de fidelidad: bit a bit idéntico a la referencia np.mean directa,
y regresión end-to-end contra golden pre-optimización (2026-06-12, 1e-9).

Run via pytest (separate invocation, QNodes module only):
    pytest tests/suites/qnodes/test_ncube_optimizacion.py -v -s
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

_TESTS_ROOT = Path(__file__).resolve().parents[2]
_CODE_ROOT = _TESTS_ROOT.parent
_QNODES_ROOT = _CODE_ROOT / "QNodes"
if str(_QNODES_ROOT) not in sys.path:
    sys.path.insert(0, str(_QNODES_ROOT))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _make_ncube(n: int, semilla: int = 42):
    """Crea un NCube n-dimensional con datos aleatorios reproducibles."""
    from src.models.core.ncube import NCube  # noqa: PLC0415
    rng = np.random.default_rng(semilla)
    return NCube(
        indice=0,
        dims=np.arange(n, dtype=np.int8),
        data=rng.random((2,) * n),
    )


def _referencia_marginalizar(cubo, ejes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Implementación de referencia (lógica original pre-optimización)."""
    marginable_axis = np.intersect1d(ejes, cubo.dims)
    if not marginable_axis.size:
        return cubo.data, cubo.dims
    numero_dims = cubo.dims.size - 1
    ejes_locales = tuple(
        numero_dims - dim_idx
        for dim_idx, axis in enumerate(cubo.dims)
        if axis in marginable_axis
    )
    new_dims = np.array(
        [d for d in cubo.dims if d not in marginable_axis], dtype=np.int8
    )
    return np.mean(cubo.data, axis=ejes_locales, keepdims=False), new_dims


def _cargar_tpm(n: int, pagina: str = "A") -> np.ndarray:
    ruta = _QNODES_ROOT / "src" / ".samples" / f"N{n}{pagina}.csv"
    if not ruta.exists():
        raise FileNotFoundError(str(ruta))
    return np.genfromtxt(ruta, delimiter=",")


def _set_env() -> None:
    from src.models.base.application import aplicacion  # noqa: PLC0415
    aplicacion.set_pagina_red_muestra("A")
    aplicacion.desactivar_profiling()


# --------------------------------------------------------------------------
# 1. Fidelidad: marginalizar() == referencia np.mean, bit a bit
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n", [3, 5, 8])
def test_marginalizar_identico_a_referencia(n: int) -> None:
    """Todo subconjunto de ejes produce datos/dims idénticos a la referencia."""
    cubo = _make_ncube(n)
    universo = list(range(n))
    for r in range(1, n + 1):
        for ejes in combinations(universo, r):
            ejes_arr = np.array(ejes, dtype=np.int8)
            esperado_data, esperado_dims = _referencia_marginalizar(cubo, ejes_arr)
            resultado = cubo.marginalizar(ejes_arr)
            assert np.array_equal(resultado.data, esperado_data), (
                f"n={n} ejes={ejes}: data difiere de la referencia"
            )
            assert np.array_equal(resultado.dims, esperado_dims), (
                f"n={n} ejes={ejes}: dims difiere de la referencia"
            )


def test_marginalizar_ejes_inexistentes_retorna_self() -> None:
    """Ejes sin intersección con dims devuelven el mismo cubo (sin copia)."""
    cubo = _make_ncube(4)
    reducido = cubo.marginalizar(np.array([0, 1], dtype=np.int8))
    assert reducido.marginalizar(np.array([0, 1], dtype=np.int8)) is reducido


# --------------------------------------------------------------------------
# 2. Clave canónica por máscara (OPT-B sobre el memo existente)
# --------------------------------------------------------------------------

def test_memo_hit_devuelve_misma_instancia() -> None:
    """El hit de memo devuelve la misma instancia (antes construía una nueva)."""
    cubo = _make_ncube(5)
    ejes = np.array([1, 3], dtype=np.int8)
    assert cubo.marginalizar(ejes) is cubo.marginalizar(ejes)


def test_clave_canonica_unifica_ejes_equivalentes() -> None:
    """Orden distinto y ejes fuera de dims comparten entrada de memo."""
    cubo = _make_ncube(5)
    a = cubo.marginalizar(np.array([1, 3], dtype=np.int8))
    b = cubo.marginalizar(np.array([3, 1], dtype=np.int8))
    c = cubo.marginalizar(np.array([1, 3, 7], dtype=np.int8))  # 7 ∉ dims
    assert a is b, "Orden distinto de ejes no comparte memo"
    assert a is c, "Ejes fuera de dims no comparten memo"
    assert len(cubo.memo) == 1, f"Memo tiene {len(cubo.memo)} entradas, esperaba 1"


# --------------------------------------------------------------------------
# 3. Regresión end-to-end contra golden pre-optimización (2026-06-12)
# --------------------------------------------------------------------------

_GOLDEN_QNODES = [
    (5, "10000", 0.0, "⎛ D ⎞⎛  A,B,C,E  ⎞\n⎝ ∅ ⎠⎝ a,b,c,d,e ⎠"),
    (8, "10000000", 0.0, "⎛ H ⎞⎛ A,B,C,D,E,F,G ⎞\n⎝ a ⎠⎝ b,c,d,e,f,g,h ⎠"),
    (8, "11111111", 0.0, "⎛ H ⎞⎛ A,B,C,D,E,F,G ⎞\n⎝ a ⎠⎝ b,c,d,e,f,g,h ⎠"),
]

_GOLDEN_KQNODES = [
    (5, "10000", [0.0, 2.125, 2.125, 2.125]),
    (8, "10000000", [0.0, 2.0, 3.0, 4.0]),
]


@pytest.mark.parametrize("n,estado,phi_golden,particion_golden", _GOLDEN_QNODES)
def test_regresion_qnodes_golden(
    n: int, estado: str, phi_golden: float, particion_golden: str
) -> None:
    """QNodes reproduce φ y partición pre-optimización (tolerancia 1e-9)."""
    from src.strategies.qnodes import QNodes  # noqa: PLC0415
    _set_env()
    tpm = _cargar_tpm(n)
    mask = "1" * n
    sol = QNodes(tpm).aplicar_estrategia(estado, mask, mask, mask)
    assert abs(float(sol.perdida) - phi_golden) < 1e-9
    assert sol.particion == particion_golden


@pytest.mark.parametrize("n,estado,perdidas_golden", _GOLDEN_KQNODES)
def test_regresion_kqnodes_golden(
    n: int, estado: str, perdidas_golden: list[float]
) -> None:
    """KQNodes k=2..5 reproduce las φ pre-optimización (tolerancia 1e-9)."""
    from src.strategies.kqnodes import KQNodes  # noqa: PLC0415
    _set_env()
    tpm = _cargar_tpm(n)
    mask = "1" * n
    kq = KQNodes(tpm)
    perdidas = [
        float(kq.aplicar_estrategia(estado, mask, mask, mask, k=k).perdida)
        for k in range(2, 6)
    ]
    assert np.allclose(perdidas, perdidas_golden, rtol=0, atol=1e-9), (
        f"n={n}: {perdidas} != golden {perdidas_golden}"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-s"]))
