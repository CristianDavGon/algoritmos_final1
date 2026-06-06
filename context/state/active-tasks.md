# Tareas Activas — Fase 2: Validación del funcionamiento

Última actualización: 2026-06-05 (tarea 2.6 completada)

## Tareas originales

| ID | Descripción | Responsable | Estado |
|----|-------------|-------------|--------|
| 2.1 | Ejecutar GeoMIP n=5 y n=8; verificar CSV de resultados | IA | ✅ COMPLETADA |
| 2.2 | Ejecutar QNodes n=5 y n=8; verificar CSV de resultados | IA | ✅ COMPLETADA |
| 2.3 | Comparar GeoMIP vs QNodes vs BruteForce para n≤6 | IA | ✅ COMPLETADA |
| 2.5 | Confirmar que el profiling HTML se genera correctamente | IA | ✅ COMPLETADA |
| 2.6 | Documentar toda discrepancia en `known-issues.md` | IA | ✅ COMPLETADA |

## Tareas adicionales (identificadas dentro del alcance de Fase 2)

| ID | Descripción | Responsable | Estado |
|----|-------------|-------------|--------|
| 2.7 | Corrección de bug: inversión de ejes en oracle y parser de particiones (QNodes) | IA | ✅ COMPLETADA |
| 2.8 | Optimización de GeoMIP (ajuste basado en documento previo) | IA | ✅ COMPLETADA |
| 2.9 | Ejecuciones extendidas para n ∈ {10, 15, 20, 22} | IA | ✅ COMPLETADA |
| 2.10 | Generación de TPMs para n ∈ {20, 22, 25} | IA | ✅ COMPLETADA |

## Pendiente para cerrar la fase

- Ninguna tarea pendiente. Todas las tareas de Fase 2 están completadas.

## Completadas en esta fase

- **2.3**: GeoMIP y QNodes alcanzan φ accuracy 100% vs BruteForce (Δφ=0.000000 en todos los casos, n=5 y n=8). Resultados en `code/tests/results/{geomip,qnodes}/vs_bruteforce/`.
- **2.5**: pyinstrument genera HTML con call tree completo (214 KB, 870 entradas, tiempos reales). Verificado en `GeoMIP/review/profiling/`.
- **2.6**: known-issues.md cerrado. Investigación GeoMIP N8A resuelta: BruteForce confirma φ=0.0 en los 49/49 casos del sampleA (exactitud 100%, Δφ=0). QNodes sobre el mismo sampleA produce idéntico resultado. Sin discrepancias sin documentar en QNodes vs_bruteforce.
