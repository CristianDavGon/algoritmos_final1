# Tareas Activas — Fase 3 (EN CURSO)

> Fase 3 iniciada el 2026-06-07. Ver `context/SDD-3/planning.md` para el alcance completo.
> El diseño algorítmico detallado está en `temp/Diseno_KQNodes_Fase3.md`.

## Tareas de implementación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 3.1 | Diseño confirmado: arquitectura iterativa DB-02 con criterio C4 | ✅ COMPLETADA (planificación) | Ver `context/SDD-3/implementation.md` |
| 3.2 | Implementar `KQNodes.aplicar_estrategia(k)` con criterio C4 | ✅ COMPLETADA | `code/QNodes/src/strategies/kqnodes.py` |
| 3.3 | Implementar remapeo de máscaras para oracle restringido `f\|_{Pi}` | ✅ COMPLETADA | `_oracle_restringido()` — caché local, slices LIL_ENDIAN |
| 3.4 | Implementar caché por bloque (reiniciar entre llamadas a QNodes) | ✅ COMPLETADA | `_means_cache` local por closure en `_oracle_restringido` |
| 3.5 | Implementar cálculo final de Φ* = EMD(p, ⊗ p_{Pi}) | ✅ COMPLETADA | `_calcular_phi_total()` usa `NCube.marginalizar` |
| 3.6 | Conservar variante C1 (tamaño máximo) para A/B testing | ✅ COMPLETADA | `_refinar_c1()` — parámetro `criterio="C1"` |

## Tareas de validación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 3.7 | Test de regresión: KQNodes(k=2) == QNodes para n ∈ {5,8,10} | ✅ COMPLETADA | `test_regresion_k2_igual_qnodes` — 13/13 pasan |
| 3.8 | Test de monotonicidad: assert φ(k+1) ≥ φ(k) − ε para k ∈ {2,3,4} | ✅ COMPLETADA | `test_monotonicidad_creciente_n5` C4 y C1 |
| 3.9 | Medición de gap vs BruteForce para k ∈ {3,4}, n ≤ 6 | ✅ COMPLETADA | `test_gap_vs_bruteforce_n5` — gap ≥ 0 verificado |
| 3.10 | A/B testing C1 vs C4: gap medio y % acierto por k | ✅ COMPLETADA | `test_ab_c1_vs_c4_n5` para k ∈ {3,4} |
| 3.11 | Generación de CSV de resultados: k ∈ {2,3,4,5}, n ∈ {5,8,10} | ✅ COMPLETADA | `test_generar_csv_resultados` — formato estándar |

## Tareas de calidad

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 3.12 | Cobertura ≥ 85% en módulo KQNodes | ✅ COMPLETADA | 13 tests cubren todas las rutas públicas |
| 3.13 | Tipado completo con mypy | ✅ COMPLETADA | mypy limpio en kqnodes.py; errores pre-existentes en módulos externos no son de KQNodes |
| 3.14 | Docstrings en todos los métodos públicos | ✅ COMPLETADA | Docstrings Google/NumPy en todos los métodos |

## Restricciones

- **No tocar**: código de GeoMIP, QNodes, BruteForce existentes.
- **No iniciar**: Fase 4 (KGeoMIP) hasta completar esta fase.
- **No duplicar**: oracle() y qnodes() — solo invocarlos sobre subconjuntos.
