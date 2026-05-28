# Risks

Riesgos conocidos del proyecto con probabilidad, impacto y mitigación.

---

## R-01: Función de pérdida φ para k>2 no está formalizada

**Probabilidad**: Alta  
**Impacto**: Bloqueante — sin definición formal no se puede implementar KGeoMIP ni KQNodes.

**Descripción**: El enunciado del proyecto no define explícitamente cómo calcular φ para k-particiones (k>2). El supuesto actual (suma de discrepancias entre el producto tensorial de k marginales y la distribución conjunta) puede no ser el correcto.

**Mitigación**: Consultar al usuario/docente antes de implementar. Marcar como `[BLOQUEANTE]` en código.

---

## R-02: Queyranne para k>2 puede ser heurístico, no exacto

**Probabilidad**: Media  
**Impacto**: Alto — afecta la garantía de correctitud de KQNodes.

**Descripción**: El algoritmo de Queyranne garantiza encontrar la bipartición óptima para funciones simétricas submodulares. Para k>2 no hay garantía equivalente. La extensión puede requerir aplicación iterativa (greedy), con riesgo de quedar atrapado en óptimos locales.

**Mitigación**: Decidir explícitamente si se acepta una heurística o se requiere exactitud. Para n≤6, validar con búsqueda exhaustiva. Documentar las garantías (o falta de ellas) en el manual técnico.

---

## R-03: Escalabilidad de la tabla de transiciones de GeoMIP para k>2

**Probabilidad**: Media  
**Impacto**: Alto — la tabla actual crece como O(2^n × 2^n) en pares de estados.

**Descripción**: La `tabla_transiciones` de GeoMIP almacena pares (estado_ini, estado_fin). Para k-particiones se deben evaluar más candidatos, potencialmente multiplicando el espacio de estados por k.

**Mitigación**: Implementar lazy evaluation (calcular solo los pares necesarios). Considerar caching con LRU si la memoria es limitante.

---

## R-04: Duplicación de código entre GeoMIP y QNodes

**Probabilidad**: Certeza (ya existe)  
**Impacto**: Medio — mantenimiento duplicado, posibles divergencias de comportamiento.

**Descripción**: `System`, `NCube`, `Solution`, `Manager` y `SIA` existen casi idénticos en ambos sub-proyectos. Cualquier bug fix o mejora debe aplicarse en dos lugares.

**Mitigación**: Para las extensiones KGeoMIP/KQNodes, evaluar si vale refactorizar a un paquete compartido (`code/shared/` o similar). Si no, mantener la duplicación documentada.

---

## R-05: Ground-truth para k>2 no existe en PyPhi

**Probabilidad**: Certeza  
**Impacto**: Medio — imposible validar correctitud exacta para redes grandes.

**Descripción**: PyPhi solo implementa bipartición (k=2). Para k>2, no hay implementación de referencia oficial.

**Mitigación**: 
- Para n≤6: búsqueda exhaustiva interna como baseline.
- Para n>6: consistencia interna (φ(k+1) ≤ φ(k)) y comparación KGeoMIP vs KQNodes.
- Documentar las limitaciones de validación en el manual técnico.

---

## R-06: Tiempo de ejecución puede ser prohibitivo para n=10, k>2

**Probabilidad**: Media-Alta  
**Impacto**: Alto — puede imposibilitar completar el batch de pruebas en tiempo razonable.

**Descripción**: GeoMIP ya muestra tiempos largos para n=10 con k=2 (timeout de 3600s aplicado). Para k>2 el espacio de búsqueda es mayor.

**Mitigación**: 
- Implementar paralelización con `multiprocessing` o `joblib` para evaluación de candidatos.
- Reducir el conjunto de candidatos a evaluar con estrategias de poda.
- Ejecutar n=10 con k>2 manualmente (no en CI automatizado).

---

## R-07: Inconsistencia entre SIA de GeoMIP y QNodes complica la unificación

**Probabilidad**: Alta (ya existe la inconsistencia)  
**Impacto**: Bajo-Medio — solo afecta si se intenta unificar las interfaces.

**Descripción**: `SIA` en GeoMIP recibe `Manager`; en QNodes recibe `tpm: np.ndarray`. KGeoMIP y KQNodes deben respetar sus respectivas interfaces o rediseñar la jerarquía.

**Mitigación**: Documentar las diferencias claramente (ver `context/.IA/architecture.md`). No intentar unificar sin aprobación explícita del usuario.

---

## R-08: print() statements en código de producción

**Probabilidad**: Certeza (ya existe)  
**Impacto**: Bajo — no afecta correctitud pero genera ruido en output.

**Descripción**: `NCube.condicionar()` tiene `print()` statements temporales que generan output en toda ejecución.

**Mitigación**: Reemplazar por `SafeLogger` antes de cualquier entrega o prueba de rendimiento. Ver líneas 75-79 de `code/GeoMIP/src/models/core/ncube.py`.

---

## R-09: Tests insuficientes en QNodes

**Probabilidad**: Certeza  
**Impacto**: Medio — sin tests, las extensiones no tienen garantía de no regresión.

**Descripción**: El directorio `code/QNodes/tests/` solo tiene `__init__.py`. No hay tests automatizados para ninguna de las estrategias actuales.

**Mitigación**: Escribir tests de regresión para QNodes(k=2) antes de implementar KQNodes. Seguir TDD estrictamente para las extensiones.
