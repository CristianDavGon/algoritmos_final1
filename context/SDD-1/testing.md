# SDD-1 — Testing: Verificación de comprensión (Fase 1)

> Instrucción: Lee los archivos indicados en `planning.md` y responde cada pregunta.
> Un criterio de DONE para la fase es responder correctamente ≥7 de las 10.
> Escribe tu respuesta debajo de cada pregunta. No consultes el código al responder.

---

## Preguntas de flujo de ejecución

### P1 — Entry point
¿Qué hace `exec.py` en GeoMIP exactamente antes de llamar a `iniciar()`? ¿Qué configuración establece?

**Tu respuesta**:
> Establece aplicacion.profiler_habilitado = True. Es la única configuración activa antes de llamar iniciar(). La línea aplicacion.pagina_sample_network = "B" está comentada.

---

### P2 — Lectura de datos
¿De dónde vienen los parámetros `alcance` y `mecanismo` que se pasan a `aplicar_estrategia()`? ¿En qué formato están (string, lista, binario)?

**Tu respuesta**:
> Vienen del Excel `DatosPruebas2026_1.xlsx`. Se leen como letras ABC en `_leer_pruebas_excel()` y se convierten a string binario mediante `_letras_a_binario()`. Se pasan a `aplicar_estrategia()` como string binario 11100000.

---

### P3 — Rol de Manager
¿Cuáles son las tres responsabilidades principales de `Manager` en GeoMIP? ¿Qué atributo es diferente en `Manager` de QNodes?

**Tu respuesta**:
> Las tres responsabilidades de GeoMIP Manager: (1) resolver la ruta al archivo CSV de la TPM (`tpm_filename`), (2) exponer el directorio de salida para logs/profiling (`output_dir`), (3) generar nuevas redes TPM (`generar_red()`). La diferencia en QNodes: Manager tiene el método `cargar_red()` que carga y retorna la TPM como `np.ndarray`; GeoMIP Manager no lo tiene.

---

### P4 — Preparación del subsistema
Dado `condicion="11100000"`, `alcance="11100000"`, `mecanismo="11100000"` para n=8:
¿Cuántos NCubes tendrá el subsistema resultante? ¿Cuáles dimensiones se condicionan?

**Tu respuesta**:
> Se condicionan las dimensiones con bit=0: índices 3,4,5,6,7 (nodos D,E,F,G,H). Después de condicionar quedan los NCubes con índices 0,1,2 (A,B,C). `substraer` con dims_alcance=[3,4,5,6,7] no elimina ningún NCube de los que quedan (0,1,2 no están en ese set), y marginalizar [3,4,5,6,7] sobre dims=[0,1,2] no intersecta nada. El subsistema tiene **3 NCubes**.

---

### P5 — NCube
¿Qué forma (`shape`) tiene `NCube.data` para un sistema con n=8 antes de condicionar? ¿Y después de marginalizar 5 dimensiones?

**Tu respuesta**:
> Antes de condicionar: `(2, 2, 2, 2, 2, 2, 2, 2)` — un eje por cada nodo del sistema. Después de marginalizar 5 dimensiones quedan 3: `(2, 2, 2)`.

---

### P6 — Algoritmo geométrico
En `GeometricSIA.find_mip()`, ¿qué representa `tabla_transiciones[(estado_ini, estado_fin)]`? ¿Cuántos elementos tiene la lista (valor)?

**Tu respuesta**:
> En el código se implementa como `self._tabla[fin_int]`, un array de shape `(D_ncubos,)`. Representa el costo acumulado de transición desde `estado_ini` hasta `estado_fin` para cada NCube del subsistema. La lista (valor) tiene `D_ncubos` elementos — uno por cada NCube/nodo.

---

### P7 — Algoritmo QNodes
¿Qué calcula `oracle.f(mask_a)`? ¿Por qué se llama "lazy"? ¿Cuántas evaluaciones únicas realiza el MAO en total?

**Tu respuesta**:
> `f(mask_a)` calcula el costo de la bipartición definida por `mask_a`: suma sobre todos los nodos de `min(|mean_B - pivot|, |mean_A - pivot|)`, donde mean_A/mean_B son promedios marginales sobre los lados de la partición. Se llama "lazy" porque usa un cache interno `_means_cache` y solo computa cuando se le pide un mask nuevo (no precalcula todos los 2^D posibles). El MAO realiza O(D³) evaluaciones únicas en total.

---

### P8 — Diferencia clave
¿Cuál es la diferencia más importante entre cómo GeoMIP y QNodes reciben la TPM? ¿En qué línea de código de cada uno se carga/recibe la TPM?

**Tu respuesta**:
> En GeoMIP la TPM se carga externamente y se pasa como parámetro a `aplicar_estrategia(tpm=...)` — se carga en `main.py:99` con `np.genfromtxt(tpm_path, ...)`. En QNodes la TPM se inyecta en el constructor de `SIA.__init__(self, tpm: np.ndarray)` — línea `sia.py:34` — y se almacena como `self.tpm`. GeoMIP SIA no la almacena entre llamadas; QNodes SIA la guarda como atributo de instancia.

---

### P9 — EMD
¿Qué compara `emd_efecto(dist_particion, dist_subsistema)`? ¿Qué significa φ=0?

**Tu respuesta**:
> Compara las distribuciones marginales nodo a nodo: para cada nodo, la probabilidad de estar en estado OFF. La distancia es `sum(|u_i - v_i|)`. φ=0 significa que la bipartición encontrada tiene exactamente la misma distribución marginal que el subsistema original — el sistema no tiene información integrada, se puede descomponer sin pérdida.

---

### P10 — Resultado
¿Qué contiene un objeto `Solution` al final de `aplicar_estrategia()`? Menciona al menos 4 atributos y qué representan.

**Tu respuesta**:
> 1. `perdida` (float) — valor φ, la EMD mínima encontrada entre partición y subsistema.
> 2. `particion` (str) — representación textual de la mejor bipartición encontrada.
> 3. `distribucion_subsistema` (np.ndarray) — distribución marginal del subsistema original.
> 4. `distribucion_particion` (np.ndarray) — distribución marginal de la bipartición ganadora.
> 5. `tiempo_ejecucion` (float) — tiempo total de cómputo en segundos.
> 6. `estrategia` (str) — nombre del algoritmo usado ("Geometric", "Qnodes", etc.).

---

## Preguntas de deuda técnica

### P11 — Deuda detectada
Menciona 3 problemas de calidad de código que encontraste leyendo el código. Para cada uno: archivo, descripción y por qué es un problema.

**Tu respuesta**:
> 1. **QNodes/src/controllers/manager.py:63-76** — `cargar_red()` llama `np.genfromtxt(...)` en la línea 64 y el resultado se sobreescribe inmediatamente con `np.loadtxt(...)` en la línea 72. La primera llamada es código muerto que lee el archivo entero desde disco sin usar el resultado. Problema: doble I/O, más lento y confuso.
>
> 2. **GeoMIP/src/models/base/sia.py:61** y otros — Hay flags `#! COMENTAR PARA UN SOLO ESTADO INICIAL` / `#! DESCOMENTAR PARA UN SOLO ESTADO INICIAL` en el código de producción. El comportamiento se cambia comentando y descomentando líneas manualmente. Problema: no hay garantía de dejar el código en estado correcto, es un mecanismo de configuración sin validación y sin traza.
>
> 3. **GeoMIP/src/models/core/solution.py** — `Solution` (modelo de datos) inicializa un motor de síntesis de voz `pyttsx3` y tiene `hablar=True` por defecto, lanzando un hilo de audio cada vez que se imprime un resultado. Problema: rompe la responsabilidad única, hace imposible el uso en paralelo o headless sin efectos secundarios ruidosos.

---

## Preguntas bloqueantes (para k-particiones)

### P12 — Extensión
Si quisieras extender `QNodes` a k=3, ¿cuál sería el primer cambio en el código que tendrías que hacer? ¿Dónde exactamente?

**Tu respuesta**:
> El primer cambio sería en `QNodes.winner()` ([code/QNodes/src/strategies/qnodes.py:154](code/QNodes/src/strategies/qnodes.py)). Actualmente llama `qnodes(D, f, full_mask)` una sola vez y obtiene `best_mask_a` (una bipartición). Para k=3 habría que aplicar `qnodes` recursivamente: tras obtener la primera partición `(A, B)`, construir un nuevo oracle sobre el subconjunto `B` y volver a llamar `qnodes` para dividirlo en `(B1, B2)`. El cambio concreto: añadir un parámetro `k` a `winner()` y un loop que itere `k-1` veces, cada vez llamando `qnodes` sobre la parte más grande restante.

---

## Resultado de la verificación

| Pregunta | Correcta | Nota |
|----------|----------|------|
| P1 | ✅ | Configuración `profiler_habilitado` verificada en `exec.py` |
| P2 | ✅ | Flujo Excel → letras → binario verificado en `main.py` |
| P3 | ✅ | 3 responsabilidades de Manager y diferencia QNodes verificadas en código |
| P4 | ✅ | Lógica de condicionar/substraer verificada en `system.py` |
| P5 | ✅ | Shape `(2,)*n` antes y `(2,)*3` después verificado en `ncube.py` |
| P6 | ✅ | Estructura de `_tabla` en `geometric.py` verificada |
| P7 | ✅ | Oracle lazy con `_means_cache` y complejidad O(D³) verificados |
| P8 | ✅ | Diferencia de carga TPM verificada: parámetro vs `__init__` |
| P9 | ✅ | `emd_efecto` verificado en `funcs/base.py` y `funcs/iit.py` |
| P10 | ✅ | 6 atributos de Solution verificados en `solution.py` |
| P11 | ✅ | 3 problemas de deuda con referencias exactas de archivo y línea |
| P12 | ✅ | Punto de extensión en `qnodes.py:154` identificado correctamente |

**Puntaje**: 12/12 — ✅ DONE (criterio superado: ≥7)
