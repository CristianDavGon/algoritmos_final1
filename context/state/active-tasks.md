# Tareas Activas — Fase 4 (EN CURSO)

> Fase 4 iniciada el 2026-06-08. Ver `context/SDD-4/planning.md` para el alcance completo.
> El diseño algorítmico detallado está en `temp/Diseno_KGeoMIP_Fase4.md`.

## Tareas de implementación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 4.1 | Verificar función EMD de GeoMIP en producción (caveat D4-04) | ✅ DONE | `emd_efecto = np.sum(np.abs(u - v))` — L1, no pyemd |
| 4.2 | Construir matriz de similitud S (n×n) desde T | ✅ DONE | `_construir_S` en kgeomip.py; O(n²·2ⁿ) por columna |
| 4.3 | Implementar `KGeoMIP.aplicar_estrategia(k)` con heurística E4 | ✅ DONE | Fases 0-4 del pseudocódigo; hereda SIA; recibe Manager |
| 4.4 | Implementar anclaje k=2 en GeoMIP exacto (Fase 2 del pseudocódigo) | ✅ DONE | Delegación directa a `GeometricSIA.aplicar_estrategia` |
| 4.5 | Implementar cola de prioridad (MinHeap) para criterio min ΔΦ (Fase 3) | ✅ DONE | Clave `(dphi, _id, len(P), min(P))` en `_refinar_e4` |
| 4.6 | Implementar subrutina MejorCorte (S propone, EMD confirma) | ✅ DONE | Enumeración exhaustiva canónica de biparticiones del bloque |
| 4.7 | Implementar marginalización correcta (SUMAR cols, PROMEDIAR filas, ⊗ proyecto) | ✅ DONE | `_marginal_bipartida` + `marginalizar(non_pi)` en `_calcular_phi_total` |
| 4.8 | Implementar cálculo final de Φ* = EMD(p, ⊗ p_{Pₘ}) una sola vez | ✅ DONE | `_calcular_phi_total()` usa `emd_efecto` (C11) |
| 4.9 | Implementar Estrategia A (clustering aglomerativo sobre S) como baseline | ✅ DONE | `_estrategia_a` con scipy linkage/fcluster |

## Tareas de validación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 4.10 | Test de regresión: KGeoMIP(k=2) == GeoMIP para n ∈ {5,8,10} | ✅ DONE | `test_regresion_k2_igual_geomip` — PASA (Δ < 1e-9) |
| 4.11 | Test de monotonicidad: assert φ(k+1) ≥ φ(k) − ε para k ∈ {2,3,4} | ✅ DONE | `test_monotonicidad_creciente` — PASA |
| 4.12 | Medición de gap vs BruteForce para k ∈ {3,4}, n ≤ 6 | ✅ DONE | `test_gap_vs_bruteforce` — gap ≥ 0 para k=3 (exacto), k=4 (heurístico) |
| 4.13 | A/B testing E4 vs Estrategia A: gap medio y % acierto por k | ✅ DONE | `test_ab_e4_vs_estrategia_a` — ambos gap ≥ 0 |
| 4.14 | Generación de CSV de resultados: k ∈ {2,3,4,5}, n ∈ {5,8,10} | ✅ DONE | Script `exec_kgeomip.py`; columnas: phi_k, delta_phi, tiempo_s, particion |

## Tareas de calidad

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 4.15 | Cobertura ≥ 85% en módulo KGeoMIP | ✅ DONE | 91% (medido con `coverage run --include="*/kgeomip.py"`) |
| 4.16 | Tipado completo con mypy | ✅ DONE | 0 errores propios en kgeomip.py (`--ignore-missing-imports`) |
| 4.17 | Docstrings en todos los métodos públicos | ✅ DONE | Google/NumPy en todos los métodos públicos y funciones de módulo |

## Restricciones (cumplidas)

- **No tocar**: código de GeoMIP, QNodes, KQNodes, BruteForce existentes. ✓
- **No iniciar**: Fase 5 hasta completar esta fase. ✓
- **No duplicar**: maquinaria de GeoMIP (BFS, EMD, marginalización) — solo invocar. ✓
- **Pre-requisito crítico**: D4-04 resuelto — `emd_efecto = np.sum(np.abs(u-v))`. ✓
