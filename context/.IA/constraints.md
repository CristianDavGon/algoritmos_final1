# Constraints

Límites y restricciones técnicas del proyecto derivadas del código existente y los requisitos académicos.

## Restricciones de red / datos

- Tamaños de red operables en pruebas: **n ∈ {5, 8, 10}**. Redes n ∈ {15, 20, 22, 25} existen en samples pero el humano las ejecuta manualmente por tiempo.
- Estado inicial por defecto para n=8: `"10000000"` (only first bit active).
- Página de red por defecto: `"A"` (archivo `N8A.csv`).
- Hojas del Excel de pruebas: `{5: 1, 8: 2, 10: 3, 15: 4, 20: 5, 22: 6, 25: 7}` (índice de hoja por n).
- Formato de TPM: CSV con delimitador `,`, representación estado-nodo en notación **little-endian**.
- Fuente de pruebas: `code/data/DatosPruebas2026_1.xlsx`, columnas B:C a partir de la fila 6 (skiprows=5).

## Restricciones de k-particiones (futuras)

- Valores válidos de k: `k ∈ {2, 3, 4, 5}`.
- La tabla de costos `T` (o equivalente en KGeoMIP/KQNodes) debe calcularse **una sola vez** por sistema. Recalcularla para cada k es un anti-patrón explícito.
- Para k=2, KGeoMIP debe reproducir exactamente los resultados de GeoMIP: `|φ_nuevo - φ_viejo| < 1e-9`.
- Para k=2, KQNodes debe reproducir exactamente los resultados de QNodes: misma tolerancia.

## Restricciones de rendimiento

- Speedup objetivo: **≥ 5×** respecto a búsqueda exhaustiva para n=8.
- Timeout por prueba en ejecución batch: **3600 segundos** (1 hora, configurado en GeoMIP `main.py`).
- Métricas de calidad aceptables:
  - Tasa de acierto exacto > 90%
  - Error relativo en φ < 1%
  - Distancia Jaccard < 0.1
  - Cobertura de tests ≥ 85%

## Restricciones de código

- Máximo **300 LOC** por archivo (sin docstrings ni comentarios).
- Python **3.12+** obligatorio (f-strings con `=`, `match`, `type` hints modernos).
- No agregar dependencias sin declararlas en `pyproject.toml` y justificarlas.
- No usar imports cruzados entre estrategias.

## Restricciones de arquitectura

- Toda nueva estrategia **debe heredar de `SIA`**.
- `NCube` es `frozen=True`: nunca mutar sus atributos; crear nuevas instancias.
- El singleton `aplicacion` (`Application`) es la única fuente de configuración global (notación, semilla, distancia métrica, página de red).
- Los paths de samples se resuelven dinámicamente: no hardcodear rutas absolutas. Usar `Path(__file__).resolve().parents[N]` o las constantes de `src/constants/base.py`.

## Restricciones de formato de salida

- Resultados en CSV en `results/` de cada sub-proyecto (o futura carpeta `results/{strategy}/k={k}/n={n}.csv`).
- Columnas mínimas de resultados: `Prueba`, `Alcance`, `Mecanismo`, `Partición`, `Pérdida (φ)`, `Tiempo (s)`.
- Reportes de profiling: HTML en `review/profiling/NET{n}{pag}/{fecha}/{hora}/`.

## Restricciones de validación

- Ground-truth para k=2 en sistemas pequeños: PyPhi (ya configurado con `pyphi_config.yml`).
- Para k>2 no existe ground-truth en PyPhi. Validar con búsqueda exhaustiva interna para n≤6.
- Consistencia interna obligatoria: φ(k+1) ≤ φ(k) (más partes → menor o igual pérdida).
