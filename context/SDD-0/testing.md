# SDD-0 — Testing: Verificación de comprensión (Fase 1)

> Instrucción: Lee los archivos indicados en `planning.md` y responde cada pregunta.
> Un criterio de DONE para la fase es responder correctamente ≥7 de las 10.
> Escribe tu respuesta debajo de cada pregunta. No consultes el código al responder.

---

## Preguntas de flujo de ejecución

### P1 — Entry point
¿Qué hace `exec.py` en GeoMIP exactamente antes de llamar a `iniciar()`? ¿Qué configuración establece?

**Tu respuesta**:
> _[pendiente]_

---

### P2 — Lectura de datos
¿De dónde vienen los parámetros `alcance` y `mecanismo` que se pasan a `aplicar_estrategia()`? ¿En qué formato están (string, lista, binario)?

**Tu respuesta**:
> _[pendiente]_

---

### P3 — Rol de Manager
¿Cuáles son las tres responsabilidades principales de `Manager` en GeoMIP? ¿Qué atributo es diferente en `Manager` de QNodes?

**Tu respuesta**:
> _[pendiente]_

---

### P4 — Preparación del subsistema
Dado `condicion="11100000"`, `alcance="11100000"`, `mecanismo="11100000"` para n=8:
¿Cuántos NCubes tendrá el subsistema resultante? ¿Cuáles dimensiones se condicionan?

**Tu respuesta**:
> _[pendiente]_

---

### P5 — NCube
¿Qué forma (`shape`) tiene `NCube.data` para un sistema con n=8 antes de condicionar? ¿Y después de marginalizar 5 dimensiones?

**Tu respuesta**:
> _[pendiente]_

---

### P6 — Algoritmo geométrico
En `GeometricSIA.find_mip()`, ¿qué representa `tabla_transiciones[(estado_ini, estado_fin)]`? ¿Cuántos elementos tiene la lista (valor)?

**Tu respuesta**:
> _[pendiente]_

---

### P7 — Algoritmo QNodes
¿Qué calcula `oracle.f(mask_a)`? ¿Por qué se llama "lazy"? ¿Cuántas evaluaciones únicas realiza el MAO en total?

**Tu respuesta**:
> _[pendiente]_

---

### P8 — Diferencia clave
¿Cuál es la diferencia más importante entre cómo GeoMIP y QNodes reciben la TPM? ¿En qué línea de código de cada uno se carga/recibe la TPM?

**Tu respuesta**:
> _[pendiente]_

---

### P9 — EMD
¿Qué compara `emd_efecto(dist_particion, dist_subsistema)`? ¿Qué significa φ=0?

**Tu respuesta**:
> _[pendiente]_

---

### P10 — Resultado
¿Qué contiene un objeto `Solution` al final de `aplicar_estrategia()`? Menciona al menos 4 atributos y qué representan.

**Tu respuesta**:
> _[pendiente]_

---

## Preguntas de deuda técnica

### P11 — Deuda detectada
Menciona 3 problemas de calidad de código que encontraste leyendo el código. Para cada uno: archivo, descripción y por qué es un problema.

**Tu respuesta**:
> _[pendiente]_

---

## Preguntas bloqueantes (para k-particiones)

### P12 — Extensión
Si quisieras extender `QNodes` a k=3, ¿cuál sería el primer cambio en el código que tendrías que hacer? ¿Dónde exactamente?

**Tu respuesta**:
> _[pendiente]_

---

## Resultado de la verificación

| Pregunta | Correcta | Nota |
|----------|----------|------|
| P1 | ⬜ | |
| P2 | ⬜ | |
| P3 | ⬜ | |
| P4 | ⬜ | |
| P5 | ⬜ | |
| P6 | ⬜ | |
| P7 | ⬜ | |
| P8 | ⬜ | |
| P9 | ⬜ | |
| P10 | ⬜ | |
| P11 | ⬜ | |
| P12 | ⬜ | |

**Puntaje**: _/12 — DONE si ≥7_
