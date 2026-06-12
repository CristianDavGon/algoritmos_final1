"""Tests de la optimización transversal de la capa TPM/NCube en GeoMIP (D5-01).

Cubre las tres optimizaciones:

    OPT-A — Memoización de `NCube.marginalizar()` (portada desde QNodes):
            llamadas repetidas devuelven la MISMA instancia (hit de caché).
    OPT-B — Clave canónica por máscara de bits (ejes ∩ dims): ejes
            equivalentes (orden distinto, elementos fuera de dims) comparten
            entrada de memo; reemplaza np.intersect1d por aritmética O(1).
    OPT-C — Memoización de `System.bipartir()` (portada desde QNodes).

Garantía de fidelidad: resultados bit a bit idénticos a la referencia
np.mean directa, y regresión end-to-end contra valores golden capturados
ANTES de la optimización (2026-06-12, tolerancia 1e-9 del proyecto).

Run via pytest (separate invocation, GeoMIP module only):
    pytest tests/suites/geomip/test_ncube_optimizacion.py -v -s
"""
from __future__ import annotations

import os
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

_TESTS_ROOT = Path(__file__).resolve().parents[2]
_CODE_ROOT = _TESTS_ROOT.parent
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"
if str(_GEOMIP_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOMIP_ROOT))


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


def test_marginalizar_encadenado_equivale_a_conjunto() -> None:
    """marginalizar({a,b}) == marginalizar({a}).marginalizar({b})."""
    cubo = _make_ncube(6)
    junto = cubo.marginalizar(np.array([1, 4], dtype=np.int8))
    encadenado = cubo.marginalizar(np.array([1], dtype=np.int8)).marginalizar(
        np.array([4], dtype=np.int8)
    )
    assert np.allclose(junto.data, encadenado.data, rtol=0, atol=1e-15)
    assert np.array_equal(junto.dims, encadenado.dims)


def test_condicionar_no_cambia(n: int = 5) -> None:
    """condicionar() conserva su comportamiento (vista, dims correctas)."""
    cubo = _make_ncube(n)
    estado = np.array([1, 0, 1, 0, 1], dtype=np.int8)
    cond = cubo.condicionar(np.array([2], dtype=np.int8), estado)
    assert np.array_equal(cond.dims, np.array([0, 1, 3, 4], dtype=np.int8))
    seleccion = [slice(None)] * n
    seleccion[n - 3] = 1
    assert np.array_equal(cond.data, cubo.data[tuple(seleccion)])


# --------------------------------------------------------------------------
# 2. OPT-A/OPT-B: memoización con clave canónica en NCube
# --------------------------------------------------------------------------

def test_memo_hit_devuelve_misma_instancia() -> None:
    """Dos llamadas con los mismos ejes devuelven la misma instancia (OPT-A)."""
    cubo = _make_ncube(5)
    ejes = np.array([1, 3], dtype=np.int8)
    assert cubo.marginalizar(ejes) is cubo.marginalizar(ejes)


def test_clave_canonica_unifica_ejes_equivalentes() -> None:
    """Orden distinto y ejes fuera de dims comparten entrada de memo (OPT-B)."""
    cubo = _make_ncube(5)
    a = cubo.marginalizar(np.array([1, 3], dtype=np.int8))
    b = cubo.marginalizar(np.array([3, 1], dtype=np.int8))
    c = cubo.marginalizar(np.array([1, 3, 7], dtype=np.int8))  # 7 ∉ dims
    assert a is b, "Orden distinto de ejes no comparte memo"
    assert a is c, "Ejes fuera de dims no comparten memo"
    assert len(cubo.memo) == 1, f"Memo tiene {len(cubo.memo)} entradas, esperaba 1"


def test_memo_es_seguro_por_inmutabilidad() -> None:
    """El cubo memoizado es frozen: no se puede mutar la referencia compartida."""
    cubo = _make_ncube(4)
    marg = cubo.marginalizar(np.array([0], dtype=np.int8))
    with pytest.raises(Exception):
        marg.indice = 99  # type: ignore[misc]


# --------------------------------------------------------------------------
# 3. OPT-C: memoización de System.bipartir
# --------------------------------------------------------------------------

def test_bipartir_memoiza_por_clave() -> None:
    """Dos biparticiones idénticas comparten el tuple de ncubos (OPT-C)."""
    from src.models.core.system import System  # noqa: PLC0415
    tpm = _set_env(5)
    sistema = System(tpm, np.array([1, 0, 0, 0, 0], dtype=np.int8))
    alcance = np.array([0, 1], dtype=np.int8)
    mecanismo = np.array([2, 3], dtype=np.int8)
    b1 = sistema.bipartir(alcance, mecanismo)
    b2 = sistema.bipartir(alcance, mecanismo)
    assert b1.ncubos is b2.ncubos, "bipartir no reutiliza el memo del sistema"


def test_bipartir_identico_a_calculo_directo() -> None:
    """La bipartición memoizada es idéntica al cálculo directo por cubo."""
    from src.models.core.system import System  # noqa: PLC0415
    tpm = _set_env(5)
    sistema = System(tpm, np.array([1, 0, 0, 0, 0], dtype=np.int8))
    alcance = np.array([0, 1], dtype=np.int8)
    mecanismo = np.array([2, 3], dtype=np.int8)
    biparticion = sistema.bipartir(alcance, mecanismo)
    for cubo, original in zip(biparticion.ncubos, sistema.ncubos):
        ejes = (
            np.setdiff1d(original.dims, mecanismo)
            if original.indice in alcance
            else mecanismo
        )
        esperado_data, esperado_dims = _referencia_marginalizar(original, ejes)
        assert np.array_equal(cubo.data, esperado_data)
        assert np.array_equal(cubo.dims, esperado_dims)


def test_condicionar_y_substraer_tienen_memo_propio() -> None:
    """Los sistemas derivados inicializan memo sin compartir el del padre."""
    from src.models.core.system import System  # noqa: PLC0415
    tpm = _set_env(5)
    sistema = System(tpm, np.array([1, 0, 0, 0, 0], dtype=np.int8))
    candidato = sistema.condicionar(np.array([4], dtype=np.int8))
    subsistema = candidato.substraer(
        np.array([3], dtype=np.int8), np.array([], dtype=np.int8)
    )
    assert candidato.memo == {} and candidato.memo is not sistema.memo
    assert subsistema.memo == {} and subsistema.memo is not candidato.memo


# --------------------------------------------------------------------------
# 4. Regresión end-to-end contra golden pre-optimización (2026-06-12)
# --------------------------------------------------------------------------

_GOLDEN_GEOMIP = [
    (5, "10000", 0.0, "⎛  A,B,C,E  ⎞⎛ D ⎞\n⎝ a,b,c,d,e ⎠⎝ ∅ ⎠"),
    (5, "11111", 0.0, "⎛  A,B,C,E  ⎞⎛ D ⎞\n⎝ a,b,c,d,e ⎠⎝ ∅ ⎠"),
    (8, "10000000", 0.0, "⎛ A,B,C,D,E,F,G ⎞⎛ H ⎞\n⎝ b,c,d,e,f,g,h ⎠⎝ a ⎠"),
]

_GOLDEN_KGEOMIP = [
    (5, "10000", [0.0, 1.0, 1.875, 2.125]),
    (8, "10000000", [0.0, 0.0, 0.0, 1.0]),
]


@pytest.mark.parametrize("n,estado,phi_golden,particion_golden", _GOLDEN_GEOMIP)
def test_regresion_geomip_golden(
    n: int, estado: str, phi_golden: float, particion_golden: str
) -> None:
    """GeoMIP reproduce φ y partición pre-optimización (tolerancia 1e-9)."""
    from src.controllers.manager import Manager  # noqa: PLC0415
    from src.controllers.strategies.geometric import GeometricSIA  # noqa: PLC0415
    tpm = _set_env(n)
    mask = "1" * n
    sol = GeometricSIA(Manager(estado_inicial=estado)).aplicar_estrategia(
        mask, mask, mask, tpm
    )
    assert abs(float(sol.perdida) - phi_golden) < 1e-9
    assert sol.particion == particion_golden


@pytest.mark.parametrize("n,estado,perdidas_golden", _GOLDEN_KGEOMIP)
def test_regresion_kgeomip_golden(
    n: int, estado: str, perdidas_golden: list[float]
) -> None:
    """KGeoMIP k=2..5 reproduce las φ pre-optimización (tolerancia 1e-9)."""
    from src.controllers.manager import Manager  # noqa: PLC0415
    from src.controllers.strategies.kgeomip import KGeoMIP  # noqa: PLC0415
    tpm = _set_env(n)
    mask = "1" * n
    kg = KGeoMIP(Manager(estado_inicial=estado))
    perdidas = [
        float(kg.aplicar_estrategia(mask, mask, mask, tpm, k=k).perdida)
        for k in range(2, 6)
    ]
    assert np.allclose(perdidas, perdidas_golden, rtol=0, atol=1e-9), (
        f"n={n}: {perdidas} != golden {perdidas_golden}"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-s"]))
