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

**Estado**: 🟡 EN CURSO

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

---

## Fase 2 — Validación del funcionamiento

**Estado**: 🔴 PENDIENTE

### Descripción
Verificar que el código existente funciona correctamente antes de extenderlo. Corregir errores que impidan ejecución limpia.

### Tareas

1. Ejecutar `GeoMIP/exec.py` para n=5 y n=8; verificar CSV de resultados.
2. Ejecutar `QNodes/exec.py` para n=5 y n=8; verificar CSV de resultados.
3. Comparar resultados de GeoMIP vs QNodes vs BruteForce para n≤6 (ground-truth).
4. Verificar que PyPhi da los mismos φ que las estrategias para k=2 en casos pequeños.
5. Confirmar que el profiling HTML se genera correctamente.
6. Documentar toda discrepancia en `context/state/known-issues.md`.

### Criterio de DONE
- Ambas estrategias ejecutan sin errores para n ∈ {5, 8}.
- Al menos un caso de n=5 validado contra PyPhi/BruteForce con `|φ_nuevo - φ_ref| < 1e-9`.
- CSV de resultados verificados y coherentes.

---

## Fase 3 — Optimización y limpieza del código existente

**Estado**: 🔴 PENDIENTE

### Descripción
Mejorar la calidad del código existente sin cambiar comportamiento: eliminar deuda técnica, agregar tests, reemplazar prints, antes de entrar a las extensiones k.

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

## Fase 4 — Extensión KQNodes (k-particiones submodular)

**Estado**: 🔴 PENDIENTE

### Descripción
Extender QNodes al caso k-particiones, reutilizando el algoritmo Queyranne/MAO. **Se prioriza KQNodes sobre KGeoMIP** por su mejor complejidad algorítmica (O(D³) extendible iterativamente) y por no tener los problemas de escalabilidad de la tabla de transiciones geométrica (ver DEC-10).

### Tareas

1. **Diseño**: definir si la extensión usa Queyranne iterativo con re-fusión o formulación multi-vía. [PENDIENTE: confirmar con el humano]
2. **`KQNodes`**: implementa `aplicar_estrategia()` para k > 2, reutilizando oracle + MAO.
3. **Reutilización**: el oracle y MAO de `src/strategies/qnodes.py` deben reutilizarse sin copiar código.
4. **Tests de regresión**: `KQNodes(k=2) == QNodes`.
5. **Tests de consistencia**: φ(k+1) ≤ φ(k) para k ∈ {2,3,4}.
6. **Resultados experimentales**: CSV para k ∈ {2,3,4,5}, n ∈ {5,8,10}.

### Criterio de DONE
- Regresión k=2 pasa.
- Cobertura ≥ 85%.
- Tipado completo.
- Docstrings en todos los métodos públicos.
- Al menos un CSV de resultados generado.

---

## Fase 5 — Extensión KGeoMIP (k-particiones geométrica)

**Estado**: 🔴 PENDIENTE

### Descripción
Extender GeoMIP al caso k-particiones con `k ∈ {2, 3, 4, 5}`, reutilizando la infraestructura de N-Cubos y la tabla de transiciones. Se implementa después de KQNodes dado que la tabla de transiciones tiene limitaciones de escalabilidad para k>2 (R-03).

### Tareas

1. **Diseño**: definir cómo generar k-particiones candidatas desde los N-Cubos. [PENDIENTE: confirmar estrategia de partición del hipercubo para k > 2]
2. **Modelo `KPartition`**: clase para representar k-particiones con `k` partes disjuntas.
3. **`KGeoMIP`**: implementa `aplicar_estrategia()` para k > 2, reutilizando `tabla_transiciones`.
4. **Cache de tabla T**: garantizar que T se calcule una sola vez por sistema independientemente de k.
5. **Tests de regresión**: `KGeoMIP(k=2) == GeoMIP`, `|φ_nuevo - φ_viejo| < 1e-9`.
6. **Tests unitarios**: generación de k-particiones, cálculo de φ, distancia Jaccard.
7. **Resultados experimentales**: CSV para k ∈ {2,3,4,5}, n ∈ {5,8,10}.

### Criterio de DONE
- Regresión k=2 pasa.
- Cobertura ≥ 85%.
- Tipado completo.
- Docstrings en todos los métodos públicos.
- Al menos un CSV de resultados generado.

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
