# Phases

Fases del proyecto en orden, con estado actual de cada una.

---

## Fase 0 — Infraestructura base y bipartición (k=2)

**Estado**: ✅ COMPLETADA

### Descripción
Implementación de las dos estrategias de bipartición originales y toda la infraestructura compartida.

### Entregables completados
- `SIA` (clase abstracta base) en ambos sub-proyectos.
- `System`, `NCube`, `Solution`, `Manager`: modelo de dominio completo.
- `GeometricSIA`: estrategia geométrica-topológica para bipartición.
- `QNodes` (con oracle Queyranne + MAO): estrategia submodular para bipartición.
- `BruteForce`: búsqueda exhaustiva para validación.
- Pipeline de ejecución batch desde Excel (`DatosPruebas2026_1.xlsx`).
- Resultados en CSV para n=8 y n=10 en ambas estrategias.
- Profiling con pyinstrument integrado.
- Logging estructurado por fecha/hora.

---

## Fase 1 — Comprensión profunda del proyecto

**Estado**: ✅ COMPLETADA
**Cierre**: 2026-06-05

### Descripción
Entender a fondo el código existente antes de modificar nada: flujo de ejecución, contratos entre módulos, puntos de extensión y deuda técnica conocida.

### Tareas

1. Leer y trazar el flujo completo de ejecución: `exec.py → iniciar() → Estrategia.aplicar_estrategia()`.
2. Verificar contratos de `SIA`, `System`, `NCube`, `Solution`, `Manager` en ambos sub-proyectos.
3. Identificar diferencias reales (no solo documentadas) entre GeoMIP y QNodes.
4. Mapear deuda técnica: `print()` en producción, falta de tests, TODOs, código duplicado.
5. Documentar en `context/state/` el estado actual y los problemas encontrados.
6. Aclarar las decisiones bloqueantes para k-particiones (función φ, extensión de Queyranne).

### Criterio de DONE
- El agente puede explicar el flujo completo sin leer el código.
- `context/state/known-issues.md` actualizado con todos los problemas identificados.
- Decisiones bloqueantes resueltas o formalmente documentadas como pendientes.

### Resultados obtenidos
- Flujo trazado: `exec.py → iniciar() → Manager → SIA → aplicar_estrategia() → Solution` para GeoMIP y QNodes.
- 12/12 preguntas de comprensión respondidas correctamente en `context/SDD-1/testing.md`.
- 9 issues de deuda técnica (DT-01 a DT-09) catalogados en `context/state/known-issues.md`.
- 4 decisiones bloqueantes resueltas en `context/SDD-1/decisions.md` (DB-01 a DB-04).
- Carpeta renombrada de `SDD-0` → `SDD-1` para reflejar la fase correcta.

---

## Fase 2 — Validación del funcionamiento

**Estado**: ✅ COMPLETADA
**Cierre**: 2026-06-05

### Descripción
Verificar que el código existente funciona correctamente antes de extenderlo. Corregir errores que impidan ejecución limpia.

### Tareas

1. Ejecutar `GeoMIP/exec.py` para n=5 y n=8; verificar CSV de resultados.
2. Ejecutar `QNodes/exec.py` para n=5 y n=8; verificar CSV de resultados.
3. Comparar resultados de GeoMIP vs QNodes vs BruteForce para n≤6 (ground-truth).
4. Confirmar que el profiling HTML se genera correctamente.
6. Documentar toda discrepancia en `context/state/known-issues.md`.

### Criterio de DONE
- Ambas estrategias ejecutan sin errores para n ∈ {5, 8}.
- Al menos un caso de n=5 validado contra BruteForce con `|φ_nuevo - φ_ref| < 1e-9`.
- CSV de resultados verificados y coherentes.

### Resultados obtenidos
- GeoMIP ejecuta sin errores para n ∈ {5, 8, 10, 15, 20}; CSV verificados en `code/GeoMIP/results/`.
- QNodes ejecuta sin errores para n ∈ {5, 8, 10, 15, 20, 22}; CSV verificados en `code/QNodes/results/`.
- Bug DT-10 corregido: inversión de ejes en oracle Queyranne y parser de particiones de QNodes. Commit `b2b00e1`.
- Comparación vs BruteForce para n ∈ {5, 8}: exactitud φ = 100%, Δφ = 0.000000 en todos los casos. Resultados en `code/tests/results/{geomip,qnodes}/vs_bruteforce/`.
- Profiling HTML verificado: 214 KB, 870 entradas, tiempos reales. En `code/GeoMIP/review/profiling/`.
- GeoMIP N8A (φ=0.0 en 49/49 casos) confirmado como comportamiento correcto del lote sampleA: todos los sistemas tienen partición natural.
- 2 nuevos issues de deuda técnica documentados: DT-10 (corregido) y DT-11 (archivos legacy).

---

## Fase 3 — Extensión KQNodes (k-particiones submodular)

**Estado**: ✅ COMPLETADA
**Inicio**: 2026-06-07
**Cierre**: 2026-06-07

### Descripción
Extender QNodes al caso k-particiones con k ∈ {2,3,4,5}, reutilizando el oracle y MAO existentes. **Se prioriza KQNodes sobre KGeoMIP** por su mejor complejidad algorítmica (O(k·D³) extendible iterativamente) y por no tener los problemas de escalabilidad de la tabla de transiciones geométrica (ver DEC-10). El criterio de selección es **C4 (corte marginal mínimo)**: bipartir la parte cuyo mejor corte es el más barato — el único criterio alineado con minimizar Φ. Ver DEC-12 corregido.

### Tareas

1. **`KQNodes`**: implementar `KQNodes(SIA).aplicar_estrategia(k)` con criterio C4 (MinHeap por φ_local).
2. **Variante C1**: conservar como opción para A/B testing experimental (`criterio='C1'`).
3. **Remapeo de máscaras**: implementar oracle restringido f|_{Pi} con remapeo de índices global → local (§4.3 del documento de diseño).
4. **Caché por bloque**: instanciar caché fresh por cada llamada a QNodes; no compartir globalmente (D3-02).
5. **Tests de regresión**: `KQNodes(k=2) == QNodes` para n ∈ {5,8,10}, tolerancia 1e-9.
6. **Tests de monotonicidad**: `φ(k+1) ≥ φ(k)` para k ∈ {2,3,4} — dirección corregida (no `≤`).
7. **Medición de gap vs BruteForce**: gap = φ_greedy − φ* ≥ 0 y tasa de acierto exacto para k ∈ {3,4}, n ≤ 6.
8. **A/B testing C1 vs C4**: comparar gap medio y % acierto para evidencia experimental (rúbrica).
9. **Resultados experimentales**: CSV para k ∈ {2,3,4,5}, n ∈ {5,8,10}.

### Criterio de DONE
- Regresión k=2 pasa (KQNodes(k=2) == QNodes, tolerancia 1e-9).
- Monotonicidad **φ(k+1) ≥ φ(k)** verificada para k ∈ {2,3,4} — assert con dirección correcta.
- Gap de optimalidad φ_greedy − φ* ≥ 0 medido y tasa de acierto exacto reportada para k ∈ {3,4}, n ≤ 6 (no exigir igualdad exacta).
- A/B testing C1 vs C4 ejecutado y comparación documentada.
- CSV de resultados para k ∈ {2,3,4,5}, n ∈ {5,8,10} generados.
- Cobertura ≥ 85% en módulo KQNodes.
- Tipado completo (mypy) y docstrings en todos los métodos públicos.
- Ver criterios completos en `context/SDD-3/done-criteria.md`.

---

## Fase 4 — Extensión KGeoMIP (k-particiones geométrica)

**Estado**: 🟡 EN CURSO
**Inicio**: 2026-06-08
**Cierre**: —

### Descripción
Extender GeoMIP al caso k-particiones con k ∈ {2,3,4,5} usando la heurística **E4**: refinamiento divisivo top-down anclado en GeoMIP (k=2 exacto por construcción), con la matriz de similitud S derivada de T como guía global y la EMD vía T para confirmar cada corte (criterio de corte marginal mínimo, min ΔΦ). Se implementa después de KQNodes. La firma de KGeoMIP es la matriz S — lo que la distingue de KQNodes.

### Tareas

1. **Pre-requisito**: verificar la función EMD de GeoMIP en producción (caveat D4-04) antes de cualquier test.
2. **Construir S**: matriz de similitud n×n desde T, una sola vez por sistema: `S[Xᵢ][Xⱼ] = (sim(Xᵢ,Xⱼ) + sim(Xⱼ,Xᵢ)) / 2`, con `sim(Xᵢ,Xⱼ) = Σ_{δ: bit Xⱼ activo} T[Xᵢ][δ]`.
3. **`KGeoMIP(SIA).aplicar_estrategia(k)`**: heurística E4 completa (Fases 0-4 del pseudocódigo); recibe Manager como GeoMIP.
4. **Anclaje k=2**: delegar exactamente en `GeoMIP_bipartir(V, T)` sin pasos adicionales (regresión por construcción).
5. **MinHeap por min ΔΦ**: cola de prioridad con clave `(ΔΦ, bfs_order, |P|, min_idx(P))`; subrutina MejorCorte (S propone + candidatos BFS GeoMIP; EMD confirma).
6. **Marginalización correcta**: columnas SUMAR; filas descartadas PROMEDIAR; sin normalizar; ⊗ del proyecto (expande columnas, no Kronecker).
7. **EMD final**: una sola llamada al final sobre la distribución completa reconstruida.
8. **Estrategia A (baseline)**: clustering aglomerativo sobre S para A/B testing.
9. **Tests de regresión**: `KGeoMIP(k=2) == GeoMIP` para n ∈ {5,8,10}, tolerancia 1e-9.
10. **Tests de monotonicidad**: `φ(k+1) ≥ φ(k)` para k ∈ {2,3,4} — dirección **≥**, no ≤.
11. **Gap vs BruteForce**: gap = φ_E4 − φ* ≥ 0 y tasa de acierto exacto para k ∈ {3,4}, n ≤ 6.
12. **A/B testing E4 vs Estrategia A**: comparar gap medio y % acierto para k ∈ {3,4}.
13. **Resultados experimentales**: CSV para k ∈ {2,3,4,5}, n ∈ {5,8,10}, incluyendo Φ(k) y ΔΦ(k).

### Criterio de DONE
- **Regresión k=2**: KGeoMIP(k=2) == GeoMIP para n ∈ {5,8,10}, tolerancia 1e-9.
- **Monotonicidad**: φ(k+1) ≥ φ(k) para k ∈ {2,3,4} — assert con dirección correcta ≥.
- **Gap de optimalidad**: φ_E4 − φ* ≥ 0 medido y tasa de acierto exacto reportada para k ∈ {3,4}, n ≤ 6 (no exigir igualdad exacta).
- **A/B testing E4 vs Estrategia A**: ejecutado y comparación documentada para k ∈ {3,4}.
- **Función EMD consistente**: verificada como la misma que usa GeoMIP en producción.
- **CSV de resultados** para k ∈ {2,3,4,5}, n ∈ {5,8,10} generados (con Φ(k) y ΔΦ(k)).
- Cobertura ≥ 85% en módulo KGeoMIP.
- Tipado completo (mypy) y docstrings en todos los métodos públicos.
- Ver criterios completos en `context/SDD-4/done-criteria.md`.

---

## Fase 5 — Optimización y limpieza del código existente

**Estado**: 🔴 PENDIENTE

### Descripción
Mejorar la calidad del código existente sin cambiar comportamiento: eliminar deuda técnica, agregar tests, reemplazar prints, una vez finalizadas las extensiones k principales.

### Tareas

1. Reemplazar todos los `print()` de producción por `SafeLogger` (ver R-08, especialmente `ncube.py`).
2. Escribir tests de regresión para `QNodes(k=2)` en `code/QNodes/tests/` (ver R-09).
3. Escribir tests de regresión para `GeometricSIA(k=2)` en `code/GeoMIP/`.
4. Verificar cobertura ≥ 85% en módulos críticos (`System`, `NCube`, estrategias).
5. Eliminar código duplicado evidente entre GeoMIP y QNodes donde sea posible sin romper arquitectura.
6. Resolver todas las issues de tipado detectadas por mypy.

### Criterio de DONE
- Sin `print()` en código de producción.
- Tests de regresión k=2 pasan en ambos sub-proyectos.
- Cobertura ≥ 85% en módulos core.
- mypy sin errores críticos.

---

## Fase 6 — Integración y validación cruzada

**Estado**: 🔴 PENDIENTE

### Descripción
Comparar KQNodes vs KGeoMIP, generar tablas/gráficas y validar métricas globales.

### Tareas

1. Tests E2E con CLI o scripts batch.
2. Comparativa de speedup KQNodes vs KGeoMIP vs BruteForce para n ∈ {5,8,10}.
3. Gráficas: tiempo vs n, tiempo vs k, curvas de precisión.
4. Tablas resumen para incrustar en LaTeX.
5. Verificación de todas las métricas de calidad (tasa acierto, error relativo, Jaccard, speedup).

---

## Fase 7 — Documentación

**Estado**: 🔴 PENDIENTE

### Descripción
Manual técnico y manual de usuario en LaTeX.

### Tareas

1. **Manual técnico** (`docs/manual_tecnico/`): resumen ejecutivo, fundamentos teóricos, arquitectura UML, diseño algorítmico, resultados experimentales, limitaciones.
2. **Manual de usuario** (`docs/manual_usuario/`): requisitos, instalación, guía de uso, troubleshooting, ejemplos.
3. **Video tutorial**: MP4 8-15 min, 1280×720 mínimo, con subtítulos en español.
4. **Subsección de uso de IA**: en manual técnico, transparente sobre herramientas y prompts usados.
