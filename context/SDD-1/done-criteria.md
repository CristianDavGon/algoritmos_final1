# SDD-1 — Done Criteria: Fase 1

La Fase 1 se considera **COMPLETADA** cuando se cumplen todos los siguientes puntos:

---

## Criterios obligatorios

### C1 — Flujo de ejecución trazado
El agente puede describir de memoria (sin leer el código) el flujo completo:
```
exec.py → iniciar() → Manager → SIA → aplicar_estrategia() → Solution
```
para **ambos** sub-proyectos (GeoMIP y QNodes), incluyendo qué dato fluye entre cada paso.

**Verificación**: El agente responde correctamente las 10 preguntas de `context/SDD-1/testing.md`.

---

### C2 — Contratos de módulos documentados
`context/SDD-1/implementation.md` tiene la tabla de contratos completa para:
- `System` (condicionar, substraer, bipartir, distribucion_marginal)
- `NCube` (estructura, invariantes)
- `SIA` (preparar_subsistema, aplicar_estrategia)
- `Manager` (GeoMIP y QNodes — diferencias reales)
- `Solution` (estructura de salida)

**Verificación**: Cada contrato tiene: entrada tipada, salida tipada, invariante.

---

### C3 — Diferencias reales GeoMIP vs QNodes documentadas
`context/SDD-1/implementation.md` contiene la tabla comparativa con al menos 7 diferencias verificadas en código (no solo en documentación).

**Verificación**: Cada fila de la tabla tiene referencia al archivo y línea.

---

### C4 — Deuda técnica catalogada
`context/state/known-issues.md` tiene al menos:
- Todos los `print()` de producción encontrados (con archivo y línea).
- Todos los métodos públicos sin type hints.
- El código duplicado entre GeoMIP y QNodes identificado.
- Los `#!` y bloques comentados documentados.

**Verificación**: Al menos 8 issues registrados con ID, archivo y descripción.

---

### C5 — Decisiones bloqueantes respondidas
Las 4 decisiones de `context/SDD-1/decisions.md` tienen respuesta del usuario:
- DB-01: Función φ para k-particiones.
- DB-02: Extensión Queyranne a k>2.
- DB-03: Estrategia de validación sin ground-truth.
- DB-04: Generación de k-particiones candidatas para KGeoMIP.

**Verificación**: Cada decisión tiene estado `✔ RESUELTA` con la respuesta del usuario registrada.

---

### C6 — Usuario aprueba comprensión
El usuario responde correctamente al menos 7 de las 10 preguntas de `context/SDD-1/testing.md`.

**Verificación**: Respuestas registradas en `testing.md` por el usuario.

---

## Aprobación de salida

Cuando los 6 criterios estén cumplidos, el agente:
1. Actualiza `context/state/current-phase.md` → Fase 2.
2. Actualiza `context/state/progress.md` → todas las tareas de Fase 1 = ✅.
3. ✅ Crea `context/SDD-1/` con el planning de Fase 2 (Validación).
4. Notifica al usuario que puede iniciar la ejecución de las pruebas.

---

## Resultado final

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| C1 — Flujo trazado | ✅ | `implementation.md` secciones 1 y 2 |
| C2 — Contratos documentados | ✅ | `implementation.md` tablas de contratos |
| C3 — Diferencias GeoMIP vs QNodes | ✅ | `implementation.md` tabla comparativa (8 diferencias) |
| C4 — Deuda técnica catalogada | ✅ | `known-issues.md` — DT-01 a DT-09 (9 issues) |
| C5 — Decisiones bloqueantes respondidas | ✅ | `decisions.md` — DB-01 a DB-04 resueltas |
| C6 — Usuario aprueba comprensión | ✅ | `testing.md` — 12/12 preguntas correctas |

**Fecha de cierre**: 2026-06-05
**Aprobación**: ✅ TODOS LOS CRITERIOS CUMPLIDOS
