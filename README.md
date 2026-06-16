# Proyecto V03 Final - MIP / IIT k-particiones

Implementaciones experimentales para calcular particiones de minima informacion
(MIP) en el marco de IIT, con dos familias de algoritmos:

| Modulo | Archivo de entrada | Enfoque | Salida principal |
| --- | --- | --- | --- |
| `QNodes` | `QNodes/exec.py` | Biparticion con Queyranne y oracle lazy | `QNodes/results/qnodes/` |
| `KQNodes` | `QNodes/exec_kqnodes.py` | Extension greedy de QNodes a k-particiones | `QNodes/results/kqnodes/` |
| `GeoMIP` | `GeoMIP/exec.py` | Biparticion geometrica sobre hipercubo de Hamming | `GeoMIP/results/geomip/` |
| `KGeoMIP` | `GeoMIP/exec_kgeomip.py` | Extension divisiva E4 / aglomerativa a k-particiones | `GeoMIP/results/kgeomip/` |

El proyecto tambien incluye una suite de pruebas para comparar resultados contra
PyPhi y contra busqueda exhaustiva en redes pequenas.

## Requisitos

- Python `>=3.12`
- `uv` para sincronizar dependencias
- Windows, Linux o macOS con suficiente memoria para cargar las TPM grandes

Dependencias principales declaradas en `pyproject.toml`:

- `numpy`, `pandas`, `scipy`
- `pyphi`
- `openpyxl`
- `pyinstrument`
- `colorama`

## Instalacion

Desde la raiz del repositorio:

```bash
pip install uv
uv sync
```

El archivo `pyphi_config.yml` desactiva el mensaje de bienvenida de PyPhi.

## Estructura

```text
algoritmos_final1/
|-- data/
|   `-- DatosPruebas2026_1.xlsx      # Excel canonico de casos alcance/mecanismo
|-- QNodes/
|   |-- exec.py                      # QNodes, k=2
|   |-- exec_kqnodes.py              # KQNodes, k>=1
|   `-- src/
|       |-- .samples/                # TPMs usadas por QNodes
|       |-- main.py
|       |-- main_kqnodes.py
|       `-- strategies/
|-- GeoMIP/
|   |-- exec.py                      # GeoMIP, k=2
|   |-- exec_kgeomip.py              # KGeoMIP, k>=1
|   |-- data/samples/                # TPMs usadas por GeoMIP
|   `-- src/
|       |-- main.py
|       |-- main_kgeomip.py
|       `-- controllers/strategies/
|-- tests/
|   |-- core/                        # Runner generico de benchmarks
|   |-- adapters/                    # Adaptadores QNodes, GeoMIP, PyPhi, brute force
|   |-- suites/                      # Pruebas por familia
|   `-- results/                     # Reportes generados
|-- pyproject.toml
`-- uv.lock
```

## Datos de entrada

El Excel `data/DatosPruebas2026_1.xlsx` contiene los pares
`Alcance` / `Mecanismo` en columnas B:C. La longitud del estado inicial define
`N` y selecciona la hoja del Excel:

| N | Hoja |
| --- | --- |
| 5 | 1 |
| 8 | 2 |
| 10 | 3 |
| 15 | 4 |
| 20 | 5 |
| 22 | 6 |
| 25 | 7 |

Las TPMs se nombran como `N{n}{pagina}.csv`, por ejemplo `N8A.csv`.

- QNodes busca muestras en `QNodes/src/.samples/`.
- GeoMIP busca muestras en `GeoMIP/data/samples/` y, como respaldo, en rutas
  `.samples`.
- Las muestras grandes `N20A.csv`, `N22A.csv` y `N25A.csv` estan ignoradas por
  git por su tamano, aunque pueden existir localmente.

## Ejecucion de algoritmos

Los scripts de entrada tienen constantes editables arriba del archivo:

- `ESTADO`: cadena binaria. Su longitud determina `N`.
- `MUESTRA`: pagina de red, normalmente `A` o `B`.
- `K`: numero de partes para los algoritmos k-particion.
- `CRITERIO` o `VARIANTE`: heuristica usada por la extension k.

### QNodes

```bash
cd QNodes
uv run python exec.py
```

Por defecto ejecuta QNodes sobre todas las filas del Excel para el `N` indicado
por `ESTADO` y guarda:

```text
QNodes/results/qnodes/resultado__N{n}_{MUESTRA}.csv
QNodes/results/qnodes/resultado__N{n}_{MUESTRA}.md
```

### KQNodes

```bash
cd QNodes
uv run python exec_kqnodes.py
```

Usa `K` y `CRITERIO` desde `exec_kqnodes.py`.

- `CRITERIO="C4"`: corte marginal minimo.
- `CRITERIO="C1"`: bloque de tamano maximo.

Salida:

```text
QNodes/results/kqnodes/resultado__N{n}_{MUESTRA}_{K}.csv
QNodes/results/kqnodes/resultado__N{n}_{MUESTRA}_{K}.md
```

### GeoMIP

```bash
cd GeoMIP
uv run python exec.py
```

Para redes `N <= 20` corre en el proceso principal. Para redes mayores usa
`multiprocessing.Pool` con timeout por prueba.

Salida por defecto:

```text
GeoMIP/results/geomip/resultados_N{n}{MUESTRA}.csv
GeoMIP/results/geomip/resultados_N{n}{MUESTRA}.md
```

GeoMIP tambien acepta variables de entorno:

| Variable | Uso | Valor por defecto |
| --- | --- | --- |
| `GEOMIP_INPUT_XLSX` | Excel de pruebas | `data/DatosPruebas2026_1.xlsx` |
| `GEOMIP_OUTPUT_CSV` | Ruta CSV de salida | `GeoMIP/results/geomip/resultados_N{n}{MUESTRA}.csv` |
| `GEOMIP_ESTADO_INICIO` | Estado si no se pasa por codigo | `1000000000000000000000000` |
| `GEOMIP_SAMPLES_DIR` | Directorio alternativo de TPMs | autodetectado |

Ejemplo en PowerShell:

```powershell
$env:GEOMIP_ESTADO_INICIO = "10000000"
cd GeoMIP
uv run python exec.py
```

### KGeoMIP

```bash
cd GeoMIP
uv run python exec_kgeomip.py
```

Usa `K` y `VARIANTE` desde `exec_kgeomip.py`.

- `VARIANTE="E4"`: refinamiento divisivo recomendado.
- `VARIANTE="A"`: baseline aglomerativo.

Salida:

```text
GeoMIP/results/kgeomip/resultado__N{n}_{MUESTRA}_{K}.csv
GeoMIP/results/kgeomip/resultado__N{n}_{MUESTRA}_{K}.md
```

## Formato de resultados

Los CSV de biparticion incluyen:

| Columna | Significado |
| --- | --- |
| `Prueba` | Numero de caso tomado del Excel |
| `Alcance` | Alcance en letras |
| `Mecanismo` | Mecanismo en letras |
| `Particion` | Particion encontrada |
| `Perdida (phi)` | Valor de perdida / phi |
| `Tiempo (s)` | Tiempo de ejecucion |

Los CSV de k-particion agregan:

| Columna | Significado |
| --- | --- |
| `k` | Numero de partes solicitado |
| `Criterio` | Criterio o variante usada |

Nota: en los archivos generados, las columnas con acentos y el simbolo phi se
escriben en UTF-8.

## Benchmarks y pruebas

El runner generico ejecuta un algoritmo contra PyPhi o brute force:

```bash
uv run python tests/core/run_benchmark.py --algo qnodes --estado 10000 --pagina A
uv run python tests/core/run_benchmark.py --algo geomip --estado 10000 --pagina A
uv run python tests/core/run_benchmark.py --algo qnodes --estado 10000 --pagina A --reference bruteforce
uv run python tests/core/run_benchmark.py --algo geomip --estado 10000 --pagina A --n-tests 5
```

Los reportes se guardan en:

```text
tests/results/{algoritmo}/vs_{referencia}/
```

Tambien existe un barrido de estados validos:

```bash
uv run python tests/run_all_states.py --dry-run
uv run python tests/run_all_states.py --algo qnodes --reference pyphi --n-tests 5
```

Importante: QNodes y GeoMIP usan ambos un paquete raiz llamado `src`. Por eso,
las pruebas de cada familia deben ejecutarse en procesos separados para evitar
sombras de importacion.

Ejemplos seguros:

```bash
uv run python -m pytest tests/suites/qnodes/test_qnodes_vs_pyphi.py -v -s
uv run python -m pytest tests/suites/geomip/test_geomip_vs_pyphi.py -v -s
uv run python -m pytest tests/suites/kgeomip/test_kgeomip.py -v -s
```

## Notas de implementacion

- `QNodes` implementa Queyranne para minimizar una funcion simetrica con
  evaluaciones lazy y cacheadas.
- `KQNodes` parte de QNodes y divide bloques de forma greedy para alcanzar
  `k` partes.
- `GeoMIP` construye una tabla de costos sobre niveles de distancia Hamming y
  valida candidatos con EMD real.
- `KGeoMIP` ancla `k=2` en GeoMIP, reutiliza caches por subsistema y para
  `k>=3` usa refinamiento divisivo E4 o la variante aglomerativa `A`.
- Los scripts batch leen todas las pruebas disponibles en el Excel para el `N`
  seleccionado, por lo que redes grandes pueden tardar bastante.
