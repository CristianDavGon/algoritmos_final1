# SDD-3 — Decisions: Fase 3 (KQNodes)

Decisiones específicas de la Fase 3. No duplican lo que ya está en `context/project/decisions.md` (DEC-01 a DEC-14); registran únicamente lo que es específico de KQNodes o que DEC-12/DEC-13 no cubren con suficiente detalle.

---

## D3-01: Criterio de selección C4 sobre C1 — justificación de implementación

**Decisión**: El criterio de selección por defecto es C4 (corte marginal mínimo). C1 (tamaño máximo) se conserva como variante explícita para A/B testing experimental, pero no es el criterio principal.

**Justificación detallada**:
Por la descomposición aditiva del documento de diseño (§1.4): Φ(Π^(k)) = Σ φ_local(cⱼ), donde cada φ_local(cⱼ) ≥ 0 es el incremento de Φ introducido por el corte j. Minimizar Φ es equivalente, bajo esta descomposición, a minimizar la suma de los φ_local de los k−1 cortes elegidos. La estrategia greedy que aproxima mejor este objetivo es C4: en cada paso, elegir el corte de menor φ_local disponible (descenso de máxima pendiente discreta sobre el reticulado de particiones).

C1 ignora φ_local completamente y decide por cardinalidad. El argumento submodular que podría justificar C1 (rendimientos decrecientes al añadir dimensiones) no aplica aquí: describe la ganancia marginal de añadir un elemento al conjunto, no el costo de elegir qué parte cortar. Como cada corte **aumenta** Φ (nunca lo reduce), maximizar la "ganancia submodular" sería equivalente a maximizar el incremento de Φ — lo opuesto al objetivo.

**Consecuencia de implementación**: La clase KQNodes implementa C4 como política por defecto. La variante C1 se implementa como una rama alternativa en `aplicar_estrategia(k, criterio='C4')` con `criterio='C1'` como opción. El test de A/B (criterio C6 de done-criteria.md) es obligatorio para la rúbrica.

---

## D3-02: Caché del oracle por bloque — no compartir globalmente

**Decisión**: El caché del oracle se instancia fresh para cada llamada a QNodes sobre un bloque Pi, y se descarta al terminar esa llamada. No existe un caché global compartido entre bloques.

**Por qué no se puede compartir globalmente**:
El remapeo de máscaras (§4.3 del documento de diseño) transforma índices globales (D bits) a índices locales (|Pi| bits). Tras el remapeo, la misma clave entera puede corresponder a subconjuntos distintos en distintos bloques. Por ejemplo: si Pi = {0, 2} y Pj = {1, 3}, la máscara local `0b01` representa {0} en Pi pero {1} en Pj. Un caché compartido causaría colisiones silenciosas: una consulta para Pj podría retornar el valor calculado para Pi, sin ningún error visible, produciendo φ_local erróneo.

**Costo aceptable**: El caché por bloque tiene costo O(D²) de memoria pico (el MAO toca O(D²) máscaras distintas por llamada). Este overhead es despreciable frente al costo total O(k·D³) de la búsqueda.

**Implementación**: Pasar el diccionario de caché como parámetro a la función del oracle en lugar de usar estado de clase:
```python
cache: dict[int, float] = {}
resultado = qnodes(bloque, lambda mask: oracle(mask, bloque, cache))
# cache se descarta al salir del scope
```

---

## D3-03: Criterio de desempate en C4

**Decisión**: Cuando dos o más partes tienen el mismo φ_local (hasta tolerancia ε = 1e-9 por float32), se aplica el siguiente desempate determinista:
1. **Tamaño mayor**: elegir la parte de mayor cardinalidad |Pi|.
2. **Índice menor**: si persiste el empate de tamaño, elegir la de menor índice canónico (el menor elemento del subconjunto).

**Justificación**:
- A igual costo de corte, la parte más grande tiene más subconjuntos por explorar en pasos futuros y tiende a tener su estructura modular menos resuelta. Esto recupera lo único valioso de C1 pero solo como regla de desempate, no como criterio principal.
- El desempate por índice garantiza determinismo total, complementando la semilla fija `DEC-08` (`semilla_numpy=73`).
- La tolerancia 1e-9 para considerar dos φ_local como iguales es consistente con la precisión de float32 usada en el proyecto.

**Implementación en MinHeap**: la clave de prioridad es la tupla `(φ_local, −|Pi|, min_index(Pi))` donde la comparación lexicográfica implementa el desempate automáticamente (Python compara tuplas elemento a elemento).

---

## D3-04: Posición del cálculo de Φ* — una sola EMD al final

**Decisión**: La función EMD (emd_efecto) se llama exactamente una vez por ejecución de KQNodes: al final del algoritmo, sobre la distribución reconstruida completa ⊗_{Pi∈Π} p_{Pi}.

**Por qué**: Durante la búsqueda (k−1 iteraciones), el oracle restringido ya devuelve φ_local como proxy de Δφ. Este proxy es suficiente para rankear los cortes candidatos (C4 solo necesita el ranking correcto, no el valor exacto de Φ). Calcular la EMD completa en cada iteración sería O(k·2^D) extra — un factor k sobre el costo final — sin beneficio para la calidad de la búsqueda.

Esta es la misma filosofía que QNodes: el MAO guía la búsqueda con el oracle (O(D²) evaluaciones de f, no de EMD), y la EMD completa se calcula solo sobre la partición final.

**Consecuencia de implementación**: `_calcular_phi_total(particion)` es un método separado que se llama exactamente una vez en `aplicar_estrategia()`, después del bucle de refinamiento.

---

## D3-05: Estructura de datos de la partición — frozenset de frozensets

**Decisión**: La partición Π se representa internamente como una lista de `frozenset[int]`, donde cada frozenset contiene los índices globales de dimensiones de esa parte.

**Por qué frozenset**: Las partes no tienen orden interno (los miembros de Pi son un conjunto, no una secuencia). frozenset es hashable y permite usarlo como clave en el MinHeap. La lista de partes mantiene el orden de creación para el desempate por índice de D3-03.

**Alternativa descartada**: representar como máscaras de bits enteras. Más eficiente para el oracle (que trabaja con máscaras), pero más complejo para construir el producto tensorial final y para el remapeo entre niveles. frozenset es más legible y el overhead de conversión mask↔frozenset es insignificante.

---

## D3-06: Interfaz de KQNodes — herencia de SIA con parámetro k en aplicar_estrategia

**Decisión**: `class KQNodes(SIA)` hereda de la misma clase abstracta que QNodes. `aplicar_estrategia(k: int)` recibe k como parámetro (no como atributo de instancia), para mantener la consistencia con la interfaz SIA y permitir llamar al mismo objeto con distintos k.

**Por qué**: La interfaz de QNodes recibe la TPM directamente en `__init__` (DEC-02). KQNodes sigue el mismo patrón. El parámetro k en `aplicar_estrategia` es análogo a cómo GeoMIP podría recibir parámetros de búsqueda — no rompe el contrato de SIA si la firma base tiene `**kwargs`.

**Validación de k**: `aplicar_estrategia` debe validar que 2 ≤ k ≤ D (no tiene sentido k > número de dimensiones). Si k = 1, devolver la partición trivial {V} con Φ = 0 (el sistema ya está "unido").
