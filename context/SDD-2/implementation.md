# SDD-2 — Implementation: Validación del funcionamiento

**Fase**: 2  
**Estado**: ✅ COMPLETADA

---

## 1. Ejecuciones realizadas

### GeoMIP (`code/GeoMIP/`)

| n | Archivo CSV | Pruebas | Rango φ | T̄ (s) | Notas |
|---|------------|---------|---------|--------|-------|
| 5 | `geomip/resultados_N5A.csv` | 49 | 0.0 – 0.500 | ~0.00106 | Correcto |
| 8 | `geomip/resultados_N8A.csv` | 49 | 0.0 – 0.0 | ~0.00346 | φ=0 confirmado correcto (ver §3) |
| 10 | `geomip/resultados_N10A.csv` | 49 | 0.00391 – 0.484 | ~0.00745 | |
| 15 | `geomip/resultados_N15A.csv` | 50 | 0.0 – 7.61e-4 | ~0.5965 | |
| 15 | `resultados_N15B.csv` | 50 | 0.0 – 1.51e-3 | ~0.7289 | Lote distinto |
| 20 | `geomip/resultados_N20A.csv` | 50 | 2.86e-5 – 0.499 | ~9.8237 | |

### QNodes (`code/QNodes/`)

| n | Archivo CSV | Pruebas | Rango φ | T̄ (s) | Notas |
|---|------------|---------|---------|--------|-------|
| 5 | `resultados_N5B.csv` | 48 | 0.0 – 0.25 | ~0.0048 | |
| 8 | `resultados_N8A.csv` | 49 | — (vacío) | — | Legacy pre-fix DT-10 |
| 8 | `resultados_N8B.csv` | 49 | 0.0 – 1.0 | ~0.000657 | Post-fix, correcto |
| 10 | `resultados_N10A.csv` | 49 | 0.00586 – 0.480 | ~0.5357 | |
| 15 | `resultados_N15A.csv` | 50 | — (vacío) | — | Legacy pre-fix DT-10 |
| 15 | `resultados_N15B.csv` | 50 | 0.0 – 0.270 | ~0.0139 | Post-fix, correcto |
| 20 | `resultados_N20B.csv` | 50 | 2.86e-5 – 0.499 | ~1.2256 | |
| 22 | `resultados_N22B.csv` | 50 | 3.77e-5 – 0.500 | ~6.3435 | |

---

## 2. Comparación contra BruteForce

Resultados en `code/tests/results/{geomip,qnodes}/vs_bruteforce/`.

| n | Estrategia | Casos | Exactitud φ | Δφ máximo |
|---|-----------|-------|-------------|-----------|
| 5 | GeoMIP | 49 | 100% | 0.000000 |
| 5 | QNodes | 48 | 100% | 0.000000 |
| 8 | GeoMIP | 49 | 100% | 0.000000 |
| 8 | QNodes | 49 | 100% | 0.000000 |

---

## 3. Investigación GeoMIP N8A (φ=0.0 en todos los casos)

**Hallazgo**: Los 49/49 sistemas del sampleA de n=8 tienen φ=0.0 en GeoMIP.  
**Verificación**: BruteForce ejecutado sobre el mismo sampleA devuelve φ=0.0 en los 49 casos. QNodes sobre el mismo sampleA produce resultado idéntico.  
**Conclusión**: El lote sampleA de n=8 contiene exclusivamente sistemas con partición natural. No hay bug en GeoMIP ni en QNodes para este tamaño.

---

## 4. Bug DT-10 — Corrección

**Archivo**: `code/QNodes/src/controllers/strategies/qnodes.py`  
**Descripción**: Inversión de ejes en el oracle Queyranne y en el parser de particiones. Causaba resultados incorrectos al procesar la TPM con ejes transpuestos.  
**Corrección**: Commit `b2b00e1`. Los archivos legacy pre-fix (N8A, N15A) se conservan y están documentados como DT-11 en `known-issues.md`.

---

## 5. Profiling

Verificado con pyinstrument. HTML generado en `code/GeoMIP/review/profiling/`:
- Tamaño: 214 KB
- Entradas: 870
- Tiempos: reales (wall-clock)

---

## 6. Deuda técnica nueva identificada en Fase 2

| ID | Descripción | Estado |
|----|-------------|--------|
| DT-10 | Bug inversión de ejes oracle/parser QNodes | ✅ Corregido (commit `b2b00e1`) |
| DT-11 | Archivos CSV legacy vacíos (N8A, N15A pre-fix DT-10) | Documentado — conservar como evidencia |
