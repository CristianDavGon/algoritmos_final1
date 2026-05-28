# Coding Standards

Estándares aplicados en el código existente de GeoMIP y QNodes, que deben mantenerse en las extensiones KGeoMIP y KQNodes.

## Nomenclatura

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Funciones y métodos | `snake_case` | `aplicar_estrategia`, `sia_preparar_subsistema` |
| Variables | `snake_case` | `estado_inicial`, `dims_condicionadas` |
| Clases | `PascalCase` | `GeometricSIA`, `NCube`, `Solution` |
| Constantes | `UPPER_SNAKE_CASE` | `FLOAT_ZERO`, `SAMPLES_PATH`, `STR_ZERO` |
| Atributos de instancia de SIA | Prefijo `sia_` | `sia_gestor`, `sia_subsistema`, `sia_dists_marginales` |
| Tags de logging | Sufijo `_TAG` | `GEOMETRIC_STRAREGY_TAG`, `SIA_PREPARATION_TAG` |

## Type hints

Obligatorios en **toda** firma pública. Usar `numpy.typing.NDArray` para arreglos numpy tipados:

```python
def aplicar_estrategia(
    self,
    condicion: str,
    alcance: str,
    mecanismo: str,
    tpm: np.ndarray,
) -> Solution:
    ...

def marginalizar(self, ejes: NDArray[np.int8]) -> "NCube":
    ...
```

## Docstrings

Estilo **NumPy/Google** en español en todos los métodos públicos. Estructura mínima:

```python
def metodo(self, param: tipo) -> tipo_retorno:
    """Descripción una línea del propósito.

    Args:
        param (tipo): Descripción del parámetro.

    Returns:
        tipo_retorno: Descripción del retorno.

    Raises:
        ExceptionType: Cuándo se lanza.

    Examples:
        >>> ejemplo de uso
    """
```

## Estructura de archivos

- Máximo **300 LOC** por archivo (sin contar docstrings ni comentarios).
- Si un módulo supera 300 LOC, refactorizar antes de continuar.
- Constantes globales siempre en `src/constants/base.py` o `src/constants/models.py`, nunca inline en las clases.
- Paths de archivos siempre como constantes en `src/constants/base.py`.

## Imports

Orden estándar (PEP 8): stdlib → third-party → local. Ejemplo del proyecto:

```python
import time
from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
import numpy.typing as NDArray

from src.constants.base import FLOAT_ZERO, STR_ZERO
from src.models.base.sia import SIA
```

## Patrones de diseño en uso

- **Strategy**: cada algoritmo de búsqueda de MIP hereda de `SIA` e implementa `aplicar_estrategia()`.
- **Template Method**: `SIA.sia_preparar_subsistema()` define el flujo común; subclases implementan el algoritmo.
- **Singleton**: `aplicacion = Application()` en `src/models/base/application.py`.
- **Dataclass frozen**: `NCube` usa `@dataclass(frozen=True)` para inmutabilidad.
- **Lazy cache / Memoization**: oracle en QNodes usa `dict` como cache; tabla de transiciones en GeoMIP similar.

## Logging

Usar `SafeLogger` del módulo `src/middlewares/slogger.py`, nunca `print()` en código de producción (los `print()` existentes son temporales de desarrollo):

```python
self.logger = SafeLogger(MI_TAG)
self.logger.critic("mensaje crítico")
self.logger.info("información general")
self.logger.debug("detalle de debugging")
```

## Profiling

Decorar métodos costosos con `@profile` de `src/middlewares/profile.py`:

```python
@profile(context={TYPE_TAG: MI_ANALYSIS_TAG})
def aplicar_estrategia(self, ...):
    ...
```

## Manejo de errores

- Validar parámetros al inicio del método (fail-fast).
- Lanzar excepciones concretas con mensajes desde `src/constants/error.py`.
- No capturar excepciones genéricas silenciosamente salvo en capas de I/O.

## Idioma

- Código (nombres de variables, funciones, clases): español, siguiendo el patrón del proyecto.
- Docstrings: español.
- Mensajes de consola y logs: español.
- Comentarios inline: español.
