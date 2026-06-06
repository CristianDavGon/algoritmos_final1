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

## Issues encontradas en Fase 2

### Deuda técnica y bugs

| ID | Archivo(s) | Descripción | Severidad | Estado |
|----|-----------|-------------|-----------|--------|
| DT-10 | `code/QNodes/src/controllers/strategies/qnodes.py` (oracle y parser de particiones) | Bug: inversión de ejes en el oracle Queyranne y en el parser de particiones de QNodes. Causaba resultados incorrectos (φ erróneo) al procesar la TPM con ejes invertidos. Corregido en commit `b2b00e1`. | Alta | ✅ Corregido |
| DT-11 | `code/QNodes/results/resultados_N8A.csv`, `code/QNodes/results/resultados_N15A.csv` | Archivos CSV vacíos (sin datos de φ ni tiempo) generados antes de la corrección DT-10. Son archivos legacy de runs fallidos. Los runs válidos post-fix son N8B y N15B respectivamente. | Baja | ✅ Documentado — archivos legacy |

### Discrepancias entre GeoMIP y QNodes

| n | Rango φ GeoMIP | Rango φ QNodes | Observación |
|---|---------------|---------------|-------------|
| 5 | 0.0 – 0.500 | 0.0 – 0.25 | Rangos distintos. Las tandas A (GeoMIP) y B (QNodes) corresponden a lotes distintos de TPMs — no son casos comparables directamente. |
| 8 | **0.0 – 0.0 ⚠️** | 0.0 – 1.0 (N8B) | GeoMIP N8A produce φ=0.0 para los 49 casos. QNodes N8B cubre [0, 1]. Se requiere verificar si los lotes de TPMs son iguales o si existe un problema en GeoMIP para n=8. |
| 10 | 0.00391 – 0.484 | 0.00586 – 0.480 | Rangos comparables. Sin comparación caso a caso disponible. |
| 15 | 0.0 – 7.61e-4 (A) / 0.0 – 1.51e-3 (B) | 0.0 – 0.270 (B) | Rangos muy distintos. GeoMIP N15A/B tienen φ max muy bajo vs QNodes N15B (0.27). Probable causa: lotes de TPMs distintos. |
| 20 | 2.86e-5 – 0.499 (A) | 2.86e-5 – 0.499 (B) | Rangos idénticos — probable coincidencia de muestras o mismo lote. |

> ⚠️ **GeoMIP N8A — φ=0 en todos los casos**: 49 de 49 sistemas del lote A para n=8 tienen φ=0.0. Esto puede indicar que el lote A de n=8 contiene exclusivamente sistemas con partición natural (φ=0), o que existe un problema en la estrategia geométrica para ese tamaño. Se recomienda comparar los IDs de casos GeoMIP N8A vs QNodes N8B para el mismo lote antes de descartar un bug.

### N15B vs N15A

- **GeoMIP N15A**: φ ∈ [0.0, 7.61e-4], T̄ ≈ 0.597 s
- **GeoMIP N15B**: φ ∈ [0.0, 1.51e-3], T̄ ≈ 0.729 s — φ max ~2× el de N15A. Consistente con muestras distintas del mismo espacio. No se considera una discrepancia preocupante.
- **QNodes N15B**: φ ∈ [0.0, 0.270], T̄ ≈ 0.0139 s — mucho más rápido que GeoMIP (≈42×) y con φ max muy superior. Diferencia atribuida a lotes distintos de TPMs y diferencia algorítmica.

---

## Leyenda

- 🔍 Por verificar
- ✅ Identificado / Verificado
- 📋 Documentado
- ⛔ Bloqueante
- ✔ Resuelto
