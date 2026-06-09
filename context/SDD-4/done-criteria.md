# SDD-4 — Done Criteria: Extensión KGeoMIP (k-particiones geométrica)

**Fase**: 4
**Estado**: 🔴 PENDIENTE

---

## Criterios de aceptación

| ID | Criterio | Estado | Evidencia esperada |
|----|----------|--------|-------------------|
| C1 | **Regresión k=2**: KGeoMIP(k=2) == GeoMIP para n ∈ {5,8,10}, tolerancia 1e-9 | 🔴 | Misma partición y mismo φ — E4 delega en GeoMIP exacto en Fase 2 del pseudocódigo |
| C2 | **Monotonicidad correcta**: φ(k+1) ≥ φ(k) para k ∈ {2,3,4} (con tolerancia ε) | 🔴 | `assert Φ(k+1) ≥ Φ(k) − ε` — dirección **≥**, NOT ≤; gratuita por anidación en E4 |
| C3 | **Gap de optimalidad k=3**: φ_E4 − φ* ≥ 0 medido contra BruteForce para n ≤ 6 | 🔴 | gap ≥ 0 verificado; reportar distribución del gap y tasa de acierto exacto |
| C4 | **Gap de optimalidad k=4**: ídem para k=4, n ≤ 6 | 🔴 | ídem; no exigir igualdad exacta — E4 es greedy, no óptimo global |
| C5 | **Tasa de acierto exacto** reportada para k ∈ {3,4}: % de casos con gap = 0 | 🔴 | Medido sobre el mismo conjunto de sistemas de C3/C4 |
| C6 | **A/B testing E4 vs Estrategia A**: gap medio y % acierto comparados para k ∈ {3,4} | 🔴 | Estrategia A = clustering jerárquico aglomerativo sobre S; comparar en n ≤ 6 |
| C7 | **CSV de resultados**: k ∈ {2,3,4,5}, n ∈ {5,8,10} generados y coherentes | 🔴 | Script batch; formato estándar del proyecto |
| C8 | **Cobertura ≥ 85%** en módulo `kgeomip.py` | 🔴 | Todas las rutas públicas y ramas principales cubiertas |
| C9 | **Tipado completo**: mypy sin errores críticos en módulo KGeoMIP | 🔴 | Limpio en kgeomip.py; errores pre-existentes en módulos externos no aplican |
| C10 | **Docstrings** en todos los métodos públicos de KGeoMIP | 🔴 | Google/NumPy docstrings en todos los métodos públicos |
| C11 | **Consistencia de función EMD**: KGeoMIP usa la misma función EMD que GeoMIP en producción | 🔴 | Verificar explícitamente antes de validar regresión; documentar hallazgo en D4-04 |
| C12 | **T y S una sola vez**: T no se recalcula entre k-valores; S no se recalcula entre cortes | 🔴 | Verificable por inspección de código; T y S se construyen una sola vez por sistema |

---

## Notas críticas sobre los criterios

### C1 — Regresión k=2
La tolerancia 1e-9 es apropiada porque con k=2 E4 **es exactamente** GeoMIP: la Fase 2 del pseudocódigo llama directamente a `GeoMIP_bipartir(V, T)` y retorna sin ejecutar ninguna fase posterior. Misma T, mismos candidatos BFS (Heurística 1 + 2), misma EMD. No hay fuente de divergencia legítima. Si este test falla, el bug más probable es C11 (función EMD distinta a la de GeoMIP).

### C2 — Monotonicidad
La dirección **φ(k+1) ≥ φ(k)** es la correcta (§1.5 del diseño, DEC-13 corregido, DB-03 corregido). Más partes ⟹ reconstrucción más factorizada ⟹ mayor distancia EMD al original. Esta propiedad es **gratuita por construcción** en E4: cada refinamiento añade un corte con ΔΦ ≥ 0; la suma acumulada es no decreciente. Si el test falla, indica un bug en el cálculo de EMD, la marginalización, o la lógica del refinamiento — **no** una propiedad matemática violada.

### C3/C4 — Gap para k≥3
**No** exigir |ΔΦ| < 1e-9 contra BruteForce para k≥3. E4 es greedy divisivo y no garantiza optimalidad global para k≥3 (miopía inherente al refinamiento secuencial). Lo correcto:
- `gap = φ_E4 − φ* ≥ 0` (siempre no negativo porque φ* es el mínimo global)
- Reportar distribución del gap, tasa de acierto exacto (gap = 0), y opcionalmente Jaccard entre la partición de E4 y la óptima

### C6 — A/B testing E4 vs Estrategia A
Ejecutar tanto E4 (recomendada) como Estrategia A (clustering jerárquico aglomerativo sobre S, baseline) sobre el mismo conjunto de test (n ≤ 6, k ∈ {3,4}). Conjetura verificable: E[φ_E4] ≤ E[φ_A] con módulos solapados; empate con módulos nítidos (complementariedad exacta). La comparación es requerida por la rúbrica como "evidencia de análisis de trade-offs entre variantes". Ver D4-01 para la justificación de E4 sobre Estrategia A.

### C11 — Función EMD (caveat de implementación crítico)
Verificar antes de validar C1 que KGeoMIP llama a **la misma función EMD que GeoMIP usa en producción**. Si GeoMIP usa `emd_efecto` con `pyemd` (matriz de costo de Hamming) y KGeoMIP usa `scipy.stats.wasserstein_distance` (Wasserstein 1-D sobre índices — **que NO es la EMD con métrica de Hamming**), la regresión k=2 fallará numéricamente aunque la lógica sea correcta. Ver D4-04 para la decisión de resolución.

---

## Identificación del k natural — codo de ΔΦ (corrección conceptual)

El k natural del sistema **no** es el `argmin_k Φ(k)`. Ese criterio es **degenerado**: Φ es monótona creciente en k, por lo que el argmin es siempre k=2 (o k=1 con Φ=0). No tiene información sobre la estructura del sistema.

**Criterio correcto — salto de cohesión:**

```
ΔΦ(k) = Φ(k) − Φ(k−1)   (incremento marginal del k-ésimo corte)

k* = argmax_k [ ΔΦ(k+1) − ΔΦ(k) ]   (mayor salto en el costo marginal)
```

El k natural es el mayor k tal que todos los cortes hasta k son "baratos" (ΔΦ pequeño) y el siguiente corte es "caro" (ΔΦ grande). Es el **codo** de la curva de incrementos.

E4 produce la familia anidada completa {Φ(2), Φ(3), Φ(4), Φ(5)} en una sola corrida; la curva ΔΦ queda disponible gratis para diagnosticar k* y reportar en los resultados experimentales.

---

## Aprobación de salida

- [ ] Todos los criterios C1–C12 verificados.
- [ ] `context/state/active-tasks.md` con todas las tareas marcadas COMPLETADA.
- [ ] `context/handoffs/04.md` creado con resumen de cierre.
- [ ] `context/state/current-phase.md` actualizado a Fase 5.
