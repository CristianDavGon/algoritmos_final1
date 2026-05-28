Quiero estructurar la carpeta del proyecto de la siguiente manera:
 
## Arquitectura de carpetas general
 
```
├─ code/ (Código, test y data del proyecto)
├─ traceability_data/ (Trazabilidad del uso de la IA)
├─ context/ (Contexto para la IA)
├─ others/ (Insumos para la IA)
├─ docs/ (Documentación técnica que requiere el proyecto)
```
 
---
## Arquitectura individual
 
### code
 
#### Descripción
Aquí va todo el código del proyecto, que está organizado mediante una arquitectura limpia. El proyecto está manejando el gestor de dependencias uv.
 
#### Organización
```
code/
├─ .logs/ (Registros de ejecución y debugging)
├─ .venv/ (Entorno virtual de Python)
├─ data/ (Datasets y archivos de entrada)
├─ test/ (Pruebas automatizadas)
├─ GeoMIP/ (Implementación de la estrategia geométrica)
├─── KGeoMIP/ (Futura extensión de la estrategia para k-particiones)
├─ QNodes/ (Implementación de la estrategia Queyranne)
├─── KQNodes/(Futura extensión de la estrategia para k-particiones)
├─ review/ (Revisión y análisis de resultados)
```
 
### traceability_data
 
#### Descripción
 
Aquí va todo lo relacionado con el uso de IA, pero principalmente se centra en 2 factores para tener la trazabilidad de la conversación:
 
- Prompt o pregunta que se le realizó (tal cual como se formuló)
- Explicación para el usuario de lo que se realizó
#### Organización
```
traceability_data
├─ [fecha_hora_conversacion]
├─ 2026_06_13_14-00.md
```
 
#### Ejemplo documento
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
 
## iteración 3
...
```
#### Funcionamiento 
Cuando se inicie una conversación se crea este documento y por cada pregunta que el usuario realice a ese chat se va editando y agregando una iteración bajo el mismo formato.
 
 
### context
 
#### Descripción
Aquí estará toda la parte con la que la IA o agente de código interactúa tanto la parte de handoff, fases de desarrollo, instructions, carpetas de sdd.
 
#### Organización
 
```
context
├─ handoffs (memoria temporal entre fases/agentes)
├─── 0.md (resultado/contexto de la fase 0)
├─── 1.md (resultado/contexto de la fase 1)
├─── ...md (resultado/contexto de otras fases)
 
├─ .IA (conocimiento fijo de la IA)
├─── instructions.md (cómo debe actuar)
├─── rules.md (qué no puede romper)
├─── stack.md (tecnologías usadas)
├─── architecture.md (cómo está diseñado el sistema)
├─── coding-standards.md (estándares de código)
├─── constraints.md (límites/restricciones técnicas)
├─── directory-structure.md (estructura de carpetas y archivos)
 
├─ project (visión global del proyecto)
├─── requirements.md (qué debe hacer el sistema)
├─── phases.md (orden y etapas del proyecto)
├─── decisions.md (decisiones globales tomadas)
├─── risks.md (riesgos conocidos)
 
├─ SDD-# (documentación de una feature/módulo)
├─── planning.md (plan de implementación)
├─── implementation.md (qué se implementó realmente)
├─── decisions.md (decisiones de esa feature)
├─── done-criteria.md (cuándo se considera terminado)
├─── testing.md (cómo se prueba)
 

 
├─ state (estado actual del proyecto)
├─── current-phase.md (fase actual)
├─── progress.md (avance general)
├─── active-tasks.md (tareas en curso)
└─── known-issues.md (bugs/problemas conocidos)
```
 
 
### others
 
#### Descripción
 
Aquí se van a tener otros elementos importantes del proyecto, como elementos iniciales que se dieron, explicaciones de manuales, todos los insumos.
 
 
#### Organización
Todavía no se ha definido, esa se da de acuerdo a lo que se da en el proyecto.
 
 
### docs
 
#### Descripción
Aquí estarán todos los manuales solicitados para el proyecto. Cuando se pida que se avance en un manual se trabajará sobre esta carpeta.
 
Los manuales se trabajarán en LaTeX, así que por manual tendrá una carpeta que maneja por secciones.
 
 
#### Organización
 
```
docs
├─ manual_tecnico
├─── sections
├─── main.tex
├─ manual_usuario
├─── sections
├─── main.tex