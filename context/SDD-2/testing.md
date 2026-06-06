# SDD-2 — Testing: Validación del funcionamiento

**Fase**: 2  
**Estado**: ✅ COMPLETADA

---

## Preguntas de validación (respondidas al cierre)

| # | Pregunta | Respuesta |
|---|---------|-----------|
| T1 | ¿GeoMIP ejecuta sin excepciones para n=5 y n=8? | Sí. CSVs generados con 49 pruebas cada uno. |
| T2 | ¿QNodes ejecuta sin excepciones para n=5 y n=8? | Sí. N5B (48 pruebas), N8B post-fix DT-10 (49 pruebas). |
| T3 | ¿Qué bug se encontró y corrigió? | DT-10: inversión de ejes en oracle Queyranne y parser de particiones de QNodes. Commit `b2b00e1`. |
| T4 | ¿Cuál es la exactitud de GeoMIP vs BruteForce para n≤6? | 100% en n ∈ {5, 8}. Δφ máximo = 0.000000 en todos los casos. |
| T5 | ¿Cuál es la exactitud de QNodes vs BruteForce para n≤6? | 100% en n ∈ {5, 8}. Δφ máximo = 0.000000 en todos los casos. |
| T6 | ¿Por qué GeoMIP N8A tiene φ=0.0 en los 49 casos? | El lote sampleA de n=8 contiene exclusivamente sistemas con partición natural. Confirmado por BruteForce y QNodes sobre el mismo lote. |
| T7 | ¿Se generó el profiling HTML? | Sí. 214 KB, 870 entradas, tiempos reales. En `code/GeoMIP/review/profiling/`. |
| T8 | ¿Cuántas nuevas issues de deuda técnica se documentaron? | 2: DT-10 (corregido) y DT-11 (archivos CSV legacy, documentado). |
