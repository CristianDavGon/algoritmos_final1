# SDD-4 — Testing: Preguntas de validación

**Fase**: 4 — Extensión KGeoMIP (E4)
**Propósito**: El agente de implementación debe responder estas preguntas correctamente antes de dar la fase por cerrada. Las respuestas incorrectas o parciales indican que la implementación tiene bugs o malentendidos conceptuales.

---

## Bloque 1 — Regresión k=2

**P1.1** ¿Por qué KGeoMIP(k=2) debe ser idéntico a GeoMIP para cualquier sistema?
> Respuesta esperada: Con k=2, E4 ejecuta exclusivamente la Fase 2: llama directamente a `GeoMIP_bipartir(V, T)` y retorna el resultado sin ejecutar ninguna fase posterior. Usa la misma T, los mismos candidatos BFS (Heurística 1 + 2), y la misma función EMD. No hay ningún paso adicional que pueda introducir divergencia. La tolerancia 1e-9 es apropiada porque es el mismo cómputo determinista.

**P1.2** ¿Qué diferencia fundamental hay entre el corte del dendrograma de S en k=2 y la bipartición de GeoMIP?
> Respuesta esperada: GeoMIP genera candidatos con dos heurísticas BFS (excluir una variable; mejor estado por nivel) y selecciona por EMD mínima. El corte del dendrograma de S en k=2 agrupa por similitud causal derivada de T (proxy) y corta el árbol; produce, en general, una bipartición distinta porque el mecanismo es diferente. Solo en el caso de complementariedad exacta (estructura modular nítida, S inter-bloque ≈ 0) coinciden. E4 evita esta ambigüedad anclando k=2 en GeoMIP por construcción.

**P1.3** ¿Para qué valores de n se ejecuta el test de regresión k=2 y cuál es la tolerancia?
> Respuesta esperada: n ∈ {5, 8, 10}, tolerancia 1e-9. Son los mismos tamaños usados en Fase 2 para validar GeoMIP, lo que permite reutilizar los resultados de referencia ya verificados. La tolerancia 1e-9 es exacta porque k=2 no introduce aproximaciones adicionales.

**P1.4** ¿Qué debe verificar el implementador antes de correr los tests de regresión?
> Respuesta esperada: Verificar que KGeoMIP llama a la **misma función EMD** que GeoMIP usa en producción (ver D4-04). Si GeoMIP usa `emd_efecto` con `pyemd` (matriz de costo de Hamming) y KGeoMIP usa `scipy.stats.wasserstein_distance` (Wasserstein 1-D), el test fallará numéricamente aunque la lógica sea correcta. Este caveat debe resolverse antes de validar.

---

## Bloque 2 — Monotonicidad

**P2.1** ¿Cuál es la dirección correcta de la monotonicidad de Φ y por qué?
> Respuesta esperada: **Φ(k+1) ≥ Φ(k)**. Casos extremos que fijan el sentido: k=1 da Φ=0 (sin corte, la "reconstrucción" es el sistema mismo); k=n da Φ máximo (cada variable su propia parte, máxima factorización). Más partes ⟹ reconstrucción más factorizada ⟹ más lejos del original ⟹ mayor EMD. Demostración por fusión: cualquier (k+1)-partición óptima puede fusionar dos partes obteniendo una k-partición de menor o igual Φ; por optimalidad en nivel k, la k-partición óptima tiene Φ ≤ al de esa fusión ≤ al de la (k+1)-partición.

**P2.2** ¿Por qué la monotonicidad es gratuita por construcción en E4?
> Respuesta esperada: E4 es divisivo: cada nivel k+1 es un refinamiento del nivel k (se parte una parte en dos, las demás intactas). Un refinamiento añade exactamente un corte de costo ΔΦ ≥ 0, que es no negativo porque se elige por EMD (la EMD es una distancia, siempre ≥ 0). Por lo tanto Φ(k+1) = Φ(k) + ΔΦ ≥ Φ(k). La monotonicidad es una consecuencia directa de la anidación y de que ΔΦ ≥ 0.

**P2.3** ¿Qué indica un fallo del test de monotonicidad (Φ(k+1) < Φ(k)) en una corrida real?
> Respuesta esperada: Es un bug en la implementación, no en las matemáticas. E4 cumple monotonicidad por construcción. Las causas más probables: (a) marginalización incorrecta (no sumar columnas / no promediar filas) que produce distribuciones que no son marginales válidas; (b) ⊗ del proyecto implementado incorrectamente (usando Kronecker estándar en lugar del ⊗ del proyecto); (c) función EMD distinta entre las fases (C11); (d) error en el refinamiento que no produce una familia anidada.

---

## Bloque 3 — Gap de optimalidad para k=3 y k=4

**P3.1** ¿Por qué no se exige |ΔΦ| < 1e-9 contra BruteForce para k=3 o k=4?
> Respuesta esperada: Porque E4 es greedy divisivo y no garantiza optimalidad global para k≥3. La trampa del greedy es que "la mejor k-partición puede no surgir de subdividir la mejor bipartición": un primer corte barato puede forzar cortes posteriores caros, cuando un primer corte más caro habilitaría dos baratos. Esta miopía es inherente a cualquier refinamiento secuencial. Exigir igualdad exacta reprobaría implementaciones correctas y ocultaría la información valiosa: cuánto se aleja E4 del óptimo.

**P3.2** ¿Qué se reporta en lugar del criterio de igualdad exacta para k≥3?
> Respuesta esperada: El gap de optimalidad: `gap = φ_E4 − φ* ≥ 0` (siempre no negativo porque φ* es el mínimo). Y la tasa de acierto exacto: proporción de casos donde gap = 0. Opcionalmente, el índice Jaccard entre la partición de E4 y la óptima (mide similitud estructural). Estos datos alimentan la sección experimental de la rúbrica como "análisis de precisión".

**P3.3** ¿Cómo se obtiene φ* para n ≤ 6 y k ∈ {3,4}?
> Respuesta esperada: BruteForce enumera todas las S(n,k) k-particiones (números de Stirling de segundo tipo) mediante el algoritmo de Knuth y evalúa Φ sobre cada una reutilizando la tabla T precomputada. Para n=6, k=3: S(6,3)=90 candidatas. Para n=5, k=4: S(5,4)=10. La infraestructura de comparación vs BruteForce de Fase 2 en `code/tests/` se extiende con parámetro k variable.

**P3.4** ¿Puede el gap de optimalidad ser negativo? ¿Qué indicaría?
> Respuesta esperada: No. Si gap < 0 significa φ_E4 < φ*, lo que contradice la definición de φ* como mínimo global. Un gap negativo es evidencia de bug: o BruteForce no enumera correctamente todas las S(n,k) particiones, o KGeoMIP y BruteForce usan funciones EMD distintas que no son comparables.

---

## Bloque 4 — Comparación E4 vs Estrategia A

**P4.1** ¿Por qué E4 es preferible a la Estrategia A (clustering aglomerativo) como respuesta principal?
> Respuesta esperada: Tres razones estructurales: (1) Regresión k=2: la Estrategia A no garantiza que su corte en k=2 coincida con GeoMIP. E4 lo garantiza por construcción (ancla k=2 en GeoMIP). (2) Monotonicidad: la Estrategia A produce familia anidada pero si se intenta combinar "k=2 = GeoMIP, k≥3 = dendrograma", se rompe la anidación. E4 mantiene anidación completa. (3) Selección por objetivo: la Estrategia A se compromete con la salida del proxy S sin comparar candidatos con la EMD real; E4 usa S para proponer y EMD para decidir.

**P4.2** ¿En qué casos la Estrategia A es igual de buena que E4?
> Respuesta esperada: Con complementariedad exacta (módulos causales nítidos: S inter-bloque ≈ 0, brecha espectral grande). En ese caso el proxy S identifica perfectamente los k grupos, el dendrograma corta en las fronteras correctas, y φ* ≈ 0. En este régimen E4 y Estrategia A producen el mismo resultado. La conjetura verificable del diseño: E[φ_E4] ≤ E[φ_A] con módulos solapados; empate con módulos nítidos.

**P4.3** ¿Qué se mide en la comparación A/B y cómo se interpreta?
> Respuesta esperada: Sobre el mismo conjunto de sistemas (n ≤ 6, k ∈ {3,4}): gap medio de E4 vs gap medio de Estrategia A (respecto al BruteForce φ*), y tasa de acierto exacto de ambas. Si gap_E4 < gap_A en promedio, E4 es mejor; si son iguales, confirma que la estructura de los sistemas de test es nítida. La comparación es requerida por la rúbrica como "evidencia de análisis de trade-offs".

---

## Bloque 5 — Función EMD y consistencia

**P5.1** ¿Cuántas veces se llama a la función EMD durante una ejecución completa de KGeoMIP?
> Respuesta esperada: Exactamente **una vez**, al final del algoritmo (Fase 4 del pseudocódigo), sobre la distribución reconstruida completa ⊗_{Pₘ} p_{Pₘ}. Durante las Fases 1-3 (construcción de S y refinamiento), nunca se llama a EMD directamente; MejorCorte usa `EMD_bloque` sobre bloques menores, que son llamadas a la maquinaria de GeoMIP sobre subconjuntos, no a la EMD final del sistema completo.

**P5.2** ¿Qué diferencia hay entre `EMD_bloque(A, B, T)` dentro de MejorCorte y `EMD(p_original, p_recon)` en la Fase 4?
> Respuesta esperada: `EMD_bloque(A, B, T)` calcula el ΔΦ de un corte específico sobre un bloque P (la pérdida de bipartir P en A y B, con las marginales del bloque). `EMD(p_original, p_recon)` calcula la pérdida total del sistema completo con k partes. La primera se usa como proxy de ranking durante la búsqueda; la segunda es el valor final de Φ que se retorna. Son llamadas conceptualmente distintas (bloque vs. sistema completo).

**P5.3** ¿Qué implica que la función EMD de KGeoMIP sea distinta a la de GeoMIP?
> Respuesta esperada: Que el test de regresión k=2 fallará numéricamente aunque la lógica de E4 sea correcta. Con funciones EMD distintas, KGeoMIP(k=2) y GeoMIP calcularán φ distintos para el mismo sistema, incluso si la partición es idéntica. Este es el caveat D4-04 que debe resolverse antes de implementar. La solución: localizar la función EMD exacta que usa GeoMIP en producción y asegurarse de que KGeoMIP llama a la misma.

---

## Bloque 6 — Identificación del k natural

**P6.1** ¿Por qué `argmin_k Φ(k)` no es un criterio válido para identificar el k natural del sistema?
> Respuesta esperada: Porque Φ(k) es monótona creciente en k (demostrado en §1.5 del diseño y verificado por la monotonicidad del test C2). El argmin sobre k ∈ {1,2,...} es siempre k=1 (Φ=0) o k=2 (el menor k con partición no trivial). Este criterio no tiene información sobre la estructura del sistema: siempre devuelve el menor k independientemente de si hay módulos naturales.

**P6.2** ¿Cuál es el criterio correcto para identificar el k natural y cómo se calcula?
> Respuesta esperada: El codo de la curva de incrementos: `ΔΦ(k) = Φ(k) − Φ(k−1)`. El k natural k* es el mayor k tal que ΔΦ(k) es "barato" y ΔΦ(k+1) es "caro". Formalmente: `k* = argmax_k [ΔΦ(k+1) − ΔΦ(k)]` (mayor incremento del costo marginal = punto donde la curva acumulada Φ(k) pasa de crecimiento suave a abrupto). E4 produce la familia completa {Φ(2), Φ(3), Φ(4), Φ(5)} en una sola corrida, por lo que ΔΦ queda disponible gratis.

**P6.3** ¿Cuándo un sistema tiene k* = 2 y qué indica sobre su estructura?
> Respuesta esperada: k* = 2 cuando ΔΦ(3) ≫ ΔΦ(2), es decir, el corte a 3 partes es drásticamente más caro que el corte a 2. Indica que el sistema tiene una única partición natural "barata" (la bipartición de GeoMIP) y subdividir más rompe módulos cohesivos. El sistema tiene estructura bimodular: dos bloques bien separados causalmente. En contraste, k* = 3 o 4 indica módulos más granulares.

**P6.4** ¿Cómo se reporta k* en los resultados experimentales?
> Respuesta esperada: Para cada sistema en el conjunto de prueba, reportar la curva ΔΦ(k) para k ∈ {2,3,4,5} y el k* calculado por el criterio del codo. Esto es análogo a la "curva del codo" (elbow curve) en k-means pero aplicada a la función de pérdida real Φ, no a una heurística de varianza. Los CSV de resultados deben incluir tanto Φ(k) como ΔΦ(k) para cada k.
