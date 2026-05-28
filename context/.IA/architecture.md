# Architecture

## Visión general

El proyecto contiene dos sub-proyectos paralelos bajo `code/`, cada uno implementando una estrategia de bipartición (k=2) para hallar la MIP:

- `code/GeoMIP/` — Estrategia geométrica-topológica (tabla de transiciones + costos Hamming)
- `code/QNodes/` — Estrategia submodular (algoritmo de Queyranne con MAO)

Ambos comparten: la misma fuente de datos (`code/data/DatosPruebas2026_1.xlsx`), las mismas abstracciones de dominio (`SIA`, `System`, `NCube`, `Solution`, `Manager`) y el mismo patrón de ejecución.

## Patrón arquitectónico

**Strategy + Template Method**: `SIA` es la clase base abstracta que define el contrato (`aplicar_estrategia()`). Cada estrategia concreta implementa el algoritmo específico.

```
SIA (abstract)
├── GeometricSIA   [GeoMIP] — tabla de transiciones geométrica
├── QNodes         [QNodes] — MAO + oracle lazy (Queyranne 1998)
├── BruteForce     [GeoMIP] — búsqueda exhaustiva (validación)
├── [FASE 4] KQNodes  — extensión k-particiones submodular (PRIORIDAD 1)
└── [FASE 5] KGeoMIP  — extensión k-particiones geométrica (PRIORIDAD 2)
```

> **Orden de implementación**: KQNodes precede a KGeoMIP por mejor complejidad algorítmica (O(D³) extendible iterativamente) y menor riesgo de escalabilidad. Ver DEC-10.

## Módulos por sub-proyecto

### GeoMIP (`code/GeoMIP/src/`)

```
src/
├── constants/
│   ├── base.py        — constantes globales (paths, delimitadores, símbolos)
│   ├── error.py       — mensajes de error
│   └── models.py      — tags y etiquetas de estrategias
├── controllers/
│   ├── manager.py     — Manager: gestiona rutas de TPM y directorios de salida
│   └── strategies/
│       ├── geometric.py  — GeometricSIA: algoritmo geométrico-topológico
│       ├── q_nodes.py    — QNodes (versión en GeoMIP, usando Manager)
│       ├── force.py      — BruteForce: búsqueda exhaustiva
│       └── phi.py        — Phi: wrapper PyPhi para ground-truth
├── funcs/
│   ├── base.py        — emd_efecto, ABECEDARY, seleccionar_metrica, literales
│   ├── format.py      — formateadores de bipartición para consola
│   └── system.py      — generadores de particiones, candidatos, subsistemas
├── middlewares/
│   ├── profile.py     — decorador @profile + profiler_manager (pyinstrument)
│   └── slogger.py     — SafeLogger: logging estructurado por fecha/hora
├── models/
│   ├── base/
│   │   ├── sia.py         — SIA: clase abstracta base (recibe Manager)
│   │   └── application.py — Application singleton (configuración global)
│   ├── core/
│   │   ├── system.py      — System: colección de NCubes con condicionar/substraer/bipartir
│   │   ├── ncube.py       — NCube: hipercubo n-dimensional (frozen dataclass)
│   │   └── solution.py    — Solution: resultado con visualización colorizada + voz
│   └── enums/
│       ├── distance.py    — MetricDistance enum
│       └── notation.py    — Notation enum (LIL_ENDIAN)
└── main.py            — iniciar(): lógica de orquestación y lectura del Excel
```

### QNodes (`code/QNodes/src/`)

```
src/
├── constants/        — igual estructura que GeoMIP
├── controllers/
│   └── manager.py    — Manager: similar a GeoMIP pero con cargar_red()
├── strategies/
│   ├── qnodes.py     — QNodes: oracle lazy + MAO (recibe tpm directo, no Manager)
│   ├── q_nodes.py    — versión alternativa de QNodes
│   ├── force.py      — BruteForce adaptado
│   └── phi.py        — Phi wrapper
├── funcs/
│   ├── iit.py        — emd_efecto para QNodes
│   └── format.py     — formateadores
├── middlewares/      — igual que GeoMIP
└── models/
    ├── base/
    │   ├── sia.py         — SIA: recibe tpm (np.ndarray) directo, no Manager
    │   └── application.py
    ├── core/             — System, NCube, Solution (misma lógica)
    └── enums/
        └── temporal_emd.py — enum adicional
```

## Diferencias arquitectónicas clave entre GeoMIP y QNodes

| Aspecto | GeoMIP | QNodes |
|---------|--------|--------|
| `SIA.__init__` recibe | `Manager` | `np.ndarray` (tpm) |
| Ubicación de estrategias | `src/controllers/strategies/` | `src/strategies/` |
| Manager expone | `tpm_filename`, `output_dir` | `cargar_red()`, `output_dir` |
| Profiling | `profiler_manager.start_session()` en `__init__` | Decorador `@perfilar` |
| Muestras de datos | `data/samples/NXA.csv` | `src/.samples/NXA.csv` |

## Flujo de ejecución

```
exec.py → iniciar()
  → _leer_pruebas_excel(DatosPruebas2026_1.xlsx, n)  # hoja por n: {5:1, 8:2, 10:3}
  → para cada (alcance_letras, mecanismo_letras):
      → _letras_a_binario(texto, n_bits)  # 'ABCD' → '1111'
      → Manager(estado_inicial)           # gestiona rutas
      → Estrategia(gestor/tpm)            # instancia la estrategia
      → aplicar_estrategia(condicion, alcance, mecanismo, tpm)
          → sia_preparar_subsistema()     # condicionar + substraer
          → algoritmo específico()        # geométrico o Queyranne
          → Solution(perdida, distribuciones, particion, tiempo)
      → guardar en CSV de resultados
```

## Modelo de dominio central

```
System
  └── tuple[NCube]          # un NCube por nodo del sistema
        ├── indice: int     # índice del nodo (0=A, 1=B, ...)
        ├── dims: NDArray   # dimensiones activas (se reducen al condicionar/marginalizar)
        └── data: ndarray   # hipercubo shape=(2,)*len(dims)

System.condicionar(indices)  → System  # aplica condiciones de fondo
System.substraer(alcance, mecanismo) → System  # genera subsistema
System.bipartir(alcance, mecanismo)  → System  # genera una bipartición
System.distribucion_marginal()       → ndarray # distribución para EMD
```

## Algoritmo GeometricSIA (resumen)

1. Prepara subsistema (condicionar + substraer).
2. Construye `tabla_transiciones[estado_ini, estado_fin]` con costos de transición Hamming para cada par de estados.
3. Recorre niveles de distancia Hamming desde estado inicial hasta estado final.
4. `identificar_particiones_optimas()`: evalúa candidatos y selecciona el de menor costo.
5. Para cada candidato, calcula EMD-efecto real vía `System.bipartir()`.
6. Retorna la bipartición con mínima pérdida φ.

## Algoritmo QNodes/Queyranne (resumen)

1. Prepara subsistema.
2. Oracle lazy con cache: evalúa `f(mask_a)` solo para los O(D³) masks pedidos por MAO.
3. MAO (Maximum Adjacency Ordering): D-1 iteraciones, O(D²) llamadas al oracle por iteración.
4. Pre-pass de singletons como salvaguarda para funciones no submodulares.
5. Deriva alcance/mecanismo del mejor mask encontrado.
6. Calcula EMD-efecto real y retorna `Solution`.
