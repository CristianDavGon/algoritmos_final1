# SDD-4 — Decisions: Fase 4 (KGeoMIP)

Decisiones específicas de la Fase 4. No duplican lo que ya está en `context/project/decisions.md` (DEC-01 a DEC-14); registran únicamente lo que es específico de KGeoMIP o que DEC-14 no cubre con suficiente detalle de implementación.

---

## D4-01: Elección de E4 sobre las estrategias A, B y C — justificación detallada

**Decisión**: La heurística principal de KGeoMIP es **E4** (refinamiento divisivo top-down anclado en GeoMIP). Las estrategias A (clustering aglomerativo), B (espectral) y C (comunidades) quedan descartadas como respuesta final. La Estrategia A se conserva como **baseline de comparación A/B**.

**Justificación detallada** (ver §0 y §2.4 del diseño):

Las tres estrategias de clustering puro fallan al menos una de las dos reglas duras del diseño:

| Regla dura | Estrategia A | Estrategia B | Estrategia C |
|-----------|-------------|-------------|-------------|
| Regresión k=2 exacta (KGeoMIP(k=2) ≡ GeoMIP) | ✗ | ✗ | ✗ |
| Monotonicidad anidada por construcción (φ(k+1) ≥ φ(k)) | ✓ (anidada) | ✗ (no anidada) | ✗ (no anidada) |

- **Estrategia A** produce una familia anidada (el dendrograma es anidado), pero no garantiza regresión k=2: el corte del dendrograma de S en k=2 produce, en general, una bipartición **distinta** a la de GeoMIP (mecanismos distintos). Además, "delegar k=2 a GeoMIP pero usar A para k≥3" rompe la anidación.
- **Estrategia B** relaja directamente el min-cut normalizado (mejor alineación con el objetivo), pero no produce familias anidadas: las k y k+1 particiones espectrales no están en relación de refinamiento.
- **Estrategia C** no produce familias anidadas y sufre el problema de resolución de la modularidad.

**E4 corrige los tres defectos simultáneamente**:
1. Ancla k=2 en GeoMIP exacto (Fase 2 del pseudocódigo) → regresión por construcción.
2. Es divisivo → cada nivel refina el anterior → familia anidada → monotonicidad por construcción.
3. S propone cortes baratos, EMD confirma → selección alineada con el objetivo real.

**Por qué Estrategia A como baseline y no B o C**: A produce familia anidada (única entre las tres), lo que permite una comparación justa con E4 sobre la curva Φ(k). B y C no son comparables en términos de monotonicidad.

---

## D4-02: T y S calculadas una sola vez por sistema

**Decisión**: La tabla T se calcula una única vez por sistema (herencia de GeoMIP). La matriz S (n×n) se calcula una única vez al inicio de KGeoMIP y se reutiliza para todos los k-valores y todas las llamadas a MejorCorte.

**Por qué T es independiente de k** (§4.2 del diseño):
Los valores de T dependen solo de la TPM (vía los tensores X[·]) y de la estructura del hipercubo (vía N(i,j) y d_H). Ningún término depende de cómo se particione V. Por tanto T es invariante ante k, y S — derivada de T — también lo es.

**Consecuencia de implementación**: No recalcular T entre llamadas a `aplicar_estrategia(k)` con distintos k sobre el mismo sistema. No recalcular S dentro de la Fase 3 del pseudocódigo (la cola de prioridad reutiliza la misma S para todos los bloques). Esto es la regla dura "tabla de costos una sola vez" heredada de GeoMIP.

**Costo**: T ocupa O(n·2ⁿ) en memoria (la misma tabla que ya existe en GeoMIP). S ocupa O(n²) — despreciable para n≤25.

---

## D4-03: Criterio de desempate determinístico en E4

**Decisión**: Cuando dos o más partes tienen el mismo ΔΦ (hasta tolerancia ε = 1e-9), se aplica el siguiente desempate determinístico:

1. **Orden BFS de GeoMIP**: preferir el corte que GeoMIP elegiría — orden de candidatos BFS ascendente (Heurística 1 primero por índice de variable excluida, luego Heurística 2 por nivel BFS). Garantiza que en k=2 el desempate **reproduce exactamente** el de GeoMIP, preservando la regresión.
2. **Menor cardinalidad de la parte cortada**: si persiste el empate, preferir la parte de menor |Pi|.
3. **Índice léxico**: si aún empata, elegir la parte cuyo menor elemento de índice es menor (consistente con el desempate de Fase 3/KQNodes).

**Por qué este orden**:
- El criterio 1 preserva la regresión exacta k=2 incluso en casos de empate: si dos partes tienen el mismo ΔΦ en la primera iteración, GeoMIP elegiría el corte de menor índice de variable excluida, y E4 debe hacer lo mismo.
- El criterio 3 (índice léxico) garantiza determinismo total sin estado externo (no se necesita semilla aleatoria en E4).

**Implementación en MinHeap**: la clave de prioridad es la tupla `(ΔΦ, bfs_order, |Pi|, min_index(Pi))` donde la comparación lexicográfica de Python implementa el desempate automáticamente.

---

## D4-04: Caveat de implementación — verificación de la función EMD antes de validar regresión k=2

**Decisión**: Antes de ejecutar cualquier test de regresión k=2, el implementador debe verificar explícitamente qué función EMD usa GeoMIP en producción y asegurarse de que KGeoMIP llama a **la misma función**.

**Riesgo identificado** (§Apéndice, punto 5 del diseño):
El documento-guía del proyecto muestra `pyemd` con **matriz de costo de Hamming** para calcular la EMD. Sin embargo, el handoff de Fase 3 menciona `scipy.stats.wasserstein_distance` (Wasserstein 1-D sobre índices). Estas dos funciones **no son equivalentes**:
- `pyemd` con costo de Hamming: distancia de transporte entre distribuciones sobre {0,1}ⁿ con costo d_H(i,j) entre estados.
- `wasserstein_distance` de scipy: distancia de Wasserstein 1-D entre dos distribuciones sobre enteros (sin estructura de Hamming).

Si KGeoMIP usa una función distinta a la que GeoMIP usa en producción, `KGeoMIP(k=2) ≠ GeoMIP` numéricamente aunque la lógica sea correcta.

**Acción requerida antes de implementar**:
1. Localizar la llamada a EMD en `code/GeoMIP/src/strategies/geometric.py` (o `base.py`).
2. Identificar la función exacta: nombre, módulo, parámetros.
3. Documentar el hallazgo en el handoff de cierre (context/handoffs/04.md).
4. Asegurarse de que `KGeoMIP._calcular_phi_total()` llama a la **misma** función.

**Consecuencia**: Este caveat es un pre-requisito de C1 (regresión k=2). Si no se resuelve, C1 puede fallar por razones que no tienen nada que ver con la lógica de E4.
