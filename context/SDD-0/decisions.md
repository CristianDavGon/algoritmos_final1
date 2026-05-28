# SDD-0 — Decisions: Fase 1

Decisiones que deben resolverse durante esta fase para desbloquear la implementación de k-particiones.

---

## DB-01 — Función de pérdida φ para k-particiones

**Pregunta**: Cuando una bipartición (k=2) divide el sistema en 2 partes y calcula φ = EMD(distribución_completa, distribución_bipartida), ¿cómo se define φ para k>2?

**Opciones**:
- **A) Suma**: φ(k) = Σ EMD(distribución_completa, distribución_parte_i) para i=1..k
- **B) Máximo**: φ(k) = max(EMD_i)
- **C) EMD generalizada**: se reformula la EMD para distribuciones k-partidas
- **D) Mínima corte**: se busca la bipartición de menor pérdida entre todos los pares posibles en la k-partición

**Impacto**: Define el contrato de retorno de `KQNodes.aplicar_estrategia()` y `KGeoMIP.aplicar_estrategia()`.

**Estado**: ⛔ Esperando respuesta del usuario

**Respuesta del usuario**:
> _[pendiente]_

---

## DB-02 — Extensión del algoritmo Queyranne a k>2

**Pregunta**: El MAO de Queyranne encuentra la bipartición óptima (2 partes). Para k-particiones, hay dos estrategias:

**Opciones**:
- **A) Iterativa con re-fusión (greedy k-way)**: aplicar MAO k-1 veces. En cada iteración, el "ganador" de la bipartición se fusiona con el resto y se repite. Similar a la construcción de árboles de Gomory-Hu.
- **B) Formulación multi-vía directa**: redefinir la función objetivo para minimizar simultáneamente sobre k partes. Requiere extensión matemática más compleja.

**Impacto**: Define la estructura del bucle principal de `KQNodes.aplicar_estrategia()` y la complejidad resultante (A → O(k·D³), B → O(D³·k^?) ).

**Estado**: ⛔ Esperando respuesta del usuario

**Respuesta del usuario**:
> _[pendiente]_

---

## DB-03 — Validación de optimalidad para k>2 (sin ground-truth en PyPhi)

**Contexto**: PyPhi solo soporta biparticiones (k=2), por lo que no hay ground-truth disponible para k>2.

**Pregunta**: ¿Cómo validamos que KQNodes y KGeoMIP son correctas para k>2?

**Opciones**:
- **A) BruteForce propio**: implementar búsqueda exhaustiva de k-particiones para n≤6 y comparar.
- **B) Consistencia interna**: verificar que φ(k+1) ≤ φ(k) para todo k (la partición más fina nunca sube el costo).
- **C) Ambas**: BruteForce para n≤6, consistencia interna para n>6.

**Impacto**: Define los tests de `code/KQNodes/tests/` y `code/KGeoMIP/tests/`.

**Estado**: ⛔ Esperando respuesta del usuario

**Respuesta del usuario**:
> _[pendiente]_

---

## DB-04 — Generación de k-particiones candidatas para KGeoMIP

**Contexto**: GeoMIP genera candidatos a bipartición usando la tabla de transiciones Hamming y distancias desde el estado inicial al final. Para k>2, el espacio de particiones crece exponencialmente.

**Pregunta**: ¿Cómo se generan los candidatos a k-partición desde la tabla de transiciones Hamming?

**Opciones**:
- **A) Partición jerárquica de N-Cubos**: subdividir recursivamente el hipercubo por los k-1 mejores cortes geométricos.
- **B) Clustering de estados**: aplicar k-means o clustering jerárquico sobre los vectores de costo de la tabla de transiciones.
- **C) Combinatoria controlada**: generar todas las particiones de n elementos en k subconjuntos para n≤8, filtradas por costo Hamming mínimo.

**Impacto**: Define `KGeoMIP.identificar_particiones_optimas()` y su complejidad para k>2.

**Estado**: ⛔ Esperando respuesta del usuario

**Respuesta del usuario**:
> _[pendiente]_

---

## Historial de decisiones ya tomadas (referencia)

Ver `context/project/decisions.md` — DEC-01 a DEC-10 son las decisiones globales del proyecto ya resueltas.
