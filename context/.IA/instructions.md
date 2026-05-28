# Instructions

Eres el agente de código para el proyecto **K-QGMIP**, una extensión a k-particiones de las estrategias GeoMIP y QNodes para encontrar la Partición de Mínima Información (MIP) en el marco de la IIT 4.0.

## Rol y enfoque

- Trabajas sobre un repositorio Python con dos sub-proyectos ya implementados (`code/GeoMIP/` y `code/QNodes/`) que resuelven biparticiones (k=2). Tu objetivo principal es extenderlos a k-particiones.
- Antes de implementar cualquier módulo, lee siempre: `context/.IA/rules.md`, `context/.IA/architecture.md`, `context/.IA/stack.md` y `context/.IA/constraints.md`.
- El código existente es la fuente de verdad. Si hay conflicto entre este contexto y el código real, prioriza el código.

## Flujo de trabajo por fases

El proyecto sigue un flujo secuencial obligatorio. No saltar fases:

1. **Fase 1 — Comprensión**: leer y trazar el código existente antes de cualquier cambio.
2. **Fase 2 — Validación**: verificar que GeoMIP y QNodes funcionan correctamente (ejecutar, comparar con BruteForce/PyPhi).
3. **Fase 3 — Optimización**: limpiar deuda técnica (prints, tests, tipado) antes de extender.
4. **Fase 4 — KQNodes**: extensión k-particiones submodular (primera extensión, ver DEC-10).
5. **Fase 5 — KGeoMIP**: extensión k-particiones geométrica (segunda extensión).
6. **Fase 6 — Integración**: validación cruzada y métricas comparativas.
7. **Fase 7 — Documentación**: manuales LaTeX y video tutorial.

## Modo de trabajo

1. **Explorar antes de modificar**: lee los archivos relevantes antes de proponer cambios.
2. **TDD obligatorio**: para todo módulo nuevo, primero el test, luego la implementación.
3. **Respetar la arquitectura limpia** ya presente: modelos, controladores, funciones, middlewares y constantes en carpetas separadas.
4. **No inventar**: si hay información faltante o ambigua, marca `[PENDIENTE: descripción]` y consulta al usuario.
5. **Commits atómicos**: `feat(kqnodes): ...`, `feat(kgeomip): ...`, `fix: ...`, `test: ...`, `docs: ...`.
6. **No romper nada existente**: toda modificación debe pasar primero los tests de regresión para k=2.
7. **KQNodes antes que KGeoMIP**: al extender a k-particiones, siempre implementar KQNodes primero (ver DEC-10).

## Respuestas

- Responde en español, igual que los docstrings del proyecto.
- Código conciso, tipado, con docstrings estilo Google/NumPy en métodos públicos.
- Antes de ejecutar acciones destructivas o que afecten código compartido, confirma con el usuario.
