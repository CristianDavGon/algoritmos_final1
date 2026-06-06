# Progreso — Fase 2: Validación del funcionamiento

Última actualización: 2026-06-05 (Fase 2 cerrada)

## Tablero de tareas

| ID | Tarea | Responsable | Estado |
|----|-------|-------------|--------|
| 2.1 | Ejecutar GeoMIP n=5 y n=8; verificar CSV | IA | ✅ COMPLETADA |
| 2.2 | Ejecutar QNodes n=5 y n=8; verificar CSV | IA | ✅ COMPLETADA |
| 2.3 | Comparar GeoMIP vs QNodes vs BruteForce para n≤6 | IA | ✅ COMPLETADA |
| 2.5 | Confirmar profiling HTML | IA | ✅ COMPLETADA |
| 2.6 | Documentar discrepancias en `known-issues.md` | IA | ✅ COMPLETADA |
| 2.7 | Fix bug QNodes: inversión de ejes en oracle y parser de particiones | IA | ✅ COMPLETADA |
| 2.8 | Optimización de GeoMIP (ajuste basado en documento previo) | IA | ✅ COMPLETADA |
| 2.9 | Ejecuciones extendidas n ∈ {10, 15, 20, 22} | IA | ✅ COMPLETADA |
| 2.10 | Generación de TPMs para n ∈ {20, 22, 25} | IA | ✅ COMPLETADA |

## Resultados generados

### GeoMIP (`code/GeoMIP/results/`)

| n | Archivo | Pruebas | Rango φ | T̄ (s) |
|---|---------|---------|---------|--------|
| 5 | `geomip/resultados_N5A.csv` | 49 | 0.0 – 0.500 | ~0.00106 |
| 8 | `geomip/resultados_N8A.csv` | 49 | **0.0 – 0.0 ⚠️** | ~0.00346 |
| 10 | `geomip/resultados_N10A.csv` | 49 | 0.00391 – 0.484 | ~0.00745 |
| 15 | `geomip/resultados_N15A.csv` | 50 | 0.0 – 7.61e-4 | ~0.5965 |
| 15 | `resultados_N15B.csv` | 50 | 0.0 – 1.51e-3 | ~0.7289 |
| 20 | `geomip/resultados_N20A.csv` | 50 | 2.86e-5 – 0.499 | ~9.8237 |

### QNodes (`code/QNodes/results/`)

| n | Archivo | Pruebas | Rango φ | T̄ (s) |
|---|---------|---------|---------|--------|
| 5 | `resultados_N5B.csv` | 48 | 0.0 – 0.25 | ~0.0048 |
| 8 | `resultados_N8A.csv` | 49 | **— (vacío, pre-fix DT-10)** | — |
| 8 | `resultados_N8B.csv` | 49 | 0.0 – 1.0 | ~0.000657 |
| 10 | `resultados_N10A.csv` | 49 | 0.00586 – 0.480 | ~0.5357 |
| 15 | `resultados_N15A.csv` | 50 | **— (vacío)** | — |
| 15 | `resultados_N15B.csv` | 50 | 0.0 – 0.270 | ~0.0139 |
| 20 | `resultados_N20B.csv` | 50 | 2.86e-5 – 0.499 | ~1.2256 |
| 22 | `resultados_N22B.csv` | 50 | 3.77e-5 – 0.500 | ~6.3435 |

## Leyenda

- ✅ COMPLETADA
- 🟡 EN CURSO
- 🔴 PENDIENTE
- ⛔ BLOQUEADA

## Estado de cierre

**Completado**: 2026-06-05  
Todas las tareas de Fase 2 completadas. Ver `context/handoffs/01.md` para el resumen de entrega y `context/SDD-2/` para la documentación técnica de la fase.
