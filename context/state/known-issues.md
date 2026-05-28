# Known Issues — Fase 1

Última actualización: 2026-05-27 (inicio de fase)

> Este archivo se actualiza durante la Fase 1 a medida que se identifican problemas.
> En Fase 2 (Validación) se agregarán discrepancias de resultados.

---

## Deuda técnica (código)

| ID | Archivo | Descripción | Severidad | Estado |
|----|---------|-------------|-----------|--------|
| DT-01 | Por identificar | `print()` en producción (detectados por lectura de código) | Media | 🔍 Por verificar |
| DT-02 | Por identificar | Métodos sin type hints en firmas públicas | Baja | 🔍 Por verificar |
| DT-03 | Por identificar | Código duplicado entre GeoMIP y QNodes (System, NCube, Solution) | Alta | 🔍 Por verificar |
| DT-04 | Por identificar | TODOs / FIXMEs sin resolver | Media | 🔍 Por verificar |
| DT-05 | `code/GeoMIP/src/models/base/sia.py:61,90` | Líneas comentadas `#! COMENTAR / DESCOMENTAR` en producción | Baja | ✅ Identificado |

---

## Problemas de arquitectura

| ID | Descripción | Impacto en k-particiones | Estado |
|----|-------------|--------------------------|--------|
| AR-01 | `SIA.__init__` difiere entre GeoMIP (recibe `Manager`) y QNodes (recibe `tpm`) | KQNodes y KGeoMIP tendrán interfaces distintas | 📋 Documentado (DEC-02) |
| AR-02 | Estrategias de GeoMIP en `controllers/strategies/` vs QNodes en `strategies/` | Inconsistencia estructural al crear KGeoMIP/KQNodes | 📋 Documentado |

---

## Decisiones bloqueantes (para k-particiones)

| ID | Pregunta | Impacto | Estado |
|----|----------|---------|--------|
| DB-01 | ¿Función φ para k-particiones: suma, máximo o EMD generalizada? | Define el contrato de `KQNodes.aplicar_estrategia()` | ⛔ Esperando usuario |
| DB-02 | ¿Extensión de Queyranne a k>2: iterativa con re-fusión o multi-vía? | Define la estructura del algoritmo en KQNodes | ⛔ Esperando usuario |
| DB-03 | ¿Validación de optimalidad para k>2 sin ground-truth en PyPhi? | Define la estrategia de testing de KQNodes | ⛔ Esperando usuario |
| DB-04 | ¿Estrategia de generación de k-particiones candidatas desde N-Cubos? | Necesario antes de implementar KGeoMIP | ⛔ Esperando usuario |

---

## Leyenda

- 🔍 Por verificar
- ✅ Identificado
- 📋 Documentado
- ⛔ Bloqueante
- ✔ Resuelto
