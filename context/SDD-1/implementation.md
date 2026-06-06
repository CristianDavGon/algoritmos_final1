# SDD-1 — Implementation: Guía de comprensión del código

> Este documento es la fuente viva de comprensión. Se llena durante la Fase 1.

---

## 1. Flujo de ejecución — GeoMIP

```
exec.py
  └── Application.configurar(n, pagina, semilla)   # singleton global
      └── iniciar(n, pagina)                        # src/main.py
          └── _leer_pruebas_excel(xlsx, n)          # lee hoja n del Excel
              └── para cada (alcance_letras, mecanismo_letras):
                  └── _letras_a_binario(texto, n)   # "ABC" → "11100000"
                  └── Manager(estado_inicial, pagina, n)
                  └── GeometricSIA(gestor)
                      └── __init__: profiler_manager.start_session()
                  └── aplicar_estrategia(condicion, alcance, mecanismo, tpm)
                      └── sia_preparar_subsistema(...)
                          └── System(tpm, estado_inicial)   → completo
                          └── completo.condicionar(dims_condicionadas) → candidato
                          └── candidato.substraer(dims_alcance, dims_mecanismo) → subsistema
                          └── subsistema.distribucion_marginal() → dists_marginales
                      └── find_mip()
                          └── calcular_costos_nivel(estado_final, nivel)
                              └── calcular_costo(ini, fin, ncubos)
                                  └── tabla_transiciones[(ini, fin)] = [costos por variable]
                          └── identificar_particiones_optimas() → candidatos
                          └── para cada candidato:
                              └── subsistema.bipartir(futuros, presentes) → dist_particion
                              └── emd_efecto(dist_particion, dists_marginales) → φ
                      └── Solution(perdida=φ, particion=fmt, ...)
                  └── guardar CSV en results/
```

### Contratos clave en GeoMIP

| Clase/Función | Entrada | Salida | Invariante |
|---------------|---------|--------|------------|
| `System(tpm, estado_inicio)` | tpm: ndarray shape=(2^n, n), estado_inicio: ndarray shape=(n,) | System con n NCubes | `len(ncubos) == tpm.shape[1]` |
| `System.condicionar(indices)` | indices: NDArray[int8] con dims a condicionar | Nuevo System (reducido) | Los ncubos resultantes tienen dims sin las condicionadas |
| `System.substraer(alcance, mecanismo)` | alcance, mecanismo: arrays de índices a QUITAR | Subsistema resultante | Solo quedan ncubos en intersección de alcance y mecanismo |
| `System.bipartir(futuros, presentes)` | futuros: índices ncubos, presentes: dims | System bipartido | Usado para calcular distribución de la partición |
| `SIA.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm)` | strings binarios + TPM | Setea `self.sia_subsistema` y `self.sia_dists_marginales` | Strings deben tener igual longitud que estado_inicial |
| `emd_efecto(dist_particion, dist_subsistema)` | dos ndarray de probabilidades | float φ ≥ 0 | φ=0 si las distribuciones son iguales |
| `GeometricSIA.find_mip()` | (usa self.sia_subsistema) | tuple de nodos (la bipartición ganadora) | Recorre niveles Hamming 1..n |

---

## 2. Flujo de ejecución — QNodes

```
exec.py
  └── Application.configurar(...)
      └── iniciar() / ejecutar_desde_excel()    # src/main.py
          └── Manager(...)
              └── cargar_red() → tpm: np.ndarray   # carga TPM directo (vs GeoMIP que lo hace en sia_cargar_tpm)
          └── QNodes(tpm)                          # SIA recibe tpm, no gestor
              └── aplicar_estrategia(condicion, alcance, mecanismo, tpm)
                  └── sia_preparar_subsistema(...)  # igual que GeoMIP
                  └── data_nd = subsistema aplanado en (N, 2, 2, ..., 2)
                  └── oracle(N, D, data_nd, pivot_idx, pivot_vals, full_mask)
                      → f(mask_a): float   # función submodular simétrica con cache
                  └── qnodes(D, f, full_mask)
                      → (best_val, best_mask_a)    # MAO O(D³)
                  └── derivar (alcance, mecanismo) desde best_mask_a
                  └── emd_efecto(dist_particion, dists_marginales) → φ
                  └── Solution(perdida=φ, ...)
```

### Diferencias arquitectónicas reales (verificadas en código)

| Aspecto | GeoMIP | QNodes |
|---------|--------|--------|
| `SIA.__init__` recibe | `Manager` (gestor) | `np.ndarray` (tpm) |
| Ubicación estrategias | `src/controllers/strategies/` | `src/strategies/` |
| Carga de TPM | En `sia_cargar_tpm()` o como parámetro (tiene `#! COMENTAR`) | `Manager.cargar_red()` antes de instanciar QNodes |
| Profiling | `profiler_manager.start_session()` en `__init__` | Decorador `@perfilar` |
| Algoritmo central | Tabla de transiciones Hamming + candidatos geométricos | Oracle lazy + MAO (Queyranne 1998) |
| Muestras | `data/samples/NXA.csv` | `src/.samples/NXA.csv` |
| Batch | `multiprocessing.Process` con timeout=3600 | Ejecución secuencial simple |
| `aplicar_estrategia` signature | `(condicion, alcance, mecanismo, tpm)` — tpm como param | Igual |

---

## 3. Modelo de dominio central

### NCube
- **Frozen dataclass**: inmutable después de crearse.
- `indice: int` — qué nodo representa (0=A, 1=B, ...).
- `dims: NDArray[int8]` — dimensiones activas (se reducen al condicionar/marginalizar).
- `data: ndarray` — hipercubo con shape `(2,) * len(dims)`. Cada celda es una probabilidad de transición.

### System
- Colección `tuple[NCube]` + `estado_inicial: ndarray`.
- `condicionar(indices)`: aplica condiciones de fondo — selecciona el slice del NCube según el valor del `estado_inicial` en esas dimensiones.
- `substraer(alcance, mecanismo)`: marginaliza (promedia) las dimensiones no incluidas en `alcance` (futuros) o `mecanismo` (presentes).
- `bipartir(futuros, presentes)`: genera el sistema bipartido para calcular la distribución de la partición.
- `distribucion_marginal()`: producto tensorial de distribuciones marginales por NCube → distribución conjunta.

### Solution
- Contiene: `estrategia`, `perdida` (φ), `distribucion_subsistema`, `distribucion_particion`, `tiempo_total`, `particion` (texto formateado).
- Tiene visualización colorizada en consola y opcional síntesis de voz.

---

## 4. Deuda técnica identificada

> Se completa durante la lectura del código.

| ID | Archivo | Línea(s) | Descripción |
|----|---------|----------|-------------|
| DT-05 | `code/GeoMIP/src/models/base/sia.py` | 61, 90 | Comentarios `#! COMENTAR / DESCOMENTAR` — indica toggle manual en producción |
| DT-06 | `code/GeoMIP/src/controllers/strategies/geometric.py` | 51-61 | Docstring como prosa de diseño, no contrato — no describe entradas/salidas |
| DT-07 | `code/GeoMIP/src/controllers/strategies/geometric.py` | ~200-230 | Bloque grande de código comentado (`# presentes_1 = ...`, etc.) — código muerto |
