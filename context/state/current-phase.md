# Fase Actual

**Fase**: Fase 3 — Extensión KQNodes (k-particiones submodular)
**Estado**: 🟡 EN CURSO
**Inicio**: 2026-06-07
**Cierre**: —
**SDD asociado**: `context/SDD-3/`

## Objetivo

Implementar `KQNodes`: extensión de `QNodes` (bipartición Queyranne–MAO) al caso k-particiones con k ∈ {2,3,4,5}, reutilizando el oracle() y qnodes() existentes sin duplicar código. El criterio de selección es C4 (corte marginal mínimo).

## Fase anterior

**Fase 2** — Validación del funcionamiento: ✅ COMPLETADA el 2026-06-05.
Ver `context/handoffs/02.md` para el resumen de cierre.

## Criterio de salida

| Criterio | Estado |
|----------|--------|
| KQNodes(k=2) == QNodes para n ∈ {5,8,10} (tolerancia 1e-9) | 🔴 Pendiente |
| φ(k+1) ≥ φ(k) para k ∈ {2,3,4} — monotonicidad correcta | 🔴 Pendiente |
| Gap φ_greedy − φ* ≥ 0 medido y tasa de acierto exacto reportada para k≥3, n≤6 | 🔴 Pendiente |
| CSV de resultados para k ∈ {2,3,4,5}, n ∈ {5,8,10} | 🔴 Pendiente |
| Cobertura ≥ 85% en módulo KQNodes | 🔴 Pendiente |
| Tipado completo (mypy) y docstrings en métodos públicos | 🔴 Pendiente |

## Siguiente fase

→ **Fase 4 — Extensión KGeoMIP (k-particiones geométrica)**
