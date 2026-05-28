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

## Decisiones pendientes (bloqueantes para k-particiones)

- **[BLOQUEANTE]** Función de pérdida φ para k-particiones: ¿suma de discrepancias, máximo, o EMD generalizada? → Consultar al usuario.
- **[BLOQUEANTE]** Extensión de Queyranne a k>2: ¿iterativa con re-fusión o formulación multi-vía? → Consultar al usuario.
- **[BLOQUEANTE]** Validación de optimalidad para k>2 (no hay ground-truth en PyPhi) → Estrategia: búsqueda exhaustiva para n≤6, consistencia interna para n>6.
- **[IMPORTANTE]** ¿Estrategia de generación de k-particiones candidatas desde N-Cubos para k>2? → Definir antes de implementar KGeoMIP.
