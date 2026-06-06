# Tareas Activas — Fase 2: Validación del funcionamiento

Última actualización: 2026-06-05

## Tareas originales

| ID | Descripción | Responsable | Estado |
|----|-------------|-------------|--------|
| 2.1 | Ejecutar GeoMIP n=5 y n=8; verificar CSV de resultados | IA | ✅ COMPLETADA |
| 2.2 | Ejecutar QNodes n=5 y n=8; verificar CSV de resultados | IA | ✅ COMPLETADA |
| 2.3 | Comparar GeoMIP vs QNodes vs BruteForce para n≤6 | IA | 🔴 PENDIENTE |
| 2.5 | Confirmar que el profiling HTML se genera correctamente | IA | 🔴 PENDIENTE |
| 2.6 | Documentar toda discrepancia en `known-issues.md` | IA | 🟡 EN CURSO |

## Tareas adicionales (identificadas dentro del alcance de Fase 2)

| ID | Descripción | Responsable | Estado |
|----|-------------|-------------|--------|
| 2.7 | Corrección de bug: inversión de ejes en oracle y parser de particiones (QNodes) | IA | ✅ COMPLETADA |
| 2.8 | Optimización de GeoMIP (ajuste basado en documento previo) | IA | ✅ COMPLETADA |
| 2.9 | Ejecuciones extendidas para n ∈ {10, 15, 20, 22} | IA | ✅ COMPLETADA |
| 2.10 | Generación de TPMs para n ∈ {20, 22, 25} | IA | ✅ COMPLETADA |

## Pendiente para cerrar la fase

- **2.3**: ejecutar comparación explícita GeoMIP vs QNodes vs BruteForce para n≤6 con `|φ_nuevo - φ_ref| < 1e-9`.
- **2.5**: confirmar que el profiling HTML se genera en `results/` después de una ejecución batch.
- **2.6**: completar documentación de discrepancias (especialmente GeoMIP N8A con φ=0 en todos los casos).
