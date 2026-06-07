# SDD-3 — Planning: Extensión KQNodes (k-particiones submodular)

**Fase**: 3
**Estado**: 🟡 EN CURSO
**Inicio**: 2026-06-07
**Cierre**: —

## Objetivo de la fase

Implementar `KQNodes`: extensión de `QNodes` (bipartición Queyranne–MAO) al caso general de k-particiones con k ∈ {2,3,4,5}. El algoritmo debe reutilizar el oracle() y qnodes() existentes sin duplicar código, operar en O(k·D³), y usar el **Criterio C4** (corte marginal mínimo) como política de selección de la parte a bipartir.

## Alcance

**Dentro de alcance:**
- Clase `KQNodes` que hereda de `SIA` e implementa `aplicar_estrategia(k)`.
- Remapeo de máscaras para el oracle restringido f|_{Pi} (espacio global D bits → local |Pi| bits).
- Caché del oracle por bloque (se reinicia entre llamadas a QNodes sobre distintas partes).
- Cálculo final de Φ* = EMD(p(s_{t+1}), ⊗_{Pi∈Π} p_{Pi}) una sola vez al terminar la búsqueda.
- Variante C1 (tamaño máximo) conservada para A/B testing experimental.
- Tests de regresión k=2, monotonicidad φ(k+1) ≥ φ(k), y medición de gap vs BruteForce para k≥3.
- CSV de resultados para k ∈ {2,3,4,5}, n ∈ {5,8,10}.

**Fuera de alcance:**
- No modificar GeoMIP, QNodes, BruteForce existentes.
- No iniciar KGeoMIP (Fase 4).
- No refactorizar la deuda técnica de Fases 1-2 (queda para Fase 5).
- No implementar extensiones futuras (lookahead, beam search).

## Estado inicial (herencia de Fase 2)

La Fase 2 cerró con:
- QNodes ejecuta sin errores para n ∈ {5,8,10,15,20,22}; exactitud φ 100% vs BruteForce para n ∈ {5,8}.
- Bug DT-10 corregido (inversión de ejes en oracle Queyranne). Commit `b2b00e1`.
- Scripts de comparación vs BruteForce en `code/tests/` — reutilizarlos en Fase 3 con parámetro k variable.
- Decisiones bloqueantes DB-01 a DB-04 resueltas en `context/SDD-1/decisions.md`.

El punto de entrada de código es `code/QNodes/src/strategies/qnodes.py`: el oracle (líneas 29-78) opera sobre `NCube.dims` y se reutiliza sin cambios estructurales sobre sub-NCubes.

## Entregables esperados

| Entregable | Archivo | Estado |
|-----------|---------|--------|
| Planning de la fase | `context/SDD-3/planning.md` | ✅ Este archivo |
| Criterios de DONE | `context/SDD-3/done-criteria.md` | ✅ |
| Notas de implementación | `context/SDD-3/implementation.md` | ✅ |
| Preguntas de validación | `context/SDD-3/testing.md` | ✅ |
| Decisiones de la fase | `context/SDD-3/decisions.md` | ✅ |
| Clase KQNodes implementada | `code/QNodes/src/strategies/kqnodes.py` | 🔴 Pendiente |
| Tests de regresión/monotonicidad | `code/QNodes/tests/` | 🔴 Pendiente |
| CSV de resultados | `code/QNodes/results/kqnodes_*.csv` | 🔴 Pendiente |
| Handoff de cierre | `context/handoffs/03.md` | 🔴 Pendiente (al cerrar) |

## Documento de diseño de referencia

**`temp/Diseno_KQNodes_Fase3.md`** — diseño matemático y algorítmico completo. Es el insumo principal y tiene prioridad sobre cualquier documento de contexto anterior cuando haya contradicción.
