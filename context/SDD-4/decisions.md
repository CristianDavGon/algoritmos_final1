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

---

## D4-05: `_mejor_corte` guiado por S — corrección de la inconsistencia S-ignorada

**Problema detectado (2026-06-09)**: `_mejor_corte` recibía `S` como parámetro y su docstring afirmaba "S se usa como ordenamiento previo", pero el cuerpo nunca utilizaba `S` — enumeraba exhaustivamente las `2^(|P|-1) - 1` biparticiones de cada bloque. Esto contradice DEC-14 (E4 = "S propone, EMD confirma").

**Decisión**: Convertir `_mejor_corte` en un *dispatcher* controlado por `estrategia_corte: str = "exhaustivo"` (parámetro de `aplicar_estrategia`):
- `"exhaustivo"` → `_mejor_corte_exhaustivo` (lógica original sin cambios, no usa S).
- `"guiado_S"` → `_mejor_corte_guiado_por_S`: genera candidatos con `_candidatos_por_afinidad(P, S, max_candidatos=20)`, que ordena las biparticiones por afinidad cruzada `score(A,B) = mean(S[i,j] para i∈A, j∈B)` ascendente y trunca a `_MAX_CANDIDATOS_GUIADOS=20`. EMD evalúa solo esos candidatos y decide (`argmin ΔΦ`).

**Por qué scoring directo y no clustering jerárquico**: la propuesta original pedía `scipy.cluster.hierarchy.linkage` por bloque. Para n ∈ {5,8,10} (rango de prueba, `constraints.md`), los bloques tras el anclaje GeoMIP rara vez superan 5 elementos (`2^(5-1)-1=15 ≤ 20`), por lo que el overhead de scipy por bloque superaría el costo de evaluar EMD sobre las ≤15 biparticiones exhaustivas. El scoring por afinidad cruzada es O(|P|²), sin dependencias nuevas, y **coincide exactamente con `_mejor_corte_exhaustivo` cuando `2^(|P|-1)-1 ≤ 20`** (todo n ≤ 5 y la mayoría de bloques para n ∈ {8,10}). Solo difiere para bloques ≥ 6 (posibles en n=10), donde S reduce genuinamente el espacio de búsqueda — el escenario que la propuesta original quería cubrir.

**Garantías verificadas** (`tests/suites/kgeomip/test_kgeomip_corte_guiado.py`, 15 tests):
- k=2 idéntico a GeoMIP independientemente de `estrategia_corte` (no toca `_mejor_corte`).
- `guiado_S` ≡ `exhaustivo` para n=5, k∈{3,4} (bloques ≤ 5).
- Monotonicidad φ(k+1) ≥ φ(k) preservada con `guiado_S`.
- Gap vs BruteForce ≥ 0 con `guiado_S` para k∈{3,4}, n=5.
- A/B `exhaustivo` vs `guiado_S` para n=8, k∈{3,4}.

**API**: `aplicar_estrategia(..., estrategia_corte="exhaustivo")` — default retrocompatible. `_mejor_corte_exhaustivo` se conserva intacta (no se elimina la versión exhaustiva, según lo solicitado).

---

## D4-06: Optimización de exactitud y velocidad de E4 — ΔΦ incremental exacto, raíz consistente con el modelo k y cachés (2026-06-09)

**Problemas detectados** (benchmark `code/scripts/bench_kgeomip.py`, baseline 2026-06-09):

1. **Heurística ΔΦ incorrecta**: `_emd_bloque` comparaba contra `dm_orig` sin restar el costo base del bloque, y para el lado B mantenía los dims `V∖A` en lugar de `B` — inconsistente con `_calcular_phi_total`, que marginaliza cada parte a sí misma. El heap de E4 ordenaba por una cantidad que **no es el incremento de Φ**, sesgando la selección entre bloques (criterio C4/min ΔΦ de DEC-12/DEC-14 mal implementado).
2. **Ancla proyectada inalcanzable**: la proyección del ancla GeoMIP al lado futuro descarta el emparejamiento presente/futuro de la bipartición real. Caso testigo N8A (estado `10000000`): GeoMIP da `{A..G}|{H}` con φ=0, pero las 6 únicas 3-particiones con φ*=0 agrupan `A` con `H` — **ninguna refina la proyección**, por lo que E4 quedaba estructuralmente bloqueado en gap=1.0.
3. **Recomputación**: GeoMIP (ancla k=2) se re-ejecutaba por cada valor de k en barridos k=1..5; las marginales de bloque se recalculaban ncubo por ncubo con indexación NCube por candidato.

**Decisiones**:

1. **ΔΦ incremental exacto**: como `emd_efecto = Σ_d |·|`, Φ(Π) se descompone aditivamente por parte: `Φ(Π) = Σ_P costo(P)` con `costo(P) = Σ_{d∈P} |dm_orig[d] − marg_d(P)|`. Se implementa `_delta_phi_corte(A,B) = costo(A) + costo(B) − costo(A∪B)`, que es exactamente `Φ(Π') − Φ(Π)`. El greedy del heap se convierte en descenso de máxima pendiente discreta sobre el objetivo real (alineado con DEC-12). Verificado por test: `ΔΦ == _calcular_phi_total(después) − _calcular_phi_total(antes)` (1e-6) y `_mejor_corte == argmin Φ([A,B])`.
2. **Raíz consistente con el modelo k**: para k ≥ 3, la proyección del ancla GeoMIP se contrasta con `_mejor_corte(V)` bajo el mismo ΔΦ; gana el menor, con empate a favor del ancla GeoMIP (preserva D4-03). La regresión k=2 no se toca (retorna la Solution de GeoMIP antes de llegar a E4). Resultado: N8A k∈{3,4} pasa de gap=1.0 a **gap=0 (exacto)**.
3. **Cachés**: (a) `_sol_k2` por clave `(condicion, alcance, mecanismo)` — GeoMIP corre una sola vez por subsistema en barridos k=1..5 (verificado por test con contador); (b) `_marg_cache: dict[int, ndarray]` — marginales de todos los ncubos por máscara de bits sobre `_flat_data_matrix` de GeoMIP (equivalencia con `NCube.marginalizar` verificada a 1e-9), reutilizadas entre candidatos, bloques y valores de k. `_calcular_phi_total` queda intacta como autoridad final (D4-04).
4. **GeoMIP `find_mip`**: deduplicación de candidatos (la clave de `memoria_particiones` se construye antes de calcular la distribución; si ya existe, se omite). Sin cambio de resultados (suites vs BruteForce y PyPhi pasan).

**Resultados** (mismo benchmark, después):

| Caso | gap antes | gap después |
|------|-----------|-------------|
| n=5 k=4 `10000` | 0.375 | 0.250 |
| n=5 k=4 `11111` | 0.125 | 0.125 |
| n=6 k=3 `100000` | 0.406 | **0 (exacto)** |
| n=6 k=4 `100000` | 0.250 | **0 (exacto)** |
| n=8 k=3 `10000000` | 1.000 | **0 (exacto)** |
| n=8 k=4 `10000000` | 1.000 | **0 (exacto)** |

Tiempos: barrido k=1..5 n=10 de 0.133s → 0.102s (exhaustivo); llamadas k=2 repetidas ~0 ms (caché); además en n=10 las pérdidas mejoraron (k=4: 4.3496 → 3.8711). Tests: 37/37 de KGeoMIP (12 + 15 + 10 nuevos en `test_kgeomip_optimizacion.py`), 2/2 regresión GeoMIP. LOC: 294/300. mypy: mismos 15 errores preexistentes.

**Nota sobre monotonicidad**: la cadena divisiva k≥3 sigue siendo anidada (monotonicidad por construcción entre k y k+1 para k≥3). El paso k=2→k=3 compara la φ de GeoMIP (semántica de bipartición presente/futuro) con la φ del modelo k; se mantiene φ(3) ≥ φ(2) mientras GeoMIP retorne la bipartición óptima global (validado al 100% en Fase 2), porque las 2-particiones del modelo k son un subconjunto del espacio de biparticiones de GeoMIP.
