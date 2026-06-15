# Explicación Completa: KQNodes — k-particiones submodulares

> Basado en el código de la Fase 3 del proyecto (commit `6847cff`, autor: Daniel Felipe Franco Rincón),
> trazabilidad en `traceability_data/`, decisiones en `context/SDD-3/` y `context/handoffs/03.md`.

---

## Índice

1. [Contexto: ¿Qué problema resolvemos?](#1-contexto-qué-problema-resolvemos)
2. [De QNodes (k=2) a KQNodes (k≥3)](#2-de-qnodes-k2-a-kqnodes-k3)
3. [Recorrido por exec_kqnodes.py](#3-recorrido-por-exec_kqnodespy)
4. [Recorrido por main_kqnodes.py](#4-recorrido-por-main_kqnodespy)
5. [El corazón: kqnodes.py — Explicación línea a línea](#5-el-corazón-kqnodespy--explicación-línea-a-línea)
   - 5.1 [_oracle_restringido](#51-_oracle_restringido)
   - 5.2 [_qnodes_sobre_bloque](#52-_qnodes_sobre_bloque)
   - 5.3 [_calcular_phi_total](#53-_calcular_phi_total)
   - 5.4 [KQNodes.aplicar_estrategia](#54-kqnodesaplicar_estrategia)
   - 5.5 [_resolver y caso k=2](#55-_resolver-y-caso-k2)
   - 5.6 [_buscar_particion](#56-_buscar_particion)
   - 5.7 [_refinar_c4 — La heurística principal](#57-_refinar_c4--la-heurística-principal)
   - 5.8 [_refinar_c1 — La variante de comparación](#58-_refinar_c1--la-variante-de-comparación)
6. [¿Por qué la estrategia greedy y no búsqueda exhaustiva?](#6-por-qué-la-estrategia-greedy-y-no-búsqueda-exhaustiva)
7. [¿Por qué el criterio C4 (MinHeap por φ_local)?](#7-por-qué-el-criterio-c4-minheap-por-φ_local)
8. [¿Por qué caché por bloque y no global?](#8-por-qué-caché-por-bloque-y-no-global)
9. [¿Por qué EMD se calcula solo al final (D3-04)?](#9-por-qué-emd-se-calcula-solo-al-final-d3-04)
10. [¿Por qué el remapeo de máscaras?](#10-por-qué-el-remapeo-de-máscaras)
11. [Complejidad computacional completa](#11-complejidad-computacional-completa)
12. [Parámetros explicados](#12-parámetros-explicados)
13. [Garantías y límites del algoritmo](#13-garantías-y-límites-del-algoritmo)
14. [Flujo de ejecución de principio a fin](#14-flujo-de-ejecución-de-principio-a-fin)
15. [Ejemplo concreto paso a paso (n=5, k=3)](#15-ejemplo-concreto-paso-a-paso-n5-k3)

---

## 1. Contexto: ¿Qué problema resolvemos?

### La pregunta central de IIT 4.0

La Teoría de la Información Integrada (IIT 4.0) busca cuantificar cuánta "información causal irreducible" tiene un sistema. El número que lo expresa se llama **φ (phi)**. Para calcularlo hay que encontrar la **Partición de Mínima Información (MIP)**: la forma de cortar el sistema en partes que produzca la menor pérdida posible de información.

### ¿Qué es una k-partición?

Una **k-partición** del sistema es dividirlo en exactamente **k partes disjuntas** (grupos de nodos). Para k=2 es una bipartición (A vs B). Para k=3 son tres grupos (A vs B vs C), y así hasta k=5.

El valor φ para una k-partición es la diferencia entre la distribución del sistema original y la distribución del sistema cuando lo tratamos como si las k partes fueran independientes. Matemáticamente:

```
Φ* = EMD(p(s_{t+1} | s_t), ⊗_{i=1}^{k} p_i(s_{t+1}^{(i)} | s_t^{(i)}))
```

Donde `⊗` significa producto tensorial (las partes son independientes entre sí).

### El problema computacional

La búsqueda exhaustiva de la mejor k-partición requiere evaluar **el número de Stirling S(n,k)** de posibilidades:
- Para n=5, k=2: 15 biparticiones
- Para n=5, k=3: 25 triparticiones  
- Para n=8, k=3: 966 triparticiones
- Para n=10, k=3: 9.330 triparticiones
- Para n=20, k=3: ~580 millones de triparticiones

Esto hace que la búsqueda exhaustiva sea computacionalmente inviable para n grande.

---

## 2. De QNodes (k=2) a KQNodes (k≥3)

### QNodes original (Queyranne, k=2)

QNodes resuelve el problema de bipartición (k=2) usando el **algoritmo de Queyranne** (Math. Programming, 1998), que minimiza una función submodular simétrica en **O(D³)** evaluaciones del oracle, donde D = dimensiones del subsistema.

La clave es que la función que QNodes minimiza (`f(mask_a) = Σ_i min(|mean_B(i) - pivot_i|, |mean_A(i) - pivot_i|)`) es una aproximación submodular de la EMD-Effect, y Queyranne garantiza encontrar el mínimo de funciones submodulares simétricas en tiempo polinomial.

### ¿Cómo extender a k≥3?

El algoritmo de Queyranne solo funciona para biparticiones. Para k>2 se necesita una estrategia diferente. Las opciones son:

1. **Búsqueda exhaustiva**: inviable por S(n,k) exponencial.
2. **k-way Queyranne**: no existe una extensión directa al caso k>2 con garantías similares.
3. **Refinamiento iterativo greedy**: partir el problema en k-1 biparticiones sucesivas.

Tu compañero eligió la **opción 3**, que es la estándar en la literatura cuando se extiende Queyranne a k partes.

### La idea del refinamiento iterativo

Comienzas con el conjunto completo V de dimensiones como una sola parte. En cada paso, tomas una de las partes actuales y la bipartes usando Queyranne. Repites k-1 veces hasta tener k partes:

```
Inicio:  {A,B,C,D,E}                 ← 1 parte
Paso 1:  {A,B} | {C,D,E}             ← 2 partes (bipartición de todo V)
Paso 2:  {A,B} | {C,D} | {E}         ← 3 partes (bipartición de {C,D,E})
Paso 3:  {A,B} | {C} | {D} | {E}     ← 4 partes (bipartición de {C,D})
...
```

La pregunta es: **¿cuál parte bipartir en cada paso?** Ahí entra el criterio.

---

## 3. Recorrido por exec_kqnodes.py

**Archivo**: `code/QNodes/exec_kqnodes.py` (38 líneas)

```python
"""Punto de entrada para KQNodes (k-particiones submodular)."""

from src.models.base.application import aplicacion
from src.main_kqnodes import iniciar_kqnodes

# ── Configuración ─────────────────────────────────────────────────────────────
ESTADO:   str = "1" + "0" * 7    # Estado inicial binario: "10000000" → n=8 nodos
K:        int = 5                 # Número de partes de la k-partición
CRITERIO: str = "C4"              # "C4" = corte mínimo, "C1" = tamaño máximo
MUESTRA:  str = "A"              # Letra que identifica la red (N8A.csv → A)
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    aplicacion.desactivar_profiling()              # Sin overhead de pyinstrument
    aplicacion.set_pagina_red_muestra(MUESTRA)     # Selecciona N8A.csv
    iniciar_kqnodes(estado=ESTADO, k=K, criterio=CRITERIO)

if __name__ == "__main__":
    main()
```

### ¿Por qué este archivo existe separado de exec.py?

`exec.py` corre QNodes (k=2 solamente) sobre una red usando el flujo estándar de SIA. `exec_kqnodes.py` corre KQNodes (k∈{2,3,4,5}) sobre **todas las filas del Excel de pruebas**, generando CSVs con resultados por k y criterio. Son flujos de ejecución distintos:

- `exec.py`: una red, un caso (estado_inicial + condicion + alcance + mecanismo)
- `exec_kqnodes.py`: una red, TODOS los casos del Excel, para todos los k configurados

### ¿Por qué `ESTADO = "1" + "0" * 7`?

El estado inicial es un string binario de longitud n. `"1" + "0" * 7 = "10000000"` significa n=8 nodos, con el primer nodo en estado ON (1) y los demás en OFF (0). La longitud del string determina qué red se carga (N8A.csv). Este estado es el punto de evaluación del oracle — el "pivote" desde el que se miden las distancias de probabilidad.

### ¿Por qué `K = 5` y no otro valor?

El proyecto solicita resultados para k ∈ {2,3,4,5}. Este archivo de ejemplo está configurado para k=5. En producción se corre una vez por cada k, o se modifica `iniciar_kqnodes` para recibir una lista de k valores.

### ¿Por qué `CRITERIO = "C4"`?

C4 es el criterio principal de la Fase 3. Se explica en profundidad en la sección 7.

### ¿Por qué `aplicacion.desactivar_profiling()`?

El profiling con pyinstrument agrega overhead de medición. Para correr todos los casos del Excel de forma eficiente se desactiva. Solo se activa cuando se necesita depurar rendimiento.

---

## 4. Recorrido por main_kqnodes.py

**Archivo**: `code/QNodes/src/main_kqnodes.py` (145 líneas)

Este archivo orquesta la ejecución batch: lee el Excel, prepara la red, llama a KQNodes por cada combinación alcance×mecanismo×k×criterio, y guarda los resultados en CSV y Markdown.

### Función `iniciar_kqnodes`

```python
def iniciar_kqnodes(estado: str, k: int, criterio: str) -> None:
    project_root = Path(__file__).resolve().parents[2]
    ruta_excel = project_root / "data" / "DatosPruebas2026_1.xlsx"
    n = len(estado)                   # n = longitud del estado = número de nodos
    ruta_salida = RESULTS_DIR / f"resultado__N{n}_{muestra}_{k}.csv"
    ejecutar_desde_excel(ruta_excel, ruta_salida, estado, [k], [criterio])
```

**¿Por qué `parents[2]`?** El archivo está en `code/QNodes/src/`, dos niveles arriba de `code/QNodes/` y tres niveles arriba de la raíz del proyecto. `parents[2]` sube desde `src/` → `QNodes/` → `code/` → raíz. Esto hace que el path sea independiente del directorio desde donde se ejecute.

### Función `ejecutar_desde_excel`

```python
def ejecutar_desde_excel(ruta_excel, ruta_salida, estado_inicio, k_valores, criterios):
    n = len(estado_inicio)
    condicion = "1" * n              # Todos los nodos son candidatos (sin condiciones de fondo)
    pruebas = _leer_pruebas_excel(ruta_excel, n)

    gestor = Manager(estado_inicio)
    tpm = gestor.cargar_red()        # Lee N{n}{muestra}.csv → matrix (2^n, n)
    kqn = KQNodes(tpm)               # Una instancia reutilizable para todas las pruebas

    for i, (letras_alcance, letras_mecanismo) in enumerate(pruebas):
        alcance = _letras_a_binario(letras_alcance, n, posiciones_n)
        mecanismo = _letras_a_binario(letras_mecanismo, n, posiciones_n)

        for k in k_valores:
            for criterio in criterios:
                sol = kqn.aplicar_estrategia(estado_inicio, condicion, alcance, mecanismo,
                                             k=k, criterio=criterio)
                resultados.append({...})   # Acumula resultados

    # Escribe CSV y Markdown al final
```

**¿Por qué una sola instancia `kqn = KQNodes(tpm)` para todas las pruebas?**  
Porque cargar la TPM (que puede ser 40MB para n=20) es costoso. La instancia solo carga los datos una vez y reutiliza la estructura. Cada llamada a `aplicar_estrategia` prepara el subsistema internamente desde cero, sin contaminar el estado de la anterior.

### Función `_letras_a_binario`

```python
def _letras_a_binario(texto: str, n_bits: int, posiciones: str) -> str:
    bits = ["0"] * n_bits
    for letra in str(texto).upper():
        if letra in posiciones:
            bits[posiciones.index(letra)] = "1"
    return "".join(bits)
```

**¿Por qué esta conversión?** El Excel usa letras (ej. "ABCE") para indicar alcance y mecanismo. Pero el motor SIA trabaja con strings binarios (ej. "11010000"). Esta función mapea letras a posiciones binarias. A→posición 0, B→posición 1, C→posición 2, etc.

**Ejemplo**: Para n=5, `"BCD"` → `"01110"` (bit 1, 2, 3 en ON).

### Función `_leer_pruebas_excel`

```python
_N_A_SHEET: dict[int, int] = {5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}

df = pd.read_excel(ruta_excel, sheet_name=sheet_idx, header=None, skiprows=5, usecols="B:C")
```

**¿Por qué `skiprows=5`?** El Excel `DatosPruebas2026_1.xlsx` tiene 5 filas de encabezado antes de los datos de prueba. Las columnas B y C contienen el alcance y mecanismo respectivamente.

**¿Por qué el diccionario `_N_A_SHEET`?** El Excel tiene una hoja por tamaño de red. Para n=8 es la hoja índice 2 (segunda hoja, base 0), etc.

---

## 5. El corazón: kqnodes.py — Explicación línea a línea

**Archivo**: `code/QNodes/src/strategies/kqnodes.py` (391 líneas)

El módulo importa `oracle` y `qnodes` directamente de `qnodes.py`. No los reimplementa — los reutiliza.

```python
from src.strategies.qnodes import oracle, qnodes
```

**¿Por qué importar de qnodes.py y no duplicar?** La decisión de diseño DB-03.1 exige que `KQNodes(k=2)` produzca exactamente el mismo resultado que `QNodes`. Si se duplicara el código, cualquier corrección futura en `qnodes.py` podría no propagarse a `kqnodes.py`, rompiendo la garantía de regresión.

---

### 5.1 `_oracle_restringido`

```python
def _oracle_restringido(
    bloque: frozenset[int],     # Índices globales {0..D-1} de las dims en esta parte Pi
    N: int,                     # Número de nodos del sistema
    D_global: int,              # Dimensiones totales del subsistema completo
    data_nd: np.ndarray,        # TPM como n-array (N, 2, 2, ..., 2) — forma (N, 2^D_global)
    pivot_idx: tuple[int, ...], # Estado pivote por dimensión (en orden LIL_ENDIAN)
    pivot_vals: np.ndarray,     # p(nodo_i | estado_pivote) para cada nodo i
) -> tuple[Callable[[int], float], int]:
```

#### ¿Qué es un oracle y por qué existe?

El oracle es una función `f(mask_a) → float` que dado un subconjunto de dimensiones (representado como una máscara de bits), evalúa el "costo" de partir ahí. Es el puente entre la estructura matemática del algoritmo de Queyranne y la física del sistema.

**El oracle original** (en `qnodes.py`) opera sobre **todas las D dimensiones** del subsistema.

**El oracle restringido** (aquí) opera solo sobre las dimensiones del **bloque Pi** actual. Si Pi = {2, 4, 7} (3 dimensiones), el oracle restringido trabaja con máscaras de 3 bits en lugar de D bits.

#### ¿Por qué necesitamos un oracle restringido para k≥3?

Cuando bipartimos una parte Pi (que es un subconjunto de {0..D-1}), necesitamos que el oracle evalúe solo las dimensiones dentro de Pi. Si usáramos el oracle global, una máscara de bit "00000100" significa "solo la dimensión 2" en el contexto global — pero dentro de Pi = {2,4,7}, la "dimensión 2" es el bit local 0. Las máscaras de bits son locales a cada bloque.

#### El remapeo de índices (D3-02)

```python
indices_gl = sorted(bloque)    # Ej: [2, 4, 7]
m = len(indices_gl)            # m = 3 (dimensiones locales)
full_mask_local = (1 << m) - 1  # 0b111 = 7

# Para d=0 (dim global 0): si 0 not in bloque → fijar en pivot
# Para d=2 (dim global 2): si 2 in bloque → corresponde al bit local 0
# Para d=4 (dim global 4): si 4 in bloque → corresponde al bit local 1
# Para d=7 (dim global 7): si 7 in bloque → corresponde al bit local 2
```

La función `__means(mask_local)` construye los slices para `data_nd` así:
- Para cada dimensión global d de 0 a D_global-1:
  - Si d está en el bloque: usa `slice(None)` (libre) si el bit local correspondiente está en `mask_local`, o fija en el pivote si no
  - Si d NO está en el bloque: siempre fija en el pivote (no forma parte de Pi)

**¿Por qué `pivot_idx[D_global - 1 - d]`?** Porque `data_nd` usa notación **LIL_ENDIAN**: el eje 0 corresponde a la dimensión más significativa, el eje D-1 a la menos significativa. El bit 0 de `pivot_idx` es la dimensión 0, pero el eje 0 de numpy es la dimensión D-1 (reversed). Este `D_global - 1 - d` corrige esa inversión.

```python
piv_ax = pivot_idx[D_global - 1 - d]   # Eje correcto en notación LIL_ENDIAN
```

#### El caché bidireccional

```python
_means_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}

mean_a = data_nd[tuple(slc_a)].reshape(N, -1).mean(axis=1)
mean_b = data_nd[tuple(slc_b)].reshape(N, -1).mean(axis=1)
_means_cache[mask_local] = (mean_a, mean_b)
_means_cache[comp_local] = (mean_b, mean_a)   # Complemento gratis
```

**¿Por qué guardar el complemento gratis?** Si calculamos `means(mask=0b01)`, el complemento `mask=0b10` tiene exactamente los roles A y B intercambiados. El cómputo ya está hecho — solo invertimos el orden de la tupla. Esto reduce el número de evaluaciones reales a la mitad.

**¿Por qué caché LOCAL (por bloque)?** (Ver sección 8 para la explicación completa)

#### La función de costo f_local

```python
def f_local(mask_local: int) -> float:
    if mask_local == 0 or mask_local == full_mask_local:
        return 0.0                  # Triviales: todo en A o todo en B → costo 0
    mean_a, mean_b = __means(mask_local)
    return float(np.minimum(
        np.abs(mean_b - pivot_vals),    # costo_alcance: ¿cuánto se aleja B del pivote?
        np.abs(mean_a - pivot_vals)     # costo_no_alcance: ¿cuánto se aleja A del pivote?
    ).sum())
```

**¿Qué mide esta función?** Para cada nodo i, mide cuán diferente es la distribución marginal del nodo cuando se promedia sobre su grupo (A o B) respecto al valor pivote. Esencialmente es un proxy de cuánta información se pierde al hacer ese corte.

**¿Por qué `min(cost_alcance, cost_no_alcance)` por nodo?** Porque la partición no sabe a priori en cuál lado va cada nodo (alcance vs mecanismo). El mínimo elige el lado "más barato" para cada nodo i, que es lo que después se usa para asignar nodos al alcance o mecanismo en `winner`.

---

### 5.2 `_qnodes_sobre_bloque`

```python
def _qnodes_sobre_bloque(
    bloque: frozenset[int],
    N, D_global, data_nd, pivot_idx, pivot_vals
) -> tuple[frozenset[int], frozenset[int], float]:
    indices_gl = sorted(bloque)
    m = len(indices_gl)
    if m <= 1:
        return bloque, frozenset(), 0.0   # No hay bipartición no trivial de 1 elemento

    f_local, full_mask_local = _oracle_restringido(
        bloque, N, D_global, data_nd, pivot_idx, pivot_vals
    )
    phi_local, best_mask_local = qnodes(m, f_local, full_mask_local)  # Queyranne

    # Convertir máscara local a frozensets de índices globales
    A = frozenset(indices_gl[r] for r in range(m) if (best_mask_local >> r) & 1)
    B = bloque - A
    return A, B, phi_local
```

**¿Por qué `frozenset`?** Los `frozenset` son hashables e inmutables, lo que permite usarlos como claves en el MinHeap del criterio C4 y como elementos en el conjunto `particion`. Un `set` regular no se puede poner en un heap.

**¿Por qué llamar a `qnodes()` directamente?** Porque dentro de un bloque Pi el problema es exactamente igual al problema de bipartición original, solo que sobre m ≤ D dimensiones. Queyranne funciona igual de bien sobre subproblemas más pequeños.

**La conversión máscara local → índices globales:**

Si `bloque = frozenset({2, 4, 7})` y `best_mask_local = 0b101 = 5`:
- Bit 0 (valor 1) está en ON → `indices_gl[0] = 2` → 2 va a A
- Bit 1 (valor 2) está en OFF → `indices_gl[1] = 4` → 4 va a B
- Bit 2 (valor 4) está en ON → `indices_gl[2] = 7` → 7 va a A
- Resultado: `A = frozenset({2, 7})`, `B = frozenset({4})`

---

### 5.3 `_calcular_phi_total`

```python
def _calcular_phi_total(particion: list[frozenset[int]], sistema: System) -> float:
    dm_original = sistema.distribucion_marginal()
    ...
    dist_recons = np.empty(N, dtype=np.float32)

    for parte in particion:
        pi_global = {todas_dims[d] for d in parte if d < len(todas_dims)}
        non_pi_global = np.array([g for g in todas_dims if g not in pi_global])
        for d in parte:
            ncubo = sistema.ncubos[d]
            marg = ncubo.marginalizar(non_pi_global)   # Marginaliza dims fuera de Pi
            pivot = seleccionar_estado(...)
            dist_recons[d] = float(marg.data[tuple(pivot)])

    return emd_efecto(dm_original, dist_recons)
```

#### ¿Qué hace esta función exactamente?

Calcula la EMD-Effect entre:
- `dm_original`: distribución marginal del subsistema completo (sin partición)
- `dist_recons`: distribución marginal reconstruida asumiendo que las k partes son independientes

Para reconstruir la distribución particionada, por cada nodo d en la parte Pi:
1. Toma su NCube (hipercubo de probabilidades de transición del nodo d)
2. Marginaliza (promedia) sobre todas las dimensiones **fuera** de Pi
3. Selecciona el valor en el estado pivote

Esto simula "¿qué probabilidad tendría el nodo d de estar ON si solo las dimensiones de Pi pudieran influirlo?"

#### ¿Por qué el cálculo de Φ* es una sola EMD al final? (D3-04)

El oracle (`f_local`) es solo un **proxy de ranking**: sirve para decidir qué corte es más económico. No es la medida exacta de φ. La medida exacta requiere la EMD completa sobre el sistema real (con biparticiones reales del NCube). Si calculáramos la EMD real en cada llamada al oracle, el costo sería O(D³ × N × EMD), que es mucho más costoso. El proxy sirve para explorar el espacio de particiones de forma barata; la EMD real se evalúa solo para la mejor partición encontrada.

---

### 5.4 `KQNodes.aplicar_estrategia`

```python
def aplicar_estrategia(
    self,
    estado_inicial: str,    # Ej: "10000000" → estado del sistema
    condicion: str,         # Ej: "11111111" → todos los nodos son candidatos
    alcance: str,           # Ej: "10110000" → nodos A, C, D en el futuro
    mecanismo: str,         # Ej: "01101000" → nodos B, C, E en el presente
    k: int = 2,             # Número de partes
    criterio: str = "C4",   # Criterio de selección de parte a bipartir
) -> Solution:
    self.sia_preparar_subsistema(estado_inicial, condicion, alcance, mecanismo)
    self.sistema = self.sia_subsistema
    ...
    return self._resolver(k, criterio)
```

**¿Qué hace `sia_preparar_subsistema`?** Herencia de la clase abstracta `SIA`. Aplica:
1. `condicionar()`: elimina los nodos que no son candidatos (donde `condicion[i] = 0`)
2. `substraer()`: extrae el subsistema delimitado por alcance y mecanismo
3. Calcula `sia_dists_marginales`: distribución marginal del subsistema (referencia para la EMD)

**¿Por qué `self.sistema = self.sia_subsistema`?** Para tener un acceso directo al subsistema preparado sin ir a través de la interfaz SIA. Es un alias de conveniencia.

---

### 5.5 `_resolver` y caso k=2

```python
def _resolver(self, k: int, criterio: str) -> Solution:
    ...
    if k == 2:
        # Replicación exacta de QNodes para garantizar regresión DB-03.1
        alcance_w, mec_w = self._winner_k2(sistema)
        dm_part = sistema.bipartir(arr_alc, arr_mec).distribucion_marginal()
        phi = emd_efecto(dm_part, dm_original)
    else:
        particion = self._buscar_particion(k, criterio)
        phi = _calcular_phi_total(particion, sistema)
```

**¿Por qué el caso k=2 tiene código separado?** Por la **garantía de regresión DB-03.1**: `KQNodes(k=2)` debe producir exactamente el mismo φ que `QNodes`. Si ambos usaran exactamente el mismo código de `winner()`, estaría garantizado. Aquí `_winner_k2` es una copia exacta de `QNodes.winner()`. La razón de duplicar en vez de importar es que `KQNodes` hereda de `SIA` pero `QNodes` también hereda de `SIA`, y habría un problema de herencia múltiple o dependencia circular.

**¿Cómo se verifica la regresión?** El documento `context/handoffs/03.md` reporta: "13/13 casos verificados en `test_regresion_k2_igual_qnodes`" con tolerancia 1e-9.

---

### 5.6 `_buscar_particion`

```python
def _buscar_particion(self, k: int, criterio: str) -> list[frozenset[int]]:
    sistema = self.sistema
    N = len(sistema.ncubos)
    D = len(sistema.dims_ncubos)
    data_nd = np.stack([c.data for c in sistema.ncubos])   # (N, 2, ..., 2)
    pivot_idx = tuple(int(sistema.estado_inicial[dim]) for dim in sistema.dims_ncubos)
    pivot_vals = data_nd[(slice(None),) + pivot_idx[::-1]] # p(nodo | pivote), shape (N,)

    D_part = min(N, D)   # Limitar a min(N,D) para evitar dims sin NCube correspondiente
    V = frozenset(range(D_part))
    if k <= 1 or D_part <= 1:
        return [V]
    ...
```

**¿Qué es `data_nd = np.stack([c.data for c in sistema.ncubos])`?**

Cada NCube tiene `data` con forma `(2, 2, ..., 2)` con D dimensiones. Al hacer `np.stack`, creamos un array de forma `(N, 2, 2, ..., 2)` donde la primera dimensión indexa el nodo y las siguientes son las dimensiones del hipercubo.

**¿Por qué `pivot_idx[::-1]` al indexar `data_nd`?**

`data_nd` está en notación LIL_ENDIAN (el eje 0 de numpy = dimensión D-1 del sistema). Para indexar el pivote correctamente hay que invertir el orden de los bits del estado pivote. Sin este `::-1` se accedería al estado incorrecto del hipercubo — este fue exactamente el bug DT-10 que se corrigió en la Fase 2.

**¿Por qué `D_part = min(N, D)`?**

Puede ocurrir que haya más dimensiones (D) que nodos (N), o viceversa. Si D > N, hay dimensiones que no tienen NCube correspondiente — no se pueden partir. Si N > D, hay nodos "extra" que ya están en la partición trivial. Limitar a min(N,D) evita índices fuera de rango.

---

### 5.7 `_refinar_c4` — La heurística principal

```python
def _refinar_c4(self, V, k, N, D, data_nd, pivot_idx, pivot_vals):
    # Paso 0: bipartir todo V
    A0, B0, phi0 = _qnodes_sobre_bloque(V, N, D, data_nd, pivot_idx, pivot_vals)
    _id = 0
    heap: list = [(phi0, -len(V), _id, V, A0, B0)]  # MinHeap: (phi_local, -tamaño, id, ...)
    particion: list[frozenset[int]] = [V]

    for _ in range(k - 1):   # k-1 iteraciones para llegar de 1 parte a k partes
        if not heap:
            break
        phi_sel, _, _, P_sel, A_sel, B_sel = heapq.heappop(heap)  # Parte con menor phi
        particion.remove(P_sel)
        if A_sel: particion.append(A_sel)
        if B_sel: particion.append(B_sel)

        for hijo in (A_sel, B_sel):
            if len(hijo) >= 2:           # Solo bipartir si tiene ≥2 elementos
                _id += 1
                Ah, Bh, phi_h = _qnodes_sobre_bloque(hijo, ...)
                heapq.heappush(heap, (phi_h, -len(hijo), _id, hijo, Ah, Bh))

    return particion
```

#### Explicación del MinHeap

El heap almacena tuplas `(phi_local, -tamaño, id, parte, A, B)`:
- `phi_local`: el costo de la mejor bipartición de esa parte. Es el **primer criterio de desempate**.
- `-tamaño`: el negativo del tamaño de la parte. Es el **segundo criterio de desempate** (si dos partes tienen el mismo phi_local, se prefiere la más grande — por eso negativo para MinHeap).
- `id`: contador para **garantizar determinismo** cuando phi_local y tamaño son iguales.

**¿Por qué MinHeap y no ordenar la lista?** El MinHeap (`heapq`) mantiene el mínimo en O(log n) por inserción y extracción, vs O(n log n) por reordenamiento. Como en cada iteración se insertan a lo mucho 2 nuevas partes, el heap es siempre pequeño (máximo k-1 elementos en estado estacionario).

#### ¿Cuántas llamadas a qnodes hace C4?

- Inicialmente: 1 llamada (para V completo)
- Por cada una de las k-1 iteraciones: a lo sumo 2 llamadas (para los 2 hijos)
- Total: **≤ 2k-1 llamadas a qnodes**

Con k=5: ≤ 9 llamadas. Cada llamada es O(m³) donde m ≤ D. Total: **O(k·D³)**.

#### Traza completa para k=3, n=5:

```
Inicio: V = {0,1,2,3,4}, heap = [(phi_0, -5, 0, V, A0, B0)]

Iteración 1 (k-1=2 pasos para llegar a k=3):
  pop: (phi_0, ..., V, A0={0,1,2}, B0={3,4})
  particion = [A0, B0] = [{0,1,2}, {3,4}]
  push hijo A0: (phi_A0, -3, 1, {0,1,2}, ...)
  push hijo B0: (phi_B0, -2, 2, {3,4}, ...)

Iteración 2:
  pop el de menor phi (digamos B0 con phi_B0 < phi_A0):
  particion = [{0,1,2}, {3}, {4}]   ← 3 partes ✓
```

---

### 5.8 `_refinar_c1` — La variante de comparación

```python
def _refinar_c1(self, V, k, N, D, data_nd, pivot_idx, pivot_vals):
    particion: list[frozenset[int]] = [V]
    for _ in range(k - 1):
        P_sel = max(
            (p for p in particion if len(p) >= 2),
            key=lambda p: (len(p), -min(p)),   # Tamaño máximo, desempate por índice mínimo
            default=None,
        )
        if P_sel is None: break
        A_sel, B_sel, _ = _qnodes_sobre_bloque(P_sel, ...)
        particion.remove(P_sel)
        if A_sel: particion.append(A_sel)
        if B_sel: particion.append(B_sel)
    return particion
```

**Criterio C1**: siempre bipartir la **parte más grande** (ignorando completamente el φ_local). Es una heurística de "divide para equilibrar el tamaño".

**Número de llamadas a qnodes**: exactamente k-1 (una por iteración, sin precómputos). **Total: O((k-1)·D³)**.

**¿Cuándo C1 falla?** Cuando la parte más grande NO es la que produce el corte de menor costo φ. Esto ocurre con frecuencia porque el tamaño no está correlacionado con la información integrada.

Los experimentos de A/B testing (documentados en `context/handoffs/03.md`) muestran que **C4 tiene menor gap frente al óptimo que C1**, confirmando que minimizar φ_local es mejor heurística que maximizar el tamaño.

---

## 6. ¿Por qué la estrategia greedy y no búsqueda exhaustiva?

### El costo combinatorio es prohibitivo

Los números de Stirling S(n,k) crecen explosivamente:

| n | k=2 | k=3 | k=4 | k=5 |
|---|-----|-----|-----|-----|
| 5 | 15 | 25 | 10 | 1 |
| 8 | 127 | 966 | 2.646 | 3.025 |
| 10 | 511 | 9.330 | 145.750 | 1.082.250 |
| 20 | ~524K | ~580M | — | — |

Para n=10, k=4: **145.750** particiones posibles, cada una requiriendo una EMD completa. Inviable.

### La estrategia greedy de refinamiento iterativo garantiza:

1. **Correctitud exacta para k=2**: Queyranne es exacto para funciones submodulares simétricas
2. **Heurística de alta calidad para k≥3**: empíricamente, el gap con el óptimo es pequeño (documentado en `test_ab_c1_vs_c4_n5`)
3. **Monotonicidad**: φ(k+1) ≥ φ(k) siempre (ver sección 13)
4. **Complejidad polinomial**: O(k·D³) vs O(S(n,k)) de búsqueda exhaustiva

### ¿Por qué no hay garantía de optimalidad para k≥3?

La función `f_local` no es submodular en general para la k-partición (solo lo es para bipartición). Sin submodularidad, Queyranne da la bipartición óptima de cada parte Pi, pero el greedy global puede no ser el k-corte mínimo. En términos simples: la mejor manera de partir {0,1,2,3,4} en 3 partes puede NO ser partir primero en {0,1,2} y {3,4} y luego en {0,1}, {2} y {3,4}. Puede que la mejor tripartición sea {0,3}, {1,4}, {2} — que nunca se consideraría con el enfoque iterativo.

Aun así, los benchmarks del proyecto muestran que el gap es pequeño y aceptable para los propósitos del proyecto.

---

## 7. ¿Por qué el criterio C4 (MinHeap por φ_local)?

### La intuición

C4 (criterio 4) se basa en el principio: **corta donde duela menos**. En cada paso del refinamiento, de todas las partes disponibles, elige la que produce el corte más barato (menor φ_local). Esto minimiza el costo marginal de cada división.

### Conexión con la teoría de información integrada

En IIT, φ mide la irreducibilidad causal. Una parte con φ_local pequeño es más "fácilmente reducible" — se puede cortar sin perder mucha información. Al priorizar estas partes, C4 minimiza el impacto total de todas las divisiones.

### Comparación C4 vs C1

| Propiedad | C4 (MinHeap φ_local) | C1 (tamaño máximo) |
|-----------|---------------------|-------------------|
| Llamadas a qnodes | ≤ 2k-1 | k-1 |
| Criterio de selección | φ_local mínimo | Tamaño máximo |
| Overhead de precómputo | Sí (1 llamada extra para V) | No |
| Gap vs óptimo (n=5) | Menor | Mayor |
| Determinismo | Garantizado (por `_id`) | Garantizado (por `min(p)`) |

### El desempate en el heap (D3-03)

La tupla del heap es `(phi_local, -len(parte), _id)`:
1. Si dos partes tienen el mismo φ_local: se prefiere la más grande (`-len(parte)`, MinHeap elige el menos negativo = el más grande)
2. Si también tienen el mismo tamaño: se usa `_id` (orden de inserción) para garantizar determinismo absoluto

Sin este desempate, el resultado del algoritmo dependería del orden de los elementos en Python, que no es determinístico entre ejecuciones.

---

## 8. ¿Por qué caché por bloque y no global?

Esta es la decisión de diseño **D3-02** y es crítica para la correctitud.

### El problema con caché global

Supón que estamos evaluando dos bloques diferentes:
- Pi = {0, 1, 2} (bloque de 3 dimensiones)
- Pj = {3, 4} (bloque de 2 dimensiones)

Dentro de Pi, la máscara local `0b01` significa "solo la dimensión 0".
Dentro de Pj, la máscara local `0b01` significa "solo la dimensión 3".

Son máscaras numéricamente iguales pero semánticamente distintas. Un caché global haría:
```
caché[0b01] = means para Pi   # Primer acceso
caché[0b01] → means para Pi   # Segundo acceso (¡INCORRECTO! Pj necesita dims {3}, no {0})
```

El resultado sería que Queyranne usaría los means equivocados al evaluar Pj, produciendo una bipartición incorrecta.

### La solución: caché LOCAL por llamada a `_oracle_restringido`

Cada llamada a `_oracle_restringido` crea un diccionario `_means_cache` nuevo, que es local a ese oracle y se descarta cuando termina el procesamiento del bloque. Así, las máscaras locales de Pi no interfieren con las de Pj.

```python
def _oracle_restringido(...):
    _means_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}   # LOCAL
    def __means(mask_local: int):
        if mask_local in _means_cache:          # Solo busca en caché local
            return _means_cache[mask_local]
        ...
```

El overhead es que si un bloque se reutilizara (lo cual no ocurre en el flujo actual), habría que recomputar. Pero como cada bloque se bipartite solo una vez, el caché local tiene exactamente los mismos hits que un caché global correcto tendría.

---

## 9. ¿Por qué EMD se calcula solo al final (D3-04)?

### El oracle es un proxy barato

La función `f_local(mask)` no calcula la EMD real de la bipartición. Calcula:

```
f(mask_a) = Σ_i min(|mean_B(i) - pivot_i|, |mean_A(i) - pivot_i|)
```

Esta es una **aproximación de la EMD-Effect** que se puede calcular con operaciones de promedio y valor absoluto sobre numpy — muchísimo más rápido que la EMD completa.

### ¿Cuándo se calcula la EMD real?

Solo en `_calcular_phi_total`, que se llama **una sola vez** al final, para la k-partición ganadora. En esa función se usa `emd_efecto()` que implementa la EMD-Effect como:

```python
def emd_efecto(u, v) -> float:
    return np.sum(np.abs(u - v))   # Suma de diferencias absolutas de marginales
```

Esta es la EMD bajo el supuesto de independencia de variables (usado en IIT 4.0 para el efecto).

### El costo si se calculara EMD en cada llamada al oracle

Para n=20, D=20, k=3:
- Llamadas al oracle: ≤ 2k-1 × O(D²) = O(k·D²) = O(3·400) = 1200 llamadas
- Cada EMD real requeriría `sistema.bipartir()` + `distribucion_marginal()` = operaciones de reshape y promedio sobre arrays de tamaño 2^D

Con caché del oracle: milisegundos. Con EMD real en cada llamada: potencialmente minutos.

---

## 10. ¿Por qué el remapeo de máscaras?

El remapeo es la traducción entre **índices globales** (0 a D-1) y **índices locales** (0 a m-1 dentro del bloque).

### Ejemplo concreto

Sistema con D=5 dimensiones {0,1,2,3,4}. Bloque Pi = {1,3,4} → m=3.

Índices locales: `indices_gl = [1, 3, 4]`
- Local bit 0 ↔ Global dim 1
- Local bit 1 ↔ Global dim 3  
- Local bit 2 ↔ Global dim 4

Máscara local `0b101 = 5` (bits 0 y 2 en ON):
- Bit 0 ON → dim global 1 → libre en el slice
- Bit 1 OFF → dim global 3 → fijo en pivot
- Bit 2 ON → dim global 4 → libre en el slice

Para construir el slice de `data_nd` (que tiene 5+1 = 6 ejes: eje 0 para nodos, ejes 1-5 para dims en orden LIL_ENDIAN):

```
# LIL_ENDIAN: eje 1 = dim 4, eje 2 = dim 3, eje 3 = dim 2, eje 4 = dim 1, eje 5 = dim 0
# d=0: dim global 0, not in bloque → fijo en pivot_idx[4] (eje 5 de numpy)
# d=1: dim global 1, in bloque como local bit 0, ON → libre (eje 4)
# d=2: dim global 2, not in bloque → fijo en pivot_idx[2] (eje 3 de numpy)
# d=3: dim global 3, in bloque como local bit 1, OFF → fijo en pivot_idx[1] (eje 2 de numpy)
# d=4: dim global 4, in bloque como local bit 2, ON → libre (eje 1 de numpy)
slc_a = [slice(None), slice(None), pivot_idx[1], pivot_idx[2], slice(None), pivot_idx[4]]
```

Este remapeo es el corazón de `_oracle_restringido` y es lo que permite aplicar Queyranne correctamente sobre subconjuntos de dimensiones.

---

## 11. Complejidad computacional completa

### Por componente

| Componente | Complejidad | Descripción |
|------------|-------------|-------------|
| Cargar TPM | O(2^n · n) | Lectura de CSV |
| `sia_preparar_subsistema` | O(n · 2^n) | Condicionamiento y substracción |
| `_oracle_restringido` (por bloque de m dims) | O(m²) llamadas, cada una O(N·2^m/2) | Oracle lazy con caché |
| `qnodes(m, f, mask)` | O(m³) llamadas al oracle | MAO de Queyranne |
| `_qnodes_sobre_bloque` | O(m³ · N · 2^m / 2) | = oracle × MAO |
| `_refinar_c4` (k iteraciones) | O(k · D³ · N · 2^D / 2) | ≤ 2k-1 bloques |
| `_calcular_phi_total` | O(N · D) | Una sola EMD final |
| **Total KQNodes k≥3** | **O(k·D³·N)** | Asintótico dominante |
| **vs BruteForce k≥3** | **O(S(n,k)·N)** | Stirling crece exponencial |

### Comparación práctica para n=8, k=3

| Algoritmo | Complejidad | Evaluaciones aprox. | Tiempo estimado |
|-----------|-------------|---------------------|-----------------|
| Búsqueda exhaustiva | O(S(8,3)·N) | 966 × 8 = 7.728 EMDs | ~2s |
| KQNodes C4 | O(3·8³·8) | ≤ 9 bloques × 512 ops | ~0.01s |
| KQNodes C1 | O(2·8³·8) | ≤ 6 bloques × 512 ops | ~0.007s |

Para n=20, k=3:
| Algoritmo | Evaluaciones | Tiempo estimado |
|-----------|-------------|-----------------|
| Exhaustiva | ~580M | semanas |
| KQNodes C4 | ≤ 9 × 20³ × 20 = 720.000 ops | ~1s |

---

## 12. Parámetros explicados

### Parámetros de `exec_kqnodes.py`

| Parámetro | Tipo | Ejemplo | Significado |
|-----------|------|---------|-------------|
| `ESTADO` | `str` | `"10000000"` | Estado inicial del sistema. Longitud = n = número de nodos. Cada bit es el estado ON/OFF del nodo en t=0. Define cuál red cargar (N8A.csv para len=8) y el punto pivote del oracle. |
| `K` | `int` | `5` | Número de partes de la k-partición. Rango válido: 2 ≤ k ≤ min(D, n). Si k > D, KQNodes lo limita automáticamente. |
| `CRITERIO` | `str` | `"C4"` | Heurística de selección. `"C4"` = MinHeap por φ_local (recomendado). `"C1"` = tamaño máximo (experimental). |
| `MUESTRA` | `str` | `"A"` | Identificador de la muestra de red. Concatenado con N y n forma el nombre del CSV: `N8A.csv`. Permite tener múltiples TPMs para el mismo n. |

### Parámetros de `aplicar_estrategia`

| Parámetro | Tipo | Ejemplo | Significado |
|-----------|------|---------|-------------|
| `estado_inicial` | `str` | `"10000000"` | Estado binario del sistema en t=0. Cada posición es un nodo. |
| `condicion` | `str` | `"11111111"` | Condiciones de fondo. `"1"` en posición i = nodo i es candidato. `"0"` = nodo i se condiciona (sus dimensiones se fijan al estado inicial). |
| `alcance` | `str` | `"10110000"` | Alcance del subsistema (futuro, t+1). `"1"` en posición i = nodo i está en el alcance. |
| `mecanismo` | `str` | `"01101000"` | Mecanismo del subsistema (presente, t). `"1"` en posición i = dimensión i está en el mecanismo. |
| `k` | `int` | `3` | Número de partes de la k-partición. |
| `criterio` | `str` | `"C4"` | Criterio de selección de parte a bipartir. |

### Parámetros internos del oracle

| Parámetro | Tipo | Significado |
|-----------|------|-------------|
| `N` | `int` | Número de NCubos (nodos del subsistema tras substracción) |
| `D` | `int` | Número de dimensiones del subsistema (= len(dims_ncubos)) |
| `data_nd` | `ndarray (N,2,...,2)` | TPM reestructurada como tensor N-dimensional |
| `pivot_idx` | `tuple[int,...]` | Estado pivote para cada dimensión (el estado inicial proyectado sobre las dims activas) |
| `pivot_vals` | `ndarray (N,)` | p(nodo_i = ON | estado_pivote) para cada nodo i — la distribución de referencia |
| `full_mask` | `int` | Máscara de todos los bits activos = (1 << D) - 1 |

---

## 13. Garantías y límites del algoritmo

### Garantía 1: Regresión exacta k=2

`KQNodes(k=2)` produce exactamente el mismo φ que `QNodes` (verificado en test_regresion_k2_igual_qnodes con |Δφ| < 1e-9 para n ∈ {5,8,10}, 13 casos).

### Garantía 2: Monotonicidad

φ(k+1) ≥ φ(k) — agregar más partes nunca puede aumentar la información integrada. Esto se cumple **por construcción** en el refinamiento iterativo: cada paso nuevo toma una parte y la divide, lo que solo puede mantener o reducir la información causal de esa parte. La suma global no decrece.

### Garantía 3: Corte óptimo por bloque

Dentro de cada bloque Pi, Queyranne garantiza encontrar la bipartición óptima (bajo la función proxy f_local, que es simétrica). Esta es exacta si f_local es submodular — empíricamente ~97-100% exacta según Kitazono et al. (Entropy 2018).

### Límite 1: No optimalidad global para k≥3

KQNodes no garantiza encontrar la k-partición de mínimo φ global. El refinamiento greedy puede quedar atrapado en mínimos locales. Gap real a medir en Fase 6.

### Límite 2: Tamaño mínimo de bloque

Si todas las partes tienen un solo elemento, no hay bipartición posible. El algoritmo se detiene (o devuelve la partición actual si k pedido > D).

### Límite 3: Complejidad del oracle

El oracle evalúa arrays de forma `(N, 2^m)` donde m ≤ D. Para m=20 (D=20): 2^20 ≈ 1 millón de entradas × N nodos. Para n=20, D=20: arrays de 20M floats por evaluación. El caché reduce las evaluaciones a O(D²) distintas.

---

## 14. Flujo de ejecución de principio a fin

```
exec_kqnodes.py
  │
  └─ main()
      ├─ aplicacion.desactivar_profiling()
      ├─ aplicacion.set_pagina_red_muestra("A")
      └─ iniciar_kqnodes(estado="10000000", k=5, criterio="C4")
          │
          └─ ejecutar_desde_excel(ruta_excel, ruta_salida, estado, [5], ["C4"])
              ├─ _leer_pruebas_excel(...)              ← Lee todas las filas del Excel
              ├─ Manager(estado).cargar_red()          ← Carga N8A.csv → tpm (256×8)
              ├─ KQNodes(tpm)                          ← Una instancia reutilizable
              │
              └─ for cada (alcance, mecanismo) en pruebas:
                  └─ kqn.aplicar_estrategia(estado, condicion, alcance, mecanismo, k=5, criterio="C4")
                      │
                      ├─ sia_preparar_subsistema(...)
                      │   ├─ System(tpm, estado_inicial)
                      │   ├─ .condicionar(dims_background)
                      │   ├─ .substraer(alcance, mecanismo)
                      │   └─ .distribucion_marginal() → dm_original
                      │
                      └─ _resolver(k=5, criterio="C4")
                          │
                          └─ _buscar_particion(k=5, "C4")
                              ├─ data_nd = np.stack([c.data for c in ncubos])  # (N, 2,2,...,2)
                              ├─ pivot_idx = (estado[d] for d in dims_ncubos)
                              ├─ pivot_vals = data_nd[(...) + pivot_idx[::-1]]  # (N,)
                              │
                              └─ _refinar_c4(V, k=5, ...)
                                  ├─ _qnodes_sobre_bloque(V)           # Bipartir todo V
                                  │   ├─ _oracle_restringido(V, ...)   # Oracle local
                                  │   └─ qnodes(m, f_local, mask)      # Queyranne
                                  │
                                  ├─ heap = [(phi0, -|V|, 0, V, A0, B0)]
                                  │
                                  └─ for iteracion in range(4):  # k-1 = 4 iteraciones
                                      ├─ heappop() → (phi_sel, ..., P_sel, A_sel, B_sel)
                                      ├─ particion.remove(P_sel)
                                      ├─ particion += [A_sel, B_sel]
                                      └─ for hijo in [A_sel, B_sel] si |hijo|≥2:
                                          ├─ _qnodes_sobre_bloque(hijo)
                                          └─ heappush(heap, (phi_hijo, ...))
                                  → particion = [Pi1, Pi2, Pi3, Pi4, Pi5]
                          │
                          └─ _calcular_phi_total(particion, sistema)   # EMD una sola vez
                              ├─ dm_original = sistema.distribucion_marginal()
                              ├─ for parte Pi in particion:
                              │   ├─ ncubo.marginalizar(non_pi_dims)   # Distribucion de Pi
                              │   └─ dist_recons[d] = prob en estado pivote
                              └─ emd_efecto(dm_original, dist_recons)   → phi
                  │
                  └─ Solution(estrategia="KQNodes(k=5,C4)", perdida=phi, ...)
              │
              └─ writer.writerows(resultados)    # CSV + Markdown
```

---

## 15. Ejemplo concreto paso a paso (n=5, k=3)

Supongamos un sistema de 5 nodos (A,B,C,D,E), con D=4 dimensiones activas en el subsistema {0,1,2,3}.

### Estado inicial del sistema

```
estado_inicial = [1, 0, 1, 0, 1]   # A=ON, B=OFF, C=ON, D=OFF, E=ON
pivot_idx = (1, 0, 1, 0)            # Valor de cada dim en el estado inicial
pivot_vals = [0.7, 0.3, 0.6, 0.4, 0.8]  # p(nodo=ON | estado_pivote) para 5 nodos
```

### Llamada a _refinar_c4 con k=3

**Paso 0: Bipartir todo V = {0,1,2,3}**

Oracle con todas las 4 dims. Supongamos Queyranne devuelve:
```
best_mask = 0b0110 = 6   → dims {1,2} en A, dims {0,3} en B
phi_0 = 0.15
A0 = frozenset({1,2}), B0 = frozenset({0,3})
heap = [(0.15, -4, 0, {0,1,2,3}, {1,2}, {0,3})]
particion = [{0,1,2,3}]
```

**Iteración 1 (llegar de 1 a 2 partes)**:
```
pop: (0.15, -4, 0, {0,1,2,3}, {1,2}, {0,3})
particion = [{1,2}, {0,3}]

Hijo {1,2}: _qnodes_sobre_bloque({1,2}) → A={1}, B={2}, phi=0.08
Hijo {0,3}: _qnodes_sobre_bloque({0,3}) → A={0}, B={3}, phi=0.22

heap = [(0.08, -2, 1, {1,2}, {1}, {2}),
        (0.22, -2, 2, {0,3}, {0}, {3})]
```

**Iteración 2 (llegar de 2 a 3 partes)**:
```
pop el mínimo: (0.08, -2, 1, {1,2}, {1}, {2})
particion = [{1}, {2}, {0,3}]   ← 3 partes ✓ TERMINADO
```

### Cálculo de Φ* final

Con partición `[{1}, {2}, {0,3}]`:
- Parte {1}: Nodo 1 (B) solo → marginalizar sobre dims {0,2,3}
- Parte {2}: Nodo 2 (C) solo → marginalizar sobre dims {0,1,3}
- Parte {0,3}: Nodos 0 y 3 (A y D) → marginalizar sobre dims {1,2}

```python
dist_recons = [p(A | pivot_{0,3}), p(B | pivot_{1}), p(C | pivot_{2}),
               p(D | pivot_{0,3}), ...]
phi = emd_efecto(dm_original, dist_recons)
     = Σ |dm_original[i] - dist_recons[i]|
```

Si `dm_original = [0.7, 0.3, 0.6, 0.4, 0.8]` y `dist_recons = [0.65, 0.3, 0.6, 0.45, 0.8]`:
```
phi = |0.7-0.65| + |0.3-0.3| + |0.6-0.6| + |0.4-0.45| + |0.8-0.8|
    = 0.05 + 0.0 + 0.0 + 0.05 + 0.0 = 0.10
```

### Resultado final

```python
Solution(
    estrategia = "KQNodes(k=3,C4)",
    perdida = 0.10,              # φ*
    particion = "B | C | AD",   # Texto formateado de la partición
    tiempo_total = 0.003,        # segundos
)
```

---

## Resumen visual

```
exec_kqnodes.py                     Configuración de usuario
        │
main_kqnodes.py                     Orquestación batch (Excel → CSV)
        │
KQNodes.aplicar_estrategia()        Interfaz pública (hereda SIA)
        │
SIA.sia_preparar_subsistema()       Condicionamiento + substracción
        │
KQNodes._resolver()                 Dispatcher k=2 vs k≥3
        │
KQNodes._buscar_particion()         Preparación de datos (data_nd, pivot)
        │
KQNodes._refinar_c4()               Heurística greedy MinHeap [k-1 iters]
        │
_qnodes_sobre_bloque()              Bipartición de un bloque Pi
        │
_oracle_restringido()               Oracle lazy con caché LOCAL por bloque
        │
qnodes() [de qnodes.py]             Algoritmo de Queyranne (MAO)
        │
_calcular_phi_total()               EMD-Effect real (una sola vez)
        │
Solution(phi, particion, tiempo)    Resultado final
```

---

*Generado el 2026-06-09. Código fuente en `code/QNodes/src/strategies/kqnodes.py` (commit `6847cff`). Autor del código: Daniel Felipe Franco Rincón. Documentación de diseño: `context/SDD-3/`, `context/handoffs/03.md`.*
