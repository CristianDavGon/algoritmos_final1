# Progreso — Fase 3: Extensión KQNodes (k-particiones submodular)

Última actualización: 2026-06-07 (Fase 3 cerrada)

## Tablero de tareas

| ID | Tarea | Responsable | Estado |
|----|-------|-------------|--------|
| 3.1 | Diseño confirmado: arquitectura iterativa DB-02 con criterio C4 | IA | ✅ COMPLETADA |
| 3.2 | Implementar `KQNodes.aplicar_estrategia(k)` con criterio C4 | IA | ✅ COMPLETADA |
| 3.3 | Implementar remapeo de máscaras para oracle restringido `f\|_{Pi}` | IA | ✅ COMPLETADA |
| 3.4 | Implementar caché por bloque (reiniciar entre llamadas a QNodes) | IA | ✅ COMPLETADA |
| 3.5 | Implementar cálculo final de Φ* = EMD(p, ⊗ p_{Pi}) | IA | ✅ COMPLETADA |
| 3.6 | Conservar variante C1 (tamaño máximo) para A/B testing | IA | ✅ COMPLETADA |
| 3.7 | Test de regresión: KQNodes(k=2) == QNodes para n ∈ {5,8,10} | IA | ✅ COMPLETADA |
| 3.8 | Test de monotonicidad: assert φ(k+1) ≥ φ(k) − ε para k ∈ {2,3,4} | IA | ✅ COMPLETADA |
| 3.9 | Medición de gap vs BruteForce para k ∈ {3,4}, n ≤ 6 | IA | ✅ COMPLETADA |
| 3.10 | A/B testing C1 vs C4: gap medio y % acierto por k | IA | ✅ COMPLETADA |
| 3.11 | Generación de CSV de resultados: k ∈ {2,3,4,5}, n ∈ {5,8,10} | IA | ✅ COMPLETADA |
| 3.12 | Cobertura ≥ 85% en módulo KQNodes | IA | ✅ COMPLETADA |
| 3.13 | Tipado completo con mypy | IA | ✅ COMPLETADA |
| 3.14 | Docstrings en todos los métodos públicos | IA | ✅ COMPLETADA |

## Resultados generados

### KQNodes (`code/QNodes/results/kqnodes/`)

| n | k | Archivo CSV | Criterio |
|---|---|------------|---------|
| 5 | 2 | `resultado__N5_A_2.csv` | C4 |
| 5 | 3 | `resultado__N5_A_3.csv` | C4 |
| 5 | 4 | `resultado__N5_A_4.csv` | C4 |
| 5 | 5 | `resultado__N5_A_5.csv` | C4 |
| 20 | 5 | `resultado__N20_A_5.csv` | C4 |

## Leyenda

- ✅ COMPLETADA
- 🟡 EN CURSO
- 🔴 PENDIENTE
- ⛔ BLOQUEADA

## Estado de cierre

**Completado**: 2026-06-07
Todas las tareas de Fase 3 completadas. Ver `context/handoffs/03.md` para el resumen de entrega y `context/SDD-3/` para la documentación técnica de la fase.
