# Tareas Activas — Fase 4 (EN CURSO)

> Fase 4 iniciada el 2026-06-08. Ver `context/SDD-4/planning.md` para el alcance completo.
> El diseño algorítmico detallado está en `temp/Diseno_KGeoMIP_Fase4.md`.

## Tareas de implementación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 4.1 | Verificar función EMD de GeoMIP en producción (caveat D4-04) | 🔴 PENDIENTE | Pre-requisito de todos los tests; localizar `emd_efecto` en `geometric.py` |
| 4.2 | Construir matriz de similitud S (n×n) desde T | 🔴 PENDIENTE | O(n²·2ⁿ); una sola vez por sistema; ver §2 de implementation.md |
| 4.3 | Implementar `KGeoMIP.aplicar_estrategia(k)` con heurística E4 | 🔴 PENDIENTE | Fases 0-4 del pseudocódigo; hereda de SIA; recibe Manager |
| 4.4 | Implementar anclaje k=2 en GeoMIP exacto (Fase 2 del pseudocódigo) | 🔴 PENDIENTE | Llamada directa a `GeoMIP_bipartir(V, T)` — no duplicar |
| 4.5 | Implementar cola de prioridad (MinHeap) para criterio min ΔΦ (Fase 3) | 🔴 PENDIENTE | Clave: (ΔΦ, bfs_order, |P|, min_idx); ver §4 de implementation.md |
| 4.6 | Implementar subrutina MejorCorte (S propone, EMD confirma) | 🔴 PENDIENTE | Candidatos BFS de GeoMIP como red de seguridad; ver §5 |
| 4.7 | Implementar marginalización correcta (SUMAR cols, PROMEDIAR filas, ⊗ proyecto) | 🔴 PENDIENTE | Reglas críticas en §6 de implementation.md |
| 4.8 | Implementar cálculo final de Φ* = EMD(p, ⊗ p_{Pₘ}) una sola vez | 🔴 PENDIENTE | `_calcular_phi_total()` — misma función EMD que GeoMIP |
| 4.9 | Implementar Estrategia A (clustering aglomerativo sobre S) como baseline | 🔴 PENDIENTE | Para A/B testing; ver §7 de implementation.md |

## Tareas de validación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 4.10 | Test de regresión: KGeoMIP(k=2) == GeoMIP para n ∈ {5,8,10} | 🔴 PENDIENTE | `test_regresion_k2_igual_geomip` — tolerancia 1e-9 |
| 4.11 | Test de monotonicidad: assert φ(k+1) ≥ φ(k) − ε para k ∈ {2,3,4} | 🔴 PENDIENTE | `test_monotonicidad_creciente` — dirección ≥, NO ≤ |
| 4.12 | Medición de gap vs BruteForce para k ∈ {3,4}, n ≤ 6 | 🔴 PENDIENTE | `test_gap_vs_bruteforce` — gap ≥ 0; tasa de acierto exacto |
| 4.13 | A/B testing E4 vs Estrategia A: gap medio y % acierto por k | 🔴 PENDIENTE | `test_ab_e4_vs_estrategia_a` para k ∈ {3,4} |
| 4.14 | Generación de CSV de resultados: k ∈ {2,3,4,5}, n ∈ {5,8,10} | 🔴 PENDIENTE | Script batch; incluir Φ(k) y ΔΦ(k) para diagnóstico de k* |

## Tareas de calidad

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 4.15 | Cobertura ≥ 85% en módulo KGeoMIP | 🔴 PENDIENTE | Todas las rutas públicas cubiertas |
| 4.16 | Tipado completo con mypy | 🔴 PENDIENTE | Limpio en kgeomip.py |
| 4.17 | Docstrings en todos los métodos públicos | 🔴 PENDIENTE | Google/NumPy docstrings |

## Restricciones

- **No tocar**: código de GeoMIP, QNodes, KQNodes, BruteForce existentes.
- **No iniciar**: Fase 5 hasta completar esta fase.
- **No duplicar**: maquinaria de GeoMIP (BFS, EMD, marginalización) — solo invocar.
- **Pre-requisito crítico**: resolver D4-04 (verificar función EMD) antes de validar C1.
