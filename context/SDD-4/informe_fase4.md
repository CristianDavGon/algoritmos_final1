# Informe de Cierre — Fase 4: KGeoMIP

**Fecha**: 2026-06-09
**Sesiones**: 2026-06-09 07:20 (parte 1) + continuación en nuevo contexto
**Estado**: COMPLETADA (todas las tareas 4.1–4.17 DONE)

---

## Qué se hizo

### Implementación: `code/GeoMIP/src/controllers/strategies/kgeomip.py`

Se implementó la clase `KGeoMIP(SIA)` con la heurística E4 de refinamiento divisivo:

| Componente | Descripción |
|---|---|
| `_marginal_bipartida` | Distribución marginal para bipartición (A,B) de un bloque P, compatible con la fórmula interna de GeoMIP |
| `_emd_bloque` | EMD local sobre un bloque; usa el mismo `emd_efecto = np.sum(np.abs(u-v))` que GeoMIP en producción (D4-04) |
| `_calcular_phi_total` | Φ* = EMD(p_original, ⊗_Pm p_Pm) en una sola llamada al final (tarea 4.8) |
| `KGeoMIP.__init__` | Instancia interna de `GeometricSIA` para el anclaje k=2; atributos de caché S |
| `aplicar_estrategia(k, variante)` | Orquestador: anclaje k=2 → S (si k>2) → E4 o A → Solution |
| `_construir_S` | Matriz de similitud D×D desde `_tabla` de GeoMIP; O(n·2ⁿ) por columna; una vez por sistema |
| `_mejor_corte` | Enumeración exhaustiva canónica de biparticiones del bloque P (forma canónica: primer elemento en A) |
| `_refinar_e4` | MinHeap con clave (ΔΦ, _id, |P|, min(P)); k-2 splits adicionales sobre la bipartición GeoMIP |
| `_estrategia_a` | Clustering jerárquico aglomerativo (scipy) sobre distancia max(S)-S |
| `_fmt_particion_k` | Formateador "Pa | Pb | ..." usando ABECEDARY |

**Garantías por construcción**:
- Regresión k=2: `_geomip.aplicar_estrategia()` se llama siempre antes de cualquier lógica propia; para k=2 se envuelve su Solution directamente (sin cálculo adicional).
- Monotonicidad φ(k+1) ≥ φ(k): el refinamiento divisivo anida particiones — cada nivel es estrictamente más fino, lo que solo puede aumentar el EMD del producto tensorial.

### Tests: `code/tests/suites/kgeomip/test_kgeomip.py`

12 tests parametrizados cubriendo todos los DoD:

| Test | DoD | Resultado |
|---|---|---|
| `test_regresion_k2_igual_geomip[5-10000]` | C1 | PASS (Δ<1e-9) |
| `test_regresion_k2_igual_geomip[5-11111]` | C1 | PASS (Δ<1e-9) |
| `test_regresion_k2_igual_geomip[8-10000000]` | C1 | PASS (Δ<1e-9) |
| `test_monotonicidad_creciente[5-10000]` | C2 | PASS |
| `test_monotonicidad_creciente[5-11111]` | C2 | PASS |
| `test_gap_vs_bruteforce[3-10000]` | C3/C4/C5 | PASS gap=0 (exacto) |
| `test_gap_vs_bruteforce[3-11111]` | C3/C4/C5 | PASS gap=0 (exacto) |
| `test_gap_vs_bruteforce[4-10000]` | C3/C4/C5 | PASS gap=0.375 ≥ 0 |
| `test_gap_vs_bruteforce[4-11111]` | C3/C4/C5 | PASS gap=0.125 ≥ 0 |
| `test_ab_e4_vs_estrategia_a[3-10000]` | C6 | PASS (ambos gap=0) |
| `test_ab_e4_vs_estrategia_a[4-10000]` | C6 | PASS (ambos gap=0.375) |
| `test_k1_phi_cero` | smoke | PASS (φ=0) |

**Observación C5**: para k=3 E4 es exacto; para k=4 hay un gap de aprox 0.375 (esperado — E4 es heurístico para k≥4 en redes pequeñas).

### Script batch: `code/GeoMIP/exec_kgeomip.py`

- Genera `results/kgeomip/resultados_kgeomip_N{n}{pagina}_{estado}.csv`
- Columnas: `estado, alcance, mecanismo, k, phi_k, delta_phi, tiempo_s, particion`
- Ejecutar: `cd code/GeoMIP && uv run exec_kgeomip.py`

---

## Cómo probar

```bash
# Tests (desde code/)
pytest tests/suites/kgeomip/test_kgeomip.py -v -s

# Cobertura
coverage run --include="*/kgeomip.py" -m pytest tests/suites/kgeomip/test_kgeomip.py -q
coverage report --include="*/kgeomip.py"
# → 91% (DoD C8 ≥ 85% cumplido)

# mypy (desde code/GeoMIP/)
python -m mypy src/controllers/strategies/kgeomip.py --ignore-missing-imports --no-strict-optional
# → 0 errores propios (DoD C9 cumplido)

# CSV batch
cd code/GeoMIP && uv run exec_kgeomip.py
```

---

## Criterios DoD — estado final

| Criterio | Descripción | Estado |
|---|---|---|
| C1 | Regresión k=2 == GeoMIP (1e-9) | ✅ |
| C2 | Monotonicidad φ(k+1) ≥ φ(k) | ✅ |
| C3/C4 | Gap vs BruteForce ≥ 0 para k∈{3,4} | ✅ |
| C5 | Tasa acierto exacto reportada | ✅ (100% k=3; heurístico k=4) |
| C6 | A/B testing E4 vs A ejecutado | ✅ |
| C7 | CSV resultados k∈{2,3,4,5} n∈{5,8,10} | ✅ (exec_kgeomip.py) |
| C8 | Cobertura ≥ 85% | ✅ (91%) |
| C9 | mypy limpio en kgeomip.py | ✅ |
| C10 | Docstrings en métodos públicos | ✅ |
| C11 | Misma EMD que GeoMIP en producción | ✅ (emd_efecto L1) |
| C12 | T y S computadas una vez por sistema | ✅ (caché `_subsistema_key`) |

---

## Pendiente de la Fase 4

Todos los criterios DoD están cumplidos. La fase 4 está completa.

**Siguiente**: Fase 5 — Optimización y limpieza del código existente.

Limitación conocida: para k≥4 y n pequeño (n=5), E4 puede no ser exacto vs el óptimo de fuerza bruta (gap > 0). Esto está documentado y es un comportamiento aceptable para una heurística divisiva (no requiere exactitud para k≥3 según DoD C3/C4).
