# Stack

## Lenguaje y runtime

- **Python 3.12+** (declarado en `code/pyproject.toml`: `requires-python = ">=3.12"`)
- Gestor de dependencias: **uv** (archivo `code/uv.lock` presente)

## Dependencias principales (desde `code/pyproject.toml`)

| Paquete       | Versión mínima | Uso                                              |
|---------------|---------------|--------------------------------------------------|
| `numpy`       | >=2.0.2       | Operaciones matriciales, TPM, NCubes             |
| `scipy`       | >=1.17.0      | EMD (Earth Mover's Distance) y métricas          |
| `pandas`      | >=2.3.3       | Lectura de Excel, escritura de CSV, DataFrames   |
| `pyphi`       | >=1.2.0       | Referencia para validación (ground-truth k=2)    |
| `pyinstrument`| >=5.1.2       | Profiling de rendimiento (HTML report)           |
| `openpyxl`    | >=3.1.5       | Motor de lectura/escritura Excel                 |
| `colorama`    | >=0.4.6       | Output colorizado en consola                     |
| `pyttsx3`     | >=2.99        | Síntesis de voz para anunciar solución           |

## Herramientas de desarrollo

- **pytest**: pruebas unitarias e integración (estructura `tests/` en QNodes)
- **ruff**: linter (estándar del proyecto, aunque no en pyproject.toml aún)
- **mypy**: verificación de tipos estáticos
- **pyinstrument**: profiling con salida HTML en `review/profiling/`

## Configuración adicional

- `code/pyphi_config.yml` y `code/GeoMIP/pyphi_config.yml`: configuración de caché PyPhi
- `code/GeoMIP/__pyphi_cache__/`: directorio de caché PyPhi (no versionado)
- `.python-version`: fija la versión de Python para uv

## Notas de entorno

- El proyecto se ejecuta desde `code/GeoMIP/` o `code/QNodes/` como directorio de trabajo.
- Las rutas de samples se resuelven dinámicamente desde el raíz del módulo, con soporte para variable de entorno `GEOMIP_SAMPLES_DIR`.
- Configuración de red de muestra (página) se controla via `aplicacion.pagina_sample_network` (singleton `Application`).
