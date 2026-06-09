# Fase Actual

**Fase**: Fase 4 — Extensión KGeoMIP (k-particiones geométrica)
**Estado**: 🟡 EN CURSO
**Inicio**: 2026-06-08
**Cierre**: —
**SDD asociado**: `context/SDD-4/`

## Objetivo

Implementar `KGeoMIP`: extensión de `GeoMIP` al caso k-particiones con k ∈ {2,3,4,5}, usando la heurística E4 (refinamiento divisivo top-down anclado en GeoMIP, guiado por la matriz de similitud S derivada de T, con EMD confirmando cada corte). La firma de KGeoMIP es S como dispositivo central de lectura de la estructura modular del hipercubo.

## Fase anterior

**Fase 3** — Extensión KQNodes (k-particiones submodular): ✅ COMPLETADA el 2026-06-07.
Ver `context/handoffs/03.md` para el resumen de cierre.

## Criterio de salida

| Criterio | Estado |
|----------|--------|
| KGeoMIP(k=2) == GeoMIP para n ∈ {5,8,10} (tolerancia 1e-9) | 🔴 Pendiente |
| φ(k+1) ≥ φ(k) para k ∈ {2,3,4} — monotonicidad correcta (≥, no ≤) | 🔴 Pendiente |
| Gap φ_E4 − φ* ≥ 0 medido y tasa de acierto exacto reportada para k ∈ {3,4}, n≤6 | 🔴 Pendiente |
| A/B testing E4 vs Estrategia A ejecutado y documentado | 🔴 Pendiente |
| CSV de resultados para k ∈ {2,3,4,5}, n ∈ {5,8,10} generados | 🔴 Pendiente |
| Función EMD verificada y consistente con GeoMIP en producción | 🔴 Pendiente |
| Cobertura ≥ 85% en módulo KGeoMIP | 🔴 Pendiente |
| Tipado completo (mypy) y docstrings en métodos públicos | 🔴 Pendiente |

## Siguiente fase

→ **Fase 5 — Optimización y limpieza del código existente**
