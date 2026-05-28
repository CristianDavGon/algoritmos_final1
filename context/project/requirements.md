# Requirements

Qué debe hacer el sistema, derivado del código actual y los objetivos académicos del proyecto.

## Contexto del problema

En el marco de la **Teoría de la Información Integrada (IIT 4.0)**, la **Partición de Mínima Información (MIP)** identifica la división de un sistema causal que minimiza la pérdida de información integrada (φ). Las estrategias actuales (`GeoMIP`, `QNodes`) resuelven el caso bipartición (k=2). Este proyecto las extiende al caso k-particiones con `k ∈ {2, 3, 4, 5}`.

## Requisitos funcionales implementados

### RF-01: Carga de TPM desde archivo
- El sistema lee Transition Probability Matrices (TPM) en formato CSV (estado-nodo, little-endian).
- Soporta redes de tamaño n ∈ {3, 4, 5, 6, 8, 10, 15} según archivos en `data/samples/`.
- Fuente canónica de pruebas: `code/data/DatosPruebas2026_1.xlsx`.

### RF-02: Preparación de subsistema
- Dado un estado inicial, condición, alcance y mecanismo (como cadenas binarias), construye el subsistema relevante.
- Pipeline: Sistema completo → condicionar → substraer → subsistema.
- Calcula distribución marginal del subsistema para comparación posterior.

### RF-03: Estrategia GeoMIP (bipartición, k=2)
- Implementada en `GeometricSIA` (`code/GeoMIP/src/controllers/strategies/geometric.py`).
- Construye tabla de transiciones con costos Hamming entre estados.
- Identifica candidatos de bipartición por nivel y evalúa EMD-efecto real.
- Retorna `Solution` con la bipartición de mínima pérdida φ.

### RF-04: Estrategia QNodes (bipartición, k=2)
- Implementada en `QNodes` (`code/QNodes/src/strategies/qnodes.py`).
- Minimiza función submodular simétrica via MAO de Queyranne (O(D³) vs O(2^D)).
- Oracle lazy con cache: evalúa solo los O(D³) masks pedidos por MAO.
- Pre-pass de singletons como salvaguarda para funciones no submodulares.
- Retorna `Solution` con bipartición y tiempo de ejecución.

### RF-05: Ejecución batch desde Excel
- Lee todos los casos de prueba del Excel (`alcance`, `mecanismo` como letras: "ABCD").
- Convierte letras a cadenas binarias y ejecuta la estrategia para cada caso.
- Guarda resultados en CSV: `Prueba, Alcance, Mecanismo, Partición, Pérdida (φ), Tiempo (s)`.
- Timeout por prueba: 3600 segundos.

### RF-06: Estrategia de fuerza bruta (validación)
- `BruteForce` enumera todas las biparticiones posibles: O(2^(m+n-1)) evaluaciones.
- Usada como ground-truth para n pequeño (n ≤ 6).

### RF-07: Visualización de resultados
- `Solution.__str__()` muestra resultado colorizado en consola (colorama).
- Incluye distribuciones marginales, partición formateada y tiempo de ejecución.
- Anuncio por síntesis de voz (pyttsx3) al encontrar solución.

### RF-08: Profiling de rendimiento
- Decorador `@profile` genera reportes HTML con pyinstrument.
- Almacenados en `review/profiling/NET{n}{pag}/{fecha}/{hora}/`.

## Requisitos funcionales pendientes (extensión k-particiones)

### RF-09: KGeoMIP — extensión geométrica a k-particiones
- [PENDIENTE] Extiende GeoMIP para k ∈ {2, 3, 4, 5}.
- Reutiliza infraestructura NCube y tabla de transiciones de GeoMIP.
- Para k=2 debe reproducir exactamente el resultado de GeoMIP (`|φ_nuevo - φ_viejo| < 1e-9`).
- Hereda de `SIA`.

### RF-10: KQNodes — extensión submodular a k-particiones
- [PENDIENTE] Extiende QNodes para k ∈ {2, 3, 4, 5}.
- Reutiliza el algoritmo Queyranne/MAO de QNodes.
- Para k=2 debe reproducir exactamente el resultado de QNodes.
- Hereda de `SIA`.

### RF-11: Tabla de costos compartida (anti-duplicación)
- [PENDIENTE] La tabla de costos T se calcula una sola vez por sistema y se reutiliza para k=2,3,4,5.
- Test debe verificar que `T.calls_count == 1` tras ejecutar todos los k sobre el mismo sistema.

### RF-12: Salida en formato extendido para k-particiones
- [PENDIENTE] CSV con columnas: `system_id, partition_repr, phi_loss, exec_time_sec, candidates_evaluated, optimal_known, error_relative`.
- Almacenado en `results/{strategy}/k={k}/n={n}.csv`.

## Requisitos no funcionales

### RNF-01: Rendimiento
- Speedup ≥ 5× respecto a búsqueda exhaustiva para n=8.

### RNF-02: Correctitud
- Tasa de acierto exacto > 90% (Excelente) para sistemas de tamaño pequeño validables.
- Error relativo en φ < 1%.

### RNF-03: Calidad de código
- Cobertura de tests ≥ 85%.
- Máximo 300 LOC por archivo.
- Tipado completo con mypy sin errores.

### RNF-04: Reproducibilidad
- Semilla numpy fija: `aplicacion.semilla_numpy = 73`.
- Resultados deterministas para una misma red y estado inicial.
