"""Benchmark de KGeoMIP: tiempo por (n, k, estrategia_corte) y gap vs BruteForce.

Mide dos cosas:
    1. Tiempo: barrido k=1..5 sobre una misma instancia (caso batch real) y
       tiempo de la primera llamada (instancia fresca) para n ∈ {5, 8, 10}.
    2. Exactitud: gap = φ_E4 − φ* contra la enumeración exhaustiva de
       k-particiones (Stirling) para n ∈ {5, 6, 8}, k ∈ {3, 4}.

Uso (desde code/):
    uv run python scripts/bench_kgeomip.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_CODE_ROOT = Path(__file__).resolve().parents[1]
_GEOMIP_ROOT = _CODE_ROOT / "GeoMIP"
if str(_GEOMIP_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOMIP_ROOT))

import numpy as np  # noqa: E402


def _set_env(n: int, pagina: str = "A") -> np.ndarray:
    from src.models.base.application import aplicacion
    aplicacion.pagina_sample_network = pagina
    aplicacion.profiler_habilitado = False
    ruta = _GEOMIP_ROOT / "data" / "samples" / f"N{n}{pagina}.csv"
    os.environ["GEOMIP_SAMPLES_DIR"] = str(ruta.parent)
    return np.genfromtxt(ruta, delimiter=",")


def _make_kgeomip(estado: str):
    from src.controllers.manager import Manager
    from src.controllers.strategies.kgeomip import KGeoMIP
    return KGeoMIP(Manager(estado_inicial=estado))


def _all_k_partitions(n: int, k: int):
    def _rgs(i: int, max_used: int):
        if i == n:
            yield ()
            return
        for val in range(min(max_used + 2, k)):
            for rest in _rgs(i + 1, max(max_used, val)):
                yield (val,) + rest

    for rest in _rgs(1, 0):
        asg = (0,) + rest
        if len(set(asg)) == k:
            yield [frozenset(i for i in range(n) if asg[i] == g) for g in range(k)]


def _bruteforce_phi_k(kg, k: int) -> float:
    from src.controllers.strategies.kgeomip import _calcular_phi_total
    n = len(kg.sia_subsistema.dims_ncubos)
    return min(
        _calcular_phi_total(parts, kg.sia_subsistema)
        for parts in _all_k_partitions(n, k)
    )


def bench_tiempos() -> None:
    print("=" * 72)
    print("TIEMPOS — barrido k=1..5 (misma instancia) por estrategia de corte")
    print("=" * 72)
    for n in (5, 8, 10):
        estado = "1" + "0" * (n - 1)
        mask = "1" * n
        tpm = _set_env(n)
        for corte in ("exhaustivo", "guiado_S", "auto"):
            kg = _make_kgeomip(estado)
            t0 = time.perf_counter()
            phis = {}
            for k in range(1, 6):
                tk = time.perf_counter()
                sol = kg.aplicar_estrategia(
                    mask, mask, mask, tpm, k=k, estrategia_corte=corte
                )
                phis[k] = (sol.perdida, time.perf_counter() - tk)
            total = time.perf_counter() - t0
            detalle = "  ".join(
                f"k={k}:{phi:.4f}({t*1000:.0f}ms)" for k, (phi, t) in phis.items()
            )
            print(f"n={n:2d} corte={corte:<10s} total={total:7.3f}s  {detalle}")


def bench_exactitud() -> None:
    print("=" * 72)
    print("EXACTITUD — gap = φ_E4 − φ* (BruteForce Stirling) por estrategia")
    print("=" * 72)
    casos = [(5, "10000"), (5, "11111"), (6, "100000"), (8, "10000000")]
    for n, estado in casos:
        mask = "1" * n
        tpm = _set_env(n)
        for k in (3, 4):
            kg = _make_kgeomip(estado)
            for corte in ("exhaustivo", "guiado_S", "auto"):
                t0 = time.perf_counter()
                sol = kg.aplicar_estrategia(
                    mask, mask, mask, tpm, k=k, estrategia_corte=corte
                )
                t_e4 = time.perf_counter() - t0
                phi_opt = _bruteforce_phi_k(kg, k)
                gap = sol.perdida - phi_opt
                print(
                    f"n={n} k={k} estado={estado} corte={corte:<10s} "
                    f"phi={sol.perdida:.6f} phi*={phi_opt:.6f} "
                    f"gap={gap:+.2e} t={t_e4*1000:6.1f}ms "
                    f"{'EXACTO' if abs(gap) < 1e-9 else 'subopt'}"
                )


if __name__ == "__main__":
    bench_tiempos()
    bench_exactitud()
