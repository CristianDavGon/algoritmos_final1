# Tareas Activas — Fase 3 (EN CURSO)

> Fase 3 iniciada el 2026-06-07. Ver `context/SDD-3/planning.md` para el alcance completo.
> El diseño algorítmico detallado está en `temp/Diseno_KQNodes_Fase3.md`.

## Tareas de implementación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 3.1 | Diseño confirmado: arquitectura iterativa DB-02 con criterio C4 | ✅ COMPLETADA (planificación) | Ver `context/SDD-3/implementation.md` |
| 3.2 | Implementar `KQNodes.aplicar_estrategia(k)` con criterio C4 | 🔴 Pendiente | Hereda de `SIA`; reutiliza `oracle()` y `qnodes()` |
| 3.3 | Implementar remapeo de máscaras para oracle restringido `f\|_{Pi}` | 🔴 Pendiente | Ver §4.3 del documento de diseño |
| 3.4 | Implementar caché por bloque (reiniciar entre llamadas a QNodes) | 🔴 Pendiente | No compartir caché global — ver D3-02 |
| 3.5 | Implementar cálculo final de Φ* = EMD(p, ⊗ p_{Pi}) | 🔴 Pendiente | Una sola llamada al final |
| 3.6 | Conservar variante C1 (tamaño máximo) para A/B testing | 🔴 Pendiente | Mismo esquema, sustituir paso de selección |

## Tareas de validación

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 3.7 | Test de regresión: KQNodes(k=2) == QNodes para n ∈ {5,8,10} | 🔴 Pendiente | Tolerancia 1e-9; regla dura DB-03.1 |
| 3.8 | Test de monotonicidad: assert φ(k+1) ≥ φ(k) − ε para k ∈ {2,3,4} | 🔴 Pendiente | Dirección correcta; detecta bugs de EMD/remapeo |
| 3.9 | Medición de gap vs BruteForce para k ∈ {3,4}, n ≤ 6 | 🔴 Pendiente | Reportar gap = φ_greedy − φ*, tasa de acierto exacto |
| 3.10 | A/B testing C1 vs C4: gap medio y % acierto por k | 🔴 Pendiente | Evidencia experimental para rúbrica |
| 3.11 | Generación de CSV de resultados: k ∈ {2,3,4,5}, n ∈ {5,8,10} | 🔴 Pendiente | Mismo formato que QNodes |

## Tareas de calidad

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 3.12 | Cobertura ≥ 85% en módulo KQNodes | 🔴 Pendiente | — |
| 3.13 | Tipado completo con mypy | 🔴 Pendiente | — |
| 3.14 | Docstrings en todos los métodos públicos | 🔴 Pendiente | — |

## Restricciones

- **No tocar**: código de GeoMIP, QNodes, BruteForce existentes.
- **No iniciar**: Fase 4 (KGeoMIP) hasta completar esta fase.
- **No duplicar**: oracle() y qnodes() — solo invocarlos sobre subconjuntos.
