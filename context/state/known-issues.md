# Known Issues — Fase 1

Última actualización: 2026-06-05 (cierre de fase)

> Este archivo se actualiza durante la Fase 1 a medida que se identifican problemas.
> En Fase 2 (Validación) se agregarán discrepancias de resultados.

---

## Deuda técnica (código)

| ID | Archivo(s) | Descripción | Severidad | Estado |
|----|-----------|-------------|-----------|--------|
| DT-01 | `GeoMIP/src/controllers/manager.py`, `main.py`, `models/core/solution.py`, `controllers/strategies/geometric.py`, `controllers/strategies/force.py`, `funcs/system.py` / equivalentes en QNodes | `print()` en producción — 16 instancias en GeoMIP, 17 en QNodes (33 en total). Distribuidas en `manager.py` (7 en cada proyecto), `main.py`, `solution.py`, `force.py`, `geometric.py` y `system.py`. Varios comentados con `# print(...)`. | Media | ✅ Verificado |
| DT-02 | Principalmente `GeoMIP/src/funcs/format.py`, `QNodes/src/funcs/format.py` | Métodos sin type hints completos en firmas públicas. Las clases principales (`System`, `NCube`, `SIA`, `Manager`, `Solution`) tienen type hints correctos. Los helpers menores de `format.py` carecen de anotaciones de retorno. | Baja | ✅ Verificado |
| DT-03 | `code/GeoMIP/src/models/core/` vs `code/QNodes/src/models/core/` | `System`, `Solution` y `Manager` son prácticamente idénticos entre sub-proyectos. `NCube` difiere solo en el campo `memo: dict` (caching) presente en QNodes y ausente en GeoMIP. La duplicación total afecta ~4 archivos de modelos. | Alta | ✅ Verificado |
| DT-04 | — | No se encontraron TODOs ni FIXMEs formales en el código de ninguno de los dos sub-proyectos. La deuda informal está capturada en los comentarios `#!` (DT-05) y en el código muerto de `geometric.py` (DT-07). | Media | ✅ Verificado — sin TODOs activos |
| DT-05 | `code/GeoMIP/src/models/base/sia.py:61,90` | Líneas comentadas `#! COMENTAR / DESCOMENTAR` en producción — toggle manual del modo de carga TPM. | Baja | ✅ Identificado |
| DT-06 | `code/GeoMIP/src/controllers/strategies/geometric.py:51-61` | Docstring como prosa de diseño, sin contrato formal (entradas/salidas). | Baja | ✅ Identificado |
| DT-07 | `code/GeoMIP/src/controllers/strategies/geometric.py:~200-230` | Bloque grande de código comentado (`# presentes_1 = ...`, etc.) — código muerto. | Baja | ✅ Identificado |
| DT-08 | `code/QNodes/src/controllers/manager.py:63-76` | `cargar_red()` llama `np.genfromtxt(...)` en línea 64 y sobreescribe inmediatamente con `np.loadtxt(...)` en línea 72. La primera llamada es código muerto que lee el archivo entero desde disco sin usar el resultado. | Media | ✅ Identificado |
| DT-09 | `code/GeoMIP/src/models/core/solution.py` | `Solution` inicializa un motor de síntesis de voz `pyttsx3` con `hablar=True` por defecto. Rompe responsabilidad única y hace imposible el uso headless/paralelo sin efectos de audio. | Media | ✅ Identificado |

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
| DB-01 | ¿Función φ para k-particiones: suma, máximo o EMD generalizada? | Define el contrato de `KQNodes.aplicar_estrategia()` | ✔ Resuelto — Opción D (Mínima corte) |
| DB-02 | ¿Extensión de Queyranne a k>2: iterativa con re-fusión o multi-vía? | Define la estructura del algoritmo en KQNodes | ✔ Resuelto — Opción A (Iterativa, greedy k-way) |
| DB-03 | ¿Validación de optimalidad para k>2 sin ground-truth en PyPhi? | Define la estrategia de testing de KQNodes | ✔ Resuelto — Opción C (BruteForce n≤6 + consistencia interna) |
| DB-04 | ¿Estrategia de generación de k-particiones candidatas desde N-Cubos? | Necesario antes de implementar KGeoMIP | ✔ Resuelto — Opción A (Partición jerárquica de N-Cubos) |

---

## Leyenda

- 🔍 Por verificar
- ✅ Identificado / Verificado
- 📋 Documentado
- ⛔ Bloqueante
- ✔ Resuelto
