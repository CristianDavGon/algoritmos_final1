# SDD-4 — Planning: Extensión KGeoMIP (k-particiones geométrica)

**Fase**: 4
**Estado**: 🟡 EN CURSO
**Inicio**: 2026-06-08
**Cierre**: —

## Objetivo de la fase

Implementar `KGeoMIP`: extensión de `GeoMIP` (bipartición geométrico-topológica sobre el hipercubo) al caso general de k-particiones con k ∈ {2,3,4,5}. El algoritmo usa la heurística **E4**: refinamiento divisivo top-down anclado en GeoMIP (k=2 exacto por construcción), con la matriz de similitud S (n×n) derivada de T como guía global de los cortes baratos, y la EMD vía T para confirmar cada corte (criterio de corte marginal mínimo, min ΔΦ).

## Alcance

**Dentro de alcance:**
- Clase `KGeoMIP` que hereda de `SIA` e implementa `aplicar_estrategia(k)`.
- Construcción de la matriz de similitud S (n×n) desde T, una sola vez por sistema (O(n²·2ⁿ)).
- Anclaje del primer corte k=2 en GeoMIP exacto: regresión garantizada por construcción.
- Refinamiento divisivo (top-down) por criterio de corte marginal mínimo (min ΔΦ) con cola de prioridad (MinHeap).
- Subrutina MejorCorte: S propone cortes de baja similitud + candidatos BFS de GeoMIP; EMD confirma.
- Marginalización correcta: columnas SUMAR, filas descartadas PROMEDIAR, sin normalizar; ⊗ del proyecto (expande columnas, no Kronecker).
- Cálculo final de Φ* = EMD(p(s_{t+1}), ⊗_{Pi∈Π} p_{Pi}) una sola vez al terminar la búsqueda.
- Estrategia A (clustering jerárquico aglomerativo sobre S) implementada como baseline de comparación A/B.
- Tests de regresión k=2, monotonicidad φ(k+1) ≥ φ(k), gap de optimalidad y tasa de acierto exacto vs BruteForce para k≥3.
- CSV de resultados para k ∈ {2,3,4,5}, n ∈ {5,8,10}.

**Fuera de alcance:**
- No modificar GeoMIP, QNodes, KQNodes, BruteForce existentes.
- No iniciar Fase 5 hasta completar esta fase.
- No refactorizar la deuda técnica de Fases 1-3 (queda para Fase 5).
- No implementar extensiones futuras (lookahead, beam search) — están documentadas como posibles mejoras pero no son parte de la entrega.
- No implementar Estrategia B (espectral) ni C (comunidades) — solo E4 + Estrategia A como baseline.

## Estado inicial (herencia de Fase 3)

La Fase 3 cerró con:
- `KQNodes` implementado con criterio C4, regresión k=2 exacta, monotonicidad φ(k+1) ≥ φ(k) verificada.
- Infraestructura de tests de regresión y gap vs BruteForce en `code/QNodes/tests/` — reutilizable como referencia de diseño.
- Decisiones de monotonicidad ya corregidas (φ(k+1) ≥ φ(k), no ≤): DEC-13, DB-03.
- GeoMIP funciona para n ∈ {5,8,10,15,20}; tabla T disponible vía `calcular_costo()` en `geometric.py`.
- Punto de entrada de código GeoMIP: `code/GeoMIP/src/strategies/geometric.py` → `GeometricSIA.aplicar_estrategia()`.

Ver `context/handoffs/03.md` para el resumen completo de cierre de Fase 3.

**Arquitectura heredada (DEC-02):** `KGeoMIP(SIA)` recibe `Manager` en `__init__` (igual que `GeometricSIA`), no `tpm` directamente (eso es QNodes). Esta distinción es intencional.

## Entregables esperados

| Entregable | Archivo | Estado |
|-----------|---------|--------|
| Planning de la fase | `context/SDD-4/planning.md` | ✅ Este archivo |
| Criterios de DONE | `context/SDD-4/done-criteria.md` | ✅ |
| Notas de implementación | `context/SDD-4/implementation.md` | ✅ |
| Preguntas de validación | `context/SDD-4/testing.md` | ✅ |
| Decisiones de la fase | `context/SDD-4/decisions.md` | ✅ |
| Clase KGeoMIP (E4) implementada | `code/GeoMIP/src/strategies/kgeomip.py` | 🔴 Pendiente |
| Estrategia A (baseline) | `code/GeoMIP/src/strategies/kgeomip_a.py` (o integrada) | 🔴 Pendiente |
| Tests de regresión/monotonicidad/gap | `code/GeoMIP/tests/` | 🔴 Pendiente |
| CSV de resultados | `code/GeoMIP/results/kgeomip/` | 🔴 Pendiente |
| Handoff de cierre | `context/handoffs/04.md` | 🔴 Pendiente (al cerrar) |

## Documento de diseño de referencia

**`temp/Diseno_KGeoMIP_Fase4.md`** — diseño matemático y algorítmico completo de KGeoMIP. Es el insumo principal y tiene prioridad sobre cualquier documento de contexto anterior cuando haya contradicción.
