# Instrucciones del Agente — Proyecto K-QGMIP

## Contexto del proyecto

Lee y aplica los siguientes archivos de contexto antes de responder:

- `context/.IA/instructions.md` — Rol, enfoque y flujo de trabajo por fases
- `context/.IA/rules.md` — Reglas que no puedes violar
- `context/.IA/architecture.md` — Arquitectura del sistema
- `context/.IA/stack.md` — Tecnologías y dependencias
- `context/.IA/constraints.md` — Restricciones técnicas
- `context/.IA/directory-structure.md` — Estructura de carpetas y archivos
- `context/project/phases.md` — Fases del proyecto y estado actual
- `context/project/requirements.md` — Requisitos del sistema
- `context/project/decisions.md` — Decisiones tomadas
- `context/project/risks.md` — Riesgos conocidos

## Protocolo de trazabilidad

### Al ejecutar este archivo (inicio de conversación)

Sigue estos pasos en orden:

1. **Crear el archivo de trazabilidad**: crea `traceability_data/[YYYY_MM_DD_HH-MM].md` usando la fecha y hora exacta del momento en que se ejecuta este archivo.
2. **Registrar la primera pregunta**: toma el texto bajo la sección `instrucción:` al final de este archivo y regístralo como `## iteración 1` → `### prompt`.
3. **Limpiar la sección instrucción**: borra únicamente el contenido que está debajo de `instrucción:` en este archivo, dejando el encabezado vacío y listo para la próxima conversación.
4. **Responder** a la pregunta aplicando todo el contexto del proyecto cargado.
5. **Registrar la respuesta**: agrega un resumen de tu respuesta bajo `### respuesta` en la iteración 1 del archivo de trazabilidad.

### Durante la conversación (preguntas subsecuentes)

Por cada nueva pregunta que el usuario haga en este chat, sin que el usuario lo indique:

1. Agrega `## iteración N` al archivo de trazabilidad de esta conversación (incrementando N).
2. Copia la pregunta tal como fue formulada bajo `### prompt`.
3. Responde con el contexto del proyecto.
4. Agrega un resumen de tu respuesta bajo `### respuesta`.

### Formato del archivo de trazabilidad

```md
## iteración 1
### prompt
pregunta tal cual se realizó

### respuesta
Explicación de la IA para el usuario

## iteración 2
### prompt
pregunta tal cual se realizó

### respuesta
Explicación de la IA para el usuario
```

---

## instrucción:
