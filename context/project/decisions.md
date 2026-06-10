# Decisions

Decisiones globales tomadas en el proyecto, con su justificación. Solo se registran decisiones no obvias o que resuelven un trade-off importante.

---

## DEC-01: Dos sub-proyectos separados en lugar de mono-repo unificado

**Decisión**: GeoMIP y QNodes viven en carpetas independientes (`code/GeoMIP/` y `code/QNodes/`) con sus propias dependencias internas, en lugar de compartir un único paquete.

**Por qué**: Las dos estrategias tienen arquitecturas ligeramente distintas (SIA de GeoMIP recibe `Manager`; SIA de QNodes recibe `tpm` directo). Mantenerlas separadas evitó conflictos de dependencias durante el desarrollo en paralelo.

**Trade-off**: Hay duplicación de código (System, NCube, Solution, Manager son casi idénticos en ambos). Para las extensiones KGeoMIP/KQNodes se recomienda evaluar una refactorización a mono-repo con paquete compartido.

---

## DEC-02: SIA de GeoMIP recibe Manager; SIA de QNodes recibe tpm directamente

**Decisión**: La interfaz de `SIA.__init__` difiere entre sub-proyectos.

**Por qué**: GeoMIP evolucionó con el `Manager` como abstracción de I/O para soportar profiling y logging integrados. QNodes optó por simplicidad: recibe la TPM ya cargada para facilitar instanciación en batch sin overhead de I/O.

**Impacto**: Al implementar KGeoMIP/KQNodes, respetar la interfaz de cada sub-proyecto. Si se unifica, DEC-01 aplica primero.

---

## DEC-03: Notación little-endian para indexación de NCubes

**Decisión**: Los datos de la TPM se indexan en notación little-endian por defecto (`Notation.LIL_ENDIAN`).

**Por qué**: Definido en `Application.notacion` como valor por defecto. Compatible con la representación del dataset de prueba.

**Configuración**: Se puede cambiar via `aplicacion.set_notacion(Notation.BIG_ENDIAN)` antes de crear el sistema.

---

## DEC-04: Oracle lazy con cache en QNodes (O(D³) masks únicos)

**Decisión**: El oracle de Queyranne no pre-computa todos los 2^D masks; solo evalúa los pedidos durante el MAO.

**Por qué**: Para D=8 hay 256 masks posibles pero el MAO solo pide O(D³) = O(512) evaluaciones, muchas de ellas repetidas. El cache evita recomputar, reduciendo de O(2^D·N) a O(D³·N) evaluaciones efectivas.

**Referencia**: Queyranne, Math. Prog. 1998. Validación empírica en Kitazono et al., Entropy 2018.

---

## DEC-05: Tabla de transiciones en GeoMIP como dict de listas

**Decisión**: `tabla_transiciones: dict[tuple[tuple, tuple], list[float]]` donde las claves son pares (estado_inicial, estado_final) y los valores son listas de costos por cada variable futura.

**Por qué**: Permite memoización natural: si la clave ya existe, no se recalcula. La estructura de lista facilita operaciones vectorizadas con numpy en `calcular_costo()`.

**Nota**: `_flat_data` pre-aplana los NCubes para acceso O(1) por índice de estado (usando representación entera little-endian).

---

## DEC-06: Timeout de 3600 segundos por prueba en ejecución batch de GeoMIP

**Decisión**: Cada prueba del batch se ejecuta en un proceso separado con timeout de 1 hora.

**Por qué**: Redes grandes (n=10) con ciertos alcances/mecanismos pueden requerir tiempo considerable. El multiprocessing aísla fallos sin afectar el resto del batch.

**Implementación**: `multiprocessing.Process` con `proceso.join(timeout=3600)`.

---

## DEC-07: Estado inicial por defecto "10000000" para n=8

**Decisión**: El estado inicial canónico para pruebas es el primer bit activo (`"10000000"`).

**Por qué**: Convención del dataset `DatosPruebas2026_1.xlsx` que define los sistemas en función a este estado inicial.

---

## DEC-08: Semilla numpy fija = 73

**Decisión**: `aplicacion.semilla_numpy = 73` para todas las redes generadas aleatoriamente.

**Por qué**: Garantiza reproducibilidad en la generación de redes de prueba con `Manager.generar_red()`.

---

## DEC-09: Resultados de GeoMIP en multiprocessing vs QNodes en proceso único

**Decisión**: GeoMIP usa `multiprocessing` para el batch; QNodes usa ejecución secuencial simple.

**Por qué**: GeoMIP fue optimizado para manejar timeouts en redes grandes. QNodes (O(D³)) es suficientemente rápido para no requerir multiprocessing en n≤10.

---

## DEC-10: KQNodes se implementa antes que KGeoMIP

**Decisión**: El orden de implementación de las extensiones k-particiones es **KQNodes primero, KGeoMIP después**.

**Por qué**:
1. **Complejidad algorítmica**: QNodes opera en O(D³) gracias al MAO de Queyranne. La extensión iterativa a k-particiones mantiene esta ventaja; KGeoMIP parte de una tabla de transiciones O(2^n × 2^n) con mayor riesgo de explosión combinatoria para k>2 (ver R-03).
2. **Extensibilidad matemática**: Queyranne/MAO se extiende naturalmente a k-particiones mediante aplicación iterativa (greedy k-way) sobre la función submodular simétrica. La base matemática está formalizada.
3. **Menos riesgo técnico**: La interfaz de QNodes (recibe `tpm` directamente) es más simple que la de GeoMIP (recibe `Manager`), lo que facilita la extensión sin overhead de I/O.
4. **Validación más clara**: KQNodes(k=2) == QNodes es un test de regresión directo y determinista.

**Trade-off**: KGeoMIP puede dar resultados más interpretables geométricamente, pero sus garantías de escalabilidad son menores para k>2.

---

## DEC-11: Función de pérdida φ para k-particiones — EMD entre distribución original y producto tensorial de k marginales

**Decisión**: φ(k) se calcula como la EMD entre la distribución marginal del sistema sin particionar y el producto tensorial de las k marginales individuales (una por cada grupo de la partición).

**Por qué**: Es la extensión natural de la fórmula existente para k=2. `System.distribucion_marginal()` ya devuelve el vector de probabilidades del sistema completo; `emd_efecto` en `GeoMIP/src/funcs/base.py` acepta dos distribuciones y devuelve un escalar. Para k partes basta pasar la distribución original vs. `np.kron` de las k marginales — sin cambios estructurales en las funciones existentes.

**Trade-off**: Suma de discrepancias o máximo habrían sido más baratos de calcular, pero no capturan la misma semántica de pérdida de información que la EMD, que ya es el criterio validado para k=2.

---

## DEC-12: Extensión de Queyranne a k>2 — iterativa con criterio de corte marginal mínimo (C4)

**Decisión**: KQNodes aplica el MAO de Queyranne de forma iterativa con el **Criterio C4 (corte marginal mínimo)**: en cada iteración se selecciona y bipartición la parte cuyo mejor corte tiene el menor φ_local (el que menos incrementa Φ), hasta obtener k grupos.

**Corrección respecto a versión anterior**: La decisión original especificaba "bipartir la parte con mayor pérdida interna" (Criterio C2). Esto estaba **mal alineado con el objetivo**: partir la parte más integrada introduce el corte que más sube Φ, lo opuesto a minimizarla. El Criterio C4 es el único alineado directamente con min Φ: por la descomposición aditiva Φ(Π^(k)) = Σ φ_local(c_j), minimizar cada incremento iterativamente es descenso de máxima pendiente discreta sobre el reticulado de particiones.

**Por qué**: El oracle en `QNodes/src/strategies/qnodes.py` opera sobre un conjunto de dimensiones activas (`NCube.dims`). Un sub-NCube condicionado es un NCube válido, por lo que el oracle y el MAO se reutilizan sin cambios estructurales. C4 requiere calcular φ_local de cada parte candidata, pero con caché (se almacenan los resultados de QNodes sobre los hijos recién creados) el costo total sigue siendo O(k·D³) — como máximo 2k−1 llamadas a QNodes.

**Implementación** (pseudocódigo C4 con MinHeap):
1. Inicializar Π = {V}; calcular (A*, B*, φ_local) = QNodes(V); insertar en MinHeap con clave φ_local.
2. Para j = 1 hasta k−1:
   a. Extraer parte P_sel con mínimo φ_local del heap.
   b. Aplicar la bipartición ya calculada: Π ← (Π ∖ {P_sel}) ∪ {A_sel, B_sel}.
   c. Para cada hijo con |hijo| ≥ 2: calcular QNodes(hijo) e insertar en heap.
3. Calcular Φ* = EMD(p(s_{t+1}), ⊗_{Pi∈Π} p_{Pi}) una sola vez al final.

**Variante C1** (tamaño máximo): conservar como A/B baseline para comparación experimental. Mismo esquema iterativo, sustituyendo el paso 2a por argmax |Pi|.

**Trade-off**: C4 hace hasta 2k−1 llamadas a QNodes vs k−1 de C1; el costo extra (factor ~2) vale por el alineamiento con el objetivo. La solución sigue siendo greedy (no globalmente óptima), pero su calidad es verificable contra BruteForce-k para n≤6 (ver DEC-13).

---

## DEC-13: Validación de optimalidad para k>2 — exhaustiva para n≤6, consistencia interna para n>6

**Decisión**: Para n≤6 se usa búsqueda exhaustiva sobre las S(n,k) particiones de Stirling como ground-truth propio. Para n>6 se aplican invariantes de consistencia interna.

**Por qué**: PyPhi no provee ground-truth para k>2. Para n=6, k=3: S(6,3)=90 candidatas — completamente viable. La evaluación de cada candidata reutiliza la tabla de costos precomputada sin modificaciones.

**Corrección respecto a versión anterior — dos puntos:**

1. **Dirección de monotonicidad corregida**: La versión anterior enunciaba φ(k+1) ≤ φ(k). La dirección correcta es **φ(k+1) ≥ φ(k)**. Bajo la definición del proyecto (δ = EMD entre el sistema y su reconstrucción ⊗, con δ=0 ⟺ separable), más partes ⟹ reconstrucción más factorizada ⟹ más lejos del original ⟹ mayor pérdida. Formalmente: si Π^(k+1) refina a Π^(k), entonces M_{Π'} ⊆ M_Π y Φ(Π') = EMD(p, M_{Π'}) ≥ EMD(p, M_Π) = Φ(Π). La secuencia greedy cumple esto por construcción (cada corte añade Δφ = φ_local ≥ 0). El assert en tests debe ser `φ(k+1) ≥ φ(k) − ε`, **no** `≤`. El criterio anterior aprobaría implementaciones incorrectas y reprobaría correctas.

2. **Criterio de optimalidad para k≥3 corregido**: El umbral |Δφ| < 1e-9 contra BruteForce es apropiado como tolerancia numérica y como criterio de regresión **solo en k=2** (donde KQNodes es exactamente QNodes, determinista). Para k≥3, la heurística greedy (C4 o cualquier otra) **no garantiza optimalidad exacta** y puede separarse del óptimo por más de 1e-9 de forma legítima. Lo correcto es: reportar el **gap de optimalidad** φ_greedy − φ* ≥ 0 y la **tasa de acierto exacto** (proporción de casos donde gap = 0). Esto alimenta directamente los resultados experimentales requeridos por la rúbrica.

**Invariantes de consistencia interna para n>6**:
1. **Monotonicidad** (corregida): φ(k+1) ≥ φ(k) para k ∈ {2,3,4} — gratuita por construcción, detecta bugs de EMD o remapeo.
2. **Regresión exacta**: KQNodes(k=2) == QNodes con tolerancia < 1e-9 (misma partición, mismo cómputo).
3. **Determinismo**: resultados reproducibles gracias al caché del oracle y `semilla_numpy=73` (ver DEC-08) + criterio de desempate de C4.

**Implementación de exhaustiva**: BruteForce existente en `code/tests/` enumera las S(n,k) particiones de Stirling (algoritmo de Knuth, TAOCP vol. 4) sobre las n dimensiones. Reutilizar scripts de Fase 2 con parámetro k variable.

---

## DEC-14: Heurística de KGeoMIP — E4 (refinamiento divisivo top-down anclado en GeoMIP)

**Decisión**: KGeoMIP usa la heurística **E4**: refinamiento divisivo (top-down) guiado por la matriz de similitud S derivada de T, con la EMD vía T confirmando cada corte (criterio de corte marginal mínimo, min ΔΦ), y el primer corte k=2 anclado en GeoMIP exacto.

**⚠️ Corrección respecto a versión anterior (2026-06-08)**: La versión anterior (Stirling para n≤6, hill-climbing basado en KQNodes para n>6) fue descartada porque no cumple las dos reglas duras del diseño:
1. **Regresión k=2**: el corte del hill-climbing en k=2 no coincide en general con GeoMIP (mecanismos distintos).
2. **Monotonicidad anidada**: hill-climbing no produce una familia anidada, por lo que φ(k+1) ≥ φ(k) no se garantiza por construcción.

**Por qué E4**: es la única estrategia que cumple ambas reglas duras por construcción:
- k=2 ancla en GeoMIP exacto (Fase 2 del pseudocódigo delega directamente en `GeoMIP_bipartir`).
- Refinamiento divisivo (cada nivel refina el anterior) ⟹ familia anidada ⟹ monotonicidad φ(k+1) ≥ φ(k) gratuita.
- Conserva S como dispositivo central (firma de KGeoMIP): S propone cortes baratos globalmente; EMD los confirma localmente.
- Mismo presupuesto O(n²·2ⁿ) que la versión anterior pero con garantías de regresión y monotonicidad.

**Flujo de E4**:
```
FASE 0: k=1 → {V}, Φ=0
FASE 1: construir S desde T (O(n²·2ⁿ), una sola vez)
FASE 2: k=2 → GeoMIP(V, T) exacto (regresión k=2 por construcción)
FASE 3: para j=3..k → MinHeap por ΔΦ; MejorCorte(P, T, S) propone con S, confirma con EMD
FASE 4: Φ* = EMD(p(s_{t+1}), ⊗_{Pi} p_{Pi}) una sola vez al final
```

**Estrategia A (clustering jerárquico aglomerativo sobre S)**: conservada como **línea base de comparación A/B** para los resultados experimentales. No es la respuesta final porque no garantiza regresión k=2 exacta ni monotonicidad anidada por construcción. Ver D4-01 en `context/SDD-4/decisions.md`.

**Corrección 2026-06-09 (D4-05)**: `_mejor_corte` ahora despacha entre `_mejor_corte_exhaustivo` (original) y `_mejor_corte_guiado_por_S` (S propone candidatos por afinidad cruzada, EMD confirma) según `estrategia_corte ∈ {"exhaustivo","guiado_S"}`. Cierra la brecha donde S se construía pero `_mejor_corte` la ignoraba. Ver D4-05 en `context/SDD-4/decisions.md`.

**Optimización 2026-06-09 (D4-06)**: tres correcciones de exactitud/velocidad: (1) el heap de E4 ordena por el **incremento exacto** de Φ (`ΔΦ = costo(A)+costo(B)−costo(P)`, válido por aditividad de `emd_efecto`), no por la EMD absoluta del bloque; (2) la raíz de E4 contrasta la proyección del ancla GeoMIP con el mejor corte directo bajo el modelo k (la proyección descarta el lado presente y puede dejar el óptimo fuera del alcance divisivo — caso N8A: gap 1.0 → 0); (3) cachés de marginales por máscara de bits y de la solución GeoMIP k=2 por clave (GeoMIP corre una vez por subsistema en barridos k=1..5). Regresión k=2 y monotonicidad intactas. Ver D4-06 en `context/SDD-4/decisions.md`.

**Marginalización**: columnas fuera de Pₘ se **SUMAN** (eventos mutuamente excluyentes); filas de variables descartadas se **PROMEDIAN** (equiprobabilidad). No se normaliza. ⊗ del proyecto expande solo columnas (no Kronecker).

**Dependencia**: DEC-11 define la función objetivo → DEC-12 (KQNodes) y DEC-14 (KGeoMIP) la minimizan por caminos distintos (MAO iterativo vs. divisivo geométrico con S). DEC-13 provee ground-truth BruteForce para medir la calidad de ambas heurísticas en sistemas pequeños.

---

## Dependencias entre DEC-11 a DEC-14

DEC-11 define la función objetivo → DEC-12 y DEC-14 la minimizan por caminos distintos (MAO iterativo vs. refinamiento geométrico divisivo E4). DEC-13 cierra el ciclo: la búsqueda exhaustiva (BruteForce-k) sirve como ground-truth para medir el gap de optimalidad de ambas heurísticas en sistemas pequeños (n≤6).
