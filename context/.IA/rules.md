# Rules

Reglas duras que el agente NO puede violar sin confirmación explícita del usuario.

## Ejecución y datos

- Trabajar únicamente con redes n ∈ {5, 8, 10} en pruebas iterativas. Redes mayores (15, 20+) las ejecuta el humano.
- Red por defecto para pruebas: **n=8**, estado inicial `"10000000"`, página `"A"`.
- Valores válidos de k: `k ∈ {2, 3, 4, 5}`. Cualquier otro k requiere aprobación explícita.
- Fuente única de verdad para datos de prueba: `code/data/DatosPruebas2026_1.xlsx`. No generar datos sintéticos sin autorización.
- La tabla de costos de transición `T` (o equivalente) se calcula **una sola vez** por sistema y se reutiliza para todos los valores de k. Recalcularla por cada k es un anti-patrón.

## Calidad de código

- Máximo **300 LOC** por archivo (excluyendo docstrings y comentarios). Si se excede, refactorizar primero.
- **Single Responsibility Principle**: una clase = una responsabilidad.
- Alta cohesión, bajo acoplamiento. Las estrategias no se importan entre sí directamente.
- Tipado obligatorio con `type hints` en toda firma pública.
- Docstrings estilo Google o NumPy en todo método público.
- Nomenclatura: `snake_case` para funciones/variables, `PascalCase` para clases, `UPPER_SNAKE` para constantes.

## Proceso

- **TDD**: tests primero, implementación después.
- Toda modificación a estrategia existente debe pasar los tests de regresión para k=2 antes de mergear.
- No mergear código que no compile, no tenga tests o cuyo linter falle.
- No saltar hooks (`--no-verify`) ni firmas sin aprobación explícita.

## Nomenclatura del proyecto (no negociable)

| Estrategia base | Extensión k-particiones |
|-----------------|------------------------|
| GeoMIP          | **KGeoMIP**            |
| QNodes          | **KQNodes**            |

Aplica a: nombres de clase, módulos, documentación y resultados.

## Reutilización obligatoria

- KGeoMIP debe reutilizar la infraestructura de N-Cubos de GeoMIP (`NCube`, `System`).
- KQNodes debe reutilizar la minimización submodular (algoritmo Queyranne/MAO) de QNodes.
- Ambas clases deben heredar de `SIA`.
