# Directory Structure

Estructura real del repositorio verificada desde el código fuente.

```
algoritmos_final1/
├── code/                              # Todo el código del proyecto
│   ├── data/
│   │   └── DatosPruebas2026_1.xlsx   # Fuente única de datos de prueba (compartida)
│   ├── GeoMIP/                        # Estrategia geométrica (bipartición k=2)
│   │   ├── .logs/                     # Logs por fecha/hora (no versionados)
│   │   │   └── last_*.log             # Últimos logs de cada módulo
│   │   ├── data/
│   │   │   ├── creation.py            # Generación de datasets de muestra
│   │   │   └── samples/              # TPMs precalculadas (NXY.csv)
│   │   │       ├── N3A.csv, N4A.csv, N5A.csv, N6A.csv
│   │   │       ├── N8A.csv           # Red de prueba principal (n=8)
│   │   │       ├── N10A.csv
│   │   │       └── N15A.csv, N15B.csv
│   │   ├── results/                   # CSVs y Excel de resultados
│   │   │   ├── resultados_N8A.csv
│   │   │   └── resultados_N10A.csv
│   │   ├── review/
│   │   │   └── profiling/            # HTMLs de pyinstrument por red/fecha/hora
│   │   ├── src/
│   │   │   ├── constants/
│   │   │   │   ├── base.py           # Constantes globales (paths, delimitadores, símbolos)
│   │   │   │   ├── error.py          # Mensajes de error
│   │   │   │   └── models.py         # Tags y etiquetas de estrategias
│   │   │   ├── controllers/
│   │   │   │   ├── manager.py        # Manager: rutas TPM, output_dir, generar_red()
│   │   │   │   └── strategies/
│   │   │   │       ├── geometric.py  # GeometricSIA: estrategia geométrica principal
│   │   │   │       ├── q_nodes.py    # QNodes (versión GeoMIP, usa Manager)
│   │   │   │       ├── force.py      # BruteForce: búsqueda exhaustiva
│   │   │   │       └── phi.py        # Phi: wrapper PyPhi
│   │   │   ├── funcs/
│   │   │   │   ├── base.py           # emd_efecto, ABECEDARY, seleccionar_metrica
│   │   │   │   ├── format.py         # Formateadores de bipartición
│   │   │   │   └── system.py         # biparticiones, generar_candidatos, generar_particiones
│   │   │   ├── middlewares/
│   │   │   │   ├── profile.py        # @profile decorator + ProfilerManager
│   │   │   │   └── slogger.py        # SafeLogger (logs por fecha/hora)
│   │   │   ├── models/
│   │   │   │   ├── base/
│   │   │   │   │   ├── sia.py        # SIA abstract (recibe Manager)
│   │   │   │   │   └── application.py # Application singleton
│   │   │   │   ├── core/
│   │   │   │   │   ├── system.py     # System: condicionar/substraer/bipartir
│   │   │   │   │   ├── ncube.py      # NCube: frozen dataclass hipercubo n-dim
│   │   │   │   │   └── solution.py   # Solution: resultado + visualización + voz
│   │   │   │   └── enums/
│   │   │   │       ├── distance.py   # MetricDistance enum
│   │   │   │       └── notation.py   # Notation enum
│   │   │   └── main.py               # iniciar(): orquesta lectura Excel + ejecución batch
│   │   ├── exec.py                   # Entry point: configura Application y llama iniciar()
│   │   ├── run_n10a.py               # Entry point alternativo para n=10
│   │   ├── pyphi_config.yml          # Configuración PyPhi (caché, etc.)
│   │   └── __pyphi_cache__/          # Caché PyPhi (no versionado)
│   │
│   ├── QNodes/                        # Estrategia Queyranne (bipartición k=2)
│   │   ├── results/
│   │   │   ├── resultados_N8A.csv
│   │   │   └── resultados_N10A.csv
│   │   ├── src/
│   │   │   ├── constants/            # Igual estructura que GeoMIP
│   │   │   ├── controllers/
│   │   │   │   └── manager.py        # Manager: cargar_red(), output_dir
│   │   │   ├── strategies/
│   │   │   │   ├── qnodes.py         # QNodes: oracle lazy + MAO (recibe tpm directo)
│   │   │   │   ├── q_nodes.py        # Versión alternativa QNodes
│   │   │   │   ├── force.py          # BruteForce adaptado
│   │   │   │   └── phi.py            # Phi wrapper
│   │   │   ├── funcs/
│   │   │   │   ├── iit.py            # emd_efecto para QNodes
│   │   │   │   └── format.py
│   │   │   ├── middlewares/          # profile.py, slogger.py
│   │   │   ├── models/
│   │   │   │   ├── base/
│   │   │   │   │   ├── sia.py        # SIA abstract (recibe tpm: np.ndarray)
│   │   │   │   │   └── application.py
│   │   │   │   ├── core/             # System, NCube, Solution
│   │   │   │   └── enums/
│   │   │   │       └── temporal_emd.py  # Enum adicional
│   │   │   └── main.py               # iniciar(): ejecutar_desde_excel()
│   │   ├── .samples/                 # TPMs: N2A, N3A..N15B.csv
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── PruebasIniciales.xlsx
│   │   ├── exec.py                   # Entry point QNodes
│   │   ├── run_n10a.py
│   │   └── pyphi_config.yml
│   │
│   ├── KGeoMIP/                       # [PENDIENTE] Extensión k-particiones de GeoMIP
│   └── KQNodes/                       # [PENDIENTE] Extensión k-particiones de QNodes
│
│   ├── pyproject.toml                 # Dependencias unificadas del proyecto
│   └── uv.lock                        # Lock file de uv
│
├── context/                           # Contexto para la IA
│   ├── .IA/                           # Conocimiento fijo
│   │   ├── instructions.md
│   │   ├── rules.md
│   │   ├── stack.md
│   │   ├── architecture.md
│   │   ├── coding-standards.md
│   │   ├── constraints.md
│   │   └── directory-structure.md
│   ├── project/                       # Visión global del proyecto
│   │   ├── requirements.md
│   │   ├── phases.md
│   │   ├── decisions.md
│   │   └── risks.md
│   ├── handoffs/                      # Memoria temporal entre fases/agentes
│   ├── SDD-1/                         # Documentación de la Fase 1
│   │   ├── planning.md
│   │   ├── implementation.md
│   │   ├── decisions.md
│   │   ├── done-criteria.md
│   │   └── testing.md
│   └── state/                         # Estado actual del proyecto
│       ├── current-phase.md
│       ├── progress.md
│       ├── active-tasks.md
│       └── known-issues.md
│
├── traceability_data/                 # Trazabilidad de conversaciones con IA
├── docs/                              # Manuales técnico y de usuario (LaTeX)
├── others/                            # Insumos adicionales
├── prompt.md                          # Estructura de carpetas del proyecto
├── contextualizacion.md               # Contexto adicional del proyecto
└── intruction.md                      # Instrucciones para la IA
```

## Notas sobre rutas

- Los samples de GeoMIP están en `code/GeoMIP/data/samples/` pero el `Manager` los busca dinámicamente (primero `src/.samples/`, luego `data/samples/`).
- Los samples de QNodes están en `code/QNodes/src/.samples/`.
- Los resultados CSV se guardan en `code/GeoMIP/results/` y `code/QNodes/results/`.
- Los profiling HTMLs se generan en `code/GeoMIP/review/profiling/NET{n}{pag}/{fecha}/{hora}/`.
