# SDD-1 — Decisions: Fase 1

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

**Estado**: ✅ Decidido

**Respuesta**:
> **Opción D — Mínima corte**: φ(k) se define como la EMD mínima encontrada al aplicar el algoritmo sobre la k-partición resultante — el mismo principio que k=2 pero aplicado iterativamente sobre el subconjunto restante en cada paso. Esto preserva la interpretación original de φ (la "menor pérdida posible al cortar el sistema"), hace que KQNodes(k=2) sea idéntico a QNodes como test de regresión, y encaja directamente con la estrategia iterativa elegida en DB-02.

---

## DB-02 — Extensión del algoritmo Queyranne a k>2

**Pregunta**: El MAO de Queyranne encuentra la bipartición óptima (2 partes). Para k-particiones, hay dos estrategias:

**Opciones**:
- **A) Iterativa con re-fusión (greedy k-way)**: aplicar MAO k-1 veces. En cada iteración, el "ganador" de la bipartición se fusiona con el resto y se repite. Similar a la construcción de árboles de Gomory-Hu.
- **B) Formulación multi-vía directa**: redefinir la función objetivo para minimizar simultáneamente sobre k partes. Requiere extensión matemática más compleja.

**Impacto**: Define la estructura del bucle principal de `KQNodes.aplicar_estrategia()` y la complejidad resultante (A → O(k·D³), B → O(D³·k^?) ).

**Estado**: ✅ Decidido

**Respuesta**:
> **Opción A — Iterativa con re-fusión (greedy k-way)**: se aplica el MAO k-1 veces. En cada iteración, `qnodes(D, f, full_mask)` obtiene la mejor bipartición `(A, B_rest)`; el subconjunto `B_rest` pasa a ser el input de la siguiente iteración. La complejidad total es O(k·D³), predecible y validable. La opción B requeriría reformular la submodularidad para k partes simultáneas — matemáticamente incierto y sin implementación de referencia disponible. La opción A tiene precedente en la literatura (Gomory-Hu) y es directamente extensible desde el código existente en `qnodes.py`.

---

## DB-03 — Validación de optimalidad para k>2 (sin ground-truth en PyPhi)

**Contexto**: PyPhi solo soporta biparticiones (k=2), por lo que no hay ground-truth disponible para k>2.

**Pregunta**: ¿Cómo validamos que KQNodes y KGeoMIP son correctas para k>2?

**Opciones**:
- **A) BruteForce propio**: implementar búsqueda exhaustiva de k-particiones para n≤6 y comparar.
- **B) Consistencia interna**: verificar que φ(k+1) ≤ φ(k) para todo k (la partición más fina nunca sube el costo).
- **C) Ambas**: BruteForce para n≤6, consistencia interna para n>6.

**Impacto**: Define los tests de `code/KQNodes/tests/` y `code/KGeoMIP/tests/`.

**Estado**: ✅ Decidido

**Respuesta**:
> **Opción C — Ambas**: BruteForce exhaustivo para n≤6 y consistencia interna (`φ(k+1) ≤ φ(k)`) para n>6. El BruteForce para sistemas pequeños da la certeza matemática de que el algoritmo encuentra el óptimo real; la consistencia interna es la única garantía práctica para n>6 donde el BruteForce es computacionalmente inviable. Ya existe infraestructura de BruteForce en `code/GeoMIP/src/controllers/strategies/force.py` y en `code/QNodes/src/strategies/force.py` que se puede extender a k particiones.

---

## DB-04 — Generación de k-particiones candidatas para KGeoMIP

**Contexto**: GeoMIP genera candidatos a bipartición usando la tabla de transiciones Hamming y distancias desde el estado inicial al final. Para k>2, el espacio de particiones crece exponencialmente.

**Pregunta**: ¿Cómo se generan los candidatos a k-partición desde la tabla de transiciones Hamming?

**Opciones**:
- **A) Partición jerárquica de N-Cubos**: subdividir recursivamente el hipercubo por los k-1 mejores cortes geométricos.
- **B) Clustering de estados**: aplicar k-means o clustering jerárquico sobre los vectores de costo de la tabla de transiciones.
- **C) Combinatoria controlada**: generar todas las particiones de n elementos en k subconjuntos para n≤8, filtradas por costo Hamming mínimo.

**Impacto**: Define `KGeoMIP.identificar_particiones_optimas()` y su complejidad para k>2.

**Estado**: ✅ Decidido

**Respuesta**:
> **Opción A — Partición jerárquica de N-Cubos**: se extiende el método geométrico actual aplicando los k-1 mejores cortes de forma recursiva sobre el hipercubo. Es la extensión natural de `identificar_particiones_optimas()` que ya trabaja con la geometría del hipercubo; mantiene la coherencia con la lógica de `tabla_transiciones` y `calcular_costos_nivel()`. La opción B (clustering) introduce dependencia externa (sklearn) y rompe la filosofía geométrica del proyecto. La opción C es computacionalmente viable solo para n≤8 y tiene peor escalabilidad que A para k>3.

---

## Historial de decisiones ya tomadas (referencia)

Ver `context/project/decisions.md` — DEC-01 a DEC-10 son las decisiones globales del proyecto ya resueltas.
