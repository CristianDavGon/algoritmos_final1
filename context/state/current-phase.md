# Fase Actual

**Fase**: Fase 2 — Validación del funcionamiento
**Estado**: 🟡 EN CURSO
**Inicio**: 2026-06-05
**SDD asociado**: ninguno por ahora (se creará SDD-2 al cerrar la fase)

## Objetivo

Verificar que GeoMIP y QNodes producen resultados correctos antes de extender a k-particiones.

## Criterio de salida

| Criterio | Estado |
|----------|--------|
| Ambas estrategias ejecutan sin errores para n ∈ {5, 8} | ✅ Cumplido |
| Al menos un caso n=5 validado contra BruteForce (`\|φ_nuevo - φ_ref\| < 1e-9`) | 🔴 Pendiente — comparación BruteForce no realizada aún |
| CSV de resultados verificados y coherentes | 🟡 Parcial — GeoMIP N8A con φ=0.0 en todos los casos (sospechoso); QNodes N8A y N15A vacíos (legacy pre-fix DT-10) |
| Comparación GeoMIP vs QNodes vs BruteForce para n≤6 | 🔴 Sin evidencia de archivo de comparación explícito |
| Profiling HTML generado correctamente | 🔴 Sin confirmar |

## Siguiente fase

→ **Fase 3 — Optimización y limpieza del código existente**
