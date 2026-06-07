# SDD-3 — Testing: Preguntas de validación

**Fase**: 3 — Extensión KQNodes
**Propósito**: El agente de implementación debe responder estas preguntas correctamente antes de dar la fase por cerrada. Las respuestas incorrectas o parciales indican que la implementación tiene bugs o malentendidos conceptuales.

---

## Bloque 1 — Regresión k=2

**P1.1** ¿Por qué KQNodes(k=2) debe ser idéntico a QNodes para cualquier sistema?
> Respuesta esperada: Con k=2, el bucle ejecuta exactamente una iteración (j=1). Π^(1) = {V} tiene un único bloque, por lo que cualquier criterio de selección (C1, C4) elige V. El paso siguiente llama a QNodes(V, f|_V) con f|_V = f (sin remapeo, oracle completo). El paso final calcula EMD sobre la bipartición resultante. No hay ningún paso que difiera de QNodes. La tolerancia 1e-9 es apropiada aquí porque es el mismo cómputo determinista.

**P1.2** ¿Qué debería pasar si KQNodes(k=2) devuelve un φ distinto al de QNodes para el mismo sistema?
> Respuesta esperada: Es un bug en la implementación, no un comportamiento esperado. Las causas más probables: (a) el oracle restringido f|_V no es idéntico al oracle completo f (error en remapeo cuando Pi = V), (b) se está usando un caché corrupto de una llamada anterior, (c) error en la construcción del producto tensorial con k=2 en el paso final.

**P1.3** ¿Para qué tamaños de n se ejecuta el test de regresión k=2?
> Respuesta esperada: n ∈ {5, 8, 10}. Son los mismos tamaños usados en la Fase 2 para validar QNodes, lo que permite reutilizar los CSVs de referencia ya verificados.

---

## Bloque 2 — Monotonicidad

**P2.1** ¿Cuál es la dirección correcta de la monotonicidad de φ y por qué?
> Respuesta esperada: φ(k+1) ≥ φ(k). Más partes ⟹ la reconstrucción ⊗ está más factorizada ⟹ más lejos del sistema original ⟹ mayor pérdida EMD. Formalmente: si Π^(k+1) refina a Π^(k), el conjunto de distribuciones separables según Π^(k+1) es subconjunto del de Π^(k), y la distancia a un conjunto más pequeño es mayor o igual. Por la descomposición aditiva: Φ(Π^(k)) = Σ φ_local(cⱼ) con φ_local ≥ 0, así que añadir un corte solo puede incrementar Φ.

**P2.2** ¿Qué implica que el test de monotonicidad falle (φ(k+1) < φ(k)) en una corrida real?
> Respuesta esperada: Indica un bug en la implementación, nunca una propiedad matemática violada. El greedy cumple monotonicidad por construcción. Las causas típicas: (a) error en el cálculo del EMD final para k distinto (p.ej. producto tensorial incorrecto para k≥3), (b) error de remapeo de máscaras que hace que el oracle restringido calcule f sobre un subconjunto equivocado, (c) reutilización incorrecta del caché entre bloques.

**P2.3** ¿Por qué la monotonicidad se cumple siempre para el greedy pero no necesariamente para el óptimo global por nivel?
> Respuesta esperada: El greedy produce una secuencia anidada Π^(1) ⊂ Π^(2) ⊂ ... ⊂ Π^(k) (cada Π^(j+1) es refinamiento de Π^(j)). La monotonicidad es una propiedad del refinamiento, así que la secuencia greedy la hereda automáticamente. Los óptimos por nivel φ*(k) = min_{Π∈P_k(V)} Φ(Π) también cumplen φ*(k+1) ≥ φ*(k) (por el argumento de fusión: cualquier (k+1)-partición óptima puede fusionarse a una k-partición de menor o igual φ), pero eso es independiente de la secuencia que produce el greedy.

---

## Bloque 3 — Gap de optimalidad para k=3 y k=4

**P3.1** ¿Por qué no se exige |Δφ| < 1e-9 contra BruteForce para k=3 o k=4?
> Respuesta esperada: Porque la heurística greedy (C4 o cualquier otro criterio) no garantiza optimalidad exacta para k≥3. El greedy puede elegir un primer corte barato que fuerce cortes caros posteriores, cuando un primer corte algo más caro habilitaría dos baratos (miopía inherente al voraz). Exigir igualdad exacta reprobaría implementaciones correctas y ocultaría la información más valiosa: cuánto se aleja el greedy del óptimo.

**P3.2** ¿Qué se reporta en lugar del criterio |Δφ| < 1e-9 para k≥3?
> Respuesta esperada: El gap de optimalidad: gap = φ_greedy − φ* ≥ 0 (siempre no negativo porque φ* es el mínimo global). Y la tasa de acierto exacto: proporción de casos donde gap = 0 (el greedy coincide con el óptimo). Esto provee información cuantitativa sobre la calidad de la heurística y es requerido por la rúbrica como "análisis de precisión/eficiencia".

**P3.3** ¿Cómo se obtiene φ* para n ≤ 6 y k ∈ {3,4}?
> Respuesta esperada: BruteForce enumera todas las S(n,k) k-particiones de Stirling (algoritmo de Knuth) y evalúa Φ sobre cada una, reutilizando la tabla de costos precomputada. Para n=6, k=3: S(6,3)=90 candidatas; para n=5, k=4: S(5,4)=10. Los scripts de comparación de Fase 2 en `code/tests/` ya tienen la infraestructura base y se extienden con parámetro k variable.

**P3.4** ¿Puede el gap ser negativo? ¿Qué significaría si lo fuera?
> Respuesta esperada: No. Si gap < 0 significa que φ_greedy < φ*, lo cual contradice la definición de óptimo (φ* es el mínimo). Un gap negativo es evidencia de un bug: o bien BruteForce no está enumerando correctamente todas las particiones, o bien KQNodes está calculando Φ con una función distinta a la que usa BruteForce.

---

## Bloque 4 — Comparación C1 vs C4

**P4.1** ¿Por qué C4 (corte marginal mínimo) es preferible a C1 (tamaño máximo) para minimizar Φ?
> Respuesta esperada: C4 decide directamente según el objetivo. Por la descomposición aditiva Φ(Π^(k)) = Σ φ_local(cⱼ), el incremento de Φ en cada paso es exactamente φ_local del corte elegido. Minimizar φ_local en cada paso es descenso de máxima pendiente discreta sobre Φ. C1 ignora completamente los costos de corte y decide por cardinalidad; puede elegir un corte muy caro cuando el corte más barato está en una parte más pequeña. A igual complejidad O(k·D³), C4 domina en expectativa.

**P4.2** ¿En qué escenario concreto C1 es peor que C4?
> Respuesta esperada: Cuando hay un módulo débilmente acoplado (corte barato, costo ε) pero de tamaño pequeño, y un módulo fuertemente acoplado (corte caro, costo c ≫ ε) de mayor tamaño. C1 parte el grande (caro), C4 parte el pequeño (barato). Para k=2 el resultado final es el mismo (solo hay un corte), pero para k=3 C1 parte el grande y luego hace un corte adicional caro, mientras C4 parte el pequeño (costo ε) y luego aplica QNodes sobre el grande. El gap entre C1 y C4 puede ser arbitrariamente grande si c ≫ ε.

**P4.3** ¿Por qué C2 (pérdida interna máxima) es el peor criterio para minimizar Φ?
> Respuesta esperada: C2 tiene el signo opuesto al objetivo. Parte la parte con mayor φ_local (la más fuertemente integrada), que es precisamente el corte que más incrementa Φ. Es como si en el descenso por gradiente eligiéramos la dirección de máximo ascenso. Solo tendría sentido si el objetivo fuera maximizar la pérdida, no minimizarla. Además requiere más llamadas a QNodes (una por parte para rankear), siendo más caro que C4.

**P4.4** ¿Cuál es la complejidad de C4 vs C1 y qué implica para el diseño?
> Respuesta esperada: C1 hace k−1 llamadas a QNodes (una por iteración, solo sobre la parte elegida). C4 hace hasta 2k−1 llamadas (una inicial + hasta 2 hijos por iteración, aunque en la práctica puede ser menos si los hijos son singletons). En total ambos son O(k·D³). El factor ~2 de overhead de C4 es un costo justificado por el mejor alineamiento con el objetivo. Para la implementación: C4 requiere un MinHeap para gestionar los φ_local de partes candidatas; C1 solo necesita una lista de partes con sus tamaños.

---

## Bloque 5 — Arquitectura e implementación

**P5.1** ¿Por qué el caché del oracle debe reiniciarse entre llamadas a QNodes sobre distintos bloques?
> Respuesta esperada: Porque tras el remapeo de máscaras, la misma clave entera refiere a subconjuntos distintos en distintos bloques. Por ejemplo, la máscara `0b0101` en el bloque Pi = {g₀, g₂} significa {g₀, g₂} ∩ {g₀, g₂} = {g₀, g₂}, pero en el bloque Pj = {g₁, g₃} significa {g₁, g₃}. Si se comparte el caché global, un hit de caché devuelve el valor de f|_{Pi} cuando se necesita f|_{Pj}, resultado incorrecto sin ningún error visible.

**P5.2** ¿Cuándo se llama a la función EMD/emd_efecto durante la ejecución de KQNodes?
> Respuesta esperada: Solo una vez, al final del algoritmo, sobre la distribución reconstruida completa ⊗_{Pi∈Π} p_{Pi}. Durante la búsqueda (los k−1 pasos del bucle) nunca se llama a EMD directamente; solo se llama a QNodes/oracle que devuelve φ_local como proxy. Esto es eficiente: el costo O(2^D) de EMD se paga exactamente una vez, igual que en QNodes original.

**P5.3** ¿Qué pasa si al iterar con k particiones se agota la cola (MinHeap vacío) antes de llegar a k−1 refinamientos?
> Respuesta esperada: Ocurre cuando todas las partes restantes son singletons (|Pi| = 1) y no son partibles. Significa que V tiene menos de k elementos y no admite k partes no triviales. El comportamiento correcto es devolver la partición más fina alcanzable (todas las partes son singletons) y emitir un aviso en el log. No es un error de implementación sino un caso límite del input.
