# SDD-1 — Planning: Comprensión profunda del proyecto

**Fase**: Fase 1
**Objetivo**: Trazar, verificar y documentar el código existente antes de cualquier modificación.

---

## Alcance

Este SDD cubre únicamente las tareas de **lectura y comprensión** del código base actual (GeoMIP y QNodes para k=2). No se escribe ningún código nuevo en esta fase.

---

## Orden de lectura del código

### Bloque A — GeoMIP (prioridad 1)

| Orden | Archivo | Qué buscar |
|-------|---------|------------|
| 1 | `code/GeoMIP/exec.py` | Cómo se configura `Application` y cómo llama a `iniciar()` |
| 2 | `code/GeoMIP/src/main.py` | Cómo se leen las pruebas del Excel, cómo se itera por (alcance, mecanismo) |
| 3 | `code/GeoMIP/src/controllers/manager.py` | Qué expone Manager: rutas, estado_inicial, output_dir, generar_red() |
| 4 | `code/GeoMIP/src/models/base/sia.py` | Contrato abstracto: `aplicar_estrategia()`, `sia_preparar_subsistema()` |
| 5 | `code/GeoMIP/src/models/core/system.py` | System: condicionar, substraer, bipartir, distribucion_marginal |
| 6 | `code/GeoMIP/src/models/core/ncube.py` | NCube: frozen dataclass, shape, dims, data |
| 7 | `code/GeoMIP/src/controllers/strategies/geometric.py` | GeometricSIA: tabla_transiciones, find_mip, calcular_costos_nivel |
| 8 | `code/GeoMIP/src/funcs/base.py` | emd_efecto, ABECEDARY, seleccionar_metrica |
| 9 | `code/GeoMIP/src/models/core/solution.py` | Solution: cómo se construye, qué contiene |

### Bloque B — QNodes (prioridad 2)

| Orden | Archivo | Qué buscar |
|-------|---------|------------|
| 10 | `code/QNodes/exec.py` | Diferencias con GeoMIP/exec.py |
| 11 | `code/QNodes/src/main.py` | `ejecutar_desde_excel()` — diferencias con `iniciar()` de GeoMIP |
| 12 | `code/QNodes/src/controllers/manager.py` | `cargar_red()` vs GeoMIP — diferencia clave en carga de TPM |
| 13 | `code/QNodes/src/models/base/sia.py` | `SIA.__init__` recibe `tpm: np.ndarray` — diferencia con GeoMIP |
| 14 | `code/QNodes/src/strategies/qnodes.py` | oracle, qnodes (MAO), QNodes.aplicar_estrategia |
| 15 | `code/QNodes/src/funcs/iit.py` | emd_efecto en QNodes — ¿idéntico a GeoMIP? |

### Bloque C — Deuda técnica (prioridad 3)

Búsqueda global por: `print(`, `#!`, `TODO`, `FIXME`, `# type: ignore`, `pass`, métodos sin type hints.

---

## Entregables de la fase

1. `context/SDD-1/implementation.md` — flujo anotado y tabla de diferencias
2. `context/SDD-1/decisions.md` — 4 decisiones bloqueantes formalizadas
3. `context/state/known-issues.md` — deuda técnica catalogada
4. `context/SDD-1/testing.md` — preguntas de comprensión respondidas (por el usuario)

---

## Restricciones

- No modificar ningún archivo de `code/` en esta fase.
- Si se detecta un bug obvio: documentarlo en `known-issues.md`, no corregirlo.
- No inferir comportamiento del código — leer y verificar siempre.

## Estado de cierre

**Completado**: 2026-06-05
Todos los entregables generados. Ver `context/state/progress.md` para el tablero de tareas y `context/handoffs/file.md` para el resumen de entrega.
