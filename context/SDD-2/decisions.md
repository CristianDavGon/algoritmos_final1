# SDD-2 — Decisions: Validación del funcionamiento

**Fase**: 2  
**Estado**: ✅ COMPLETADA

---

## Decisiones tomadas en Fase 2

| ID | Decisión | Razonamiento |
|----|----------|--------------|
| DEC-F2-01 | Conservar archivos CSV legacy pre-fix DT-10 (N8A, N15A vacíos) en lugar de eliminarlos. | Son evidencia del estado pre-corrección y permiten auditar el impacto del bug. Documentados como DT-11. |
| DEC-F2-02 | Extender ejecuciones a n ∈ {10, 15, 20, 22} aunque no estaba en el alcance original. | Los criterios de DONE del alcance base ya estaban cumplidos y el costo de ejecución era bajo. Amplía la base experimental para Fase 6. |
| DEC-F2-03 | Generar TPMs para n ∈ {20, 22, 25} como preparación para ejecuciones futuras. | Evita regeneración costosa en fases posteriores. No modifica código de producción. |
| DEC-F2-04 | Confirmar GeoMIP N8A φ=0.0 como correcto (no como bug) antes de documentar como issue. | La verificación cruzada con BruteForce y QNodes sobre el mismo lote es suficiente evidencia. No abrir un issue sin fundamento. |
