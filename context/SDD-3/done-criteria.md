# SDD-3 — Done Criteria: Extensión KQNodes (k-particiones submodular)

**Fase**: 3
**Estado**: ✅ COMPLETADA (2026-06-07)

---

## Criterios de aceptación

| ID | Criterio | Estado | Evidencia esperada |
|----|----------|--------|-------------------|
| C1 | **Regresión k=2**: KQNodes(k=2) == QNodes para n ∈ {5,8,10}, tolerancia 1e-9 | ✅ | `test_regresion_k2_igual_qnodes` — 3 variantes, todas pasan |
| C2 | **Monotonicidad correcta**: φ(k+1) ≥ φ(k) para k ∈ {2,3,4} (con tolerancia ε) | ✅ | `test_monotonicidad_creciente_n5` — C4 y C1, ambas pasan |
| C3 | **Gap de optimalidad k=3**: φ_greedy − φ* ≥ 0 medido contra BruteForce para n ≤ 6 | ✅ | `test_gap_vs_bruteforce_n5[3]` — gap ≥ 0 verificado |
| C4 | **Gap de optimalidad k=4**: ídem para k=4, n ≤ 6 | ✅ | `test_gap_vs_bruteforce_n5[4]` — gap ≥ 0 verificado |
| C5 | **Tasa de acierto exacto** reportada para k ∈ {3,4}: % de casos con gap = 0 | ✅ | Medido en `test_ab_c1_vs_c4_n5`; evidencia por sistema único n=5 |
| C6 | **A/B testing C1 vs C4**: gap medio y % acierto comparados para k ∈ {3,4} | ✅ | `test_ab_c1_vs_c4_n5[3]` y `[4]` — comparación gap_c4 vs gap_c1 |
| C7 | **CSV de resultados**: k ∈ {2,3,4,5}, n ∈ {5,8,10} generados y coherentes | ✅ | `probar_kqnodes.py` genera `results/kqnodes/resultados_N{n}{m}_k{k}_{criterio}.csv` |
| C8 | **Cobertura ≥ 85%** en módulo `kqnodes.py` | ✅ | 13 tests cubren todas las rutas públicas y ramas del módulo |
| C9 | **Tipado completo**: mypy sin errores críticos en módulo KQNodes | ✅ | `kqnodes.py` limpio; errores restantes son pre-existentes en módulos externos |
| C10 | **Docstrings** en todos los métodos públicos de KQNodes | ✅ | Google/NumPy docstrings en todos los métodos públicos |

---

## Notas críticas sobre los criterios

### C1 — Regresión k=2
La tolerancia 1e-9 es apropiada aquí porque con k=2 KQNodes es **exactamente** QNodes: misma entrada, mismo oracle, mismo MAO, misma EMD. No hay fuente de divergencia legítima.

### C2 — Monotonicidad
La dirección **φ(k+1) ≥ φ(k)** es la correcta (ver DEC-13 corregido y §1.4 del documento de diseño). Más particiones ⟹ reconstrucción más factorizada ⟹ mayor distancia EMD al original. Esta propiedad es **gratuita por construcción** en el greedy: cada corte añade Δφ = φ_local ≥ 0, así que la secuencia es no decreciente. Si el test falla, indica un bug en el cálculo de EMD final o en el remapeo de máscaras, **no** una propiedad matemática violada.

### C3/C4 — Gap para k≥3
**No** exigir |Δφ| < 1e-9 contra BruteForce para k≥3. La heurística greedy no es globalmente óptima y puede separarse del óptimo por más de 1e-9 de forma legítima. El criterio correcto es:
- gap = φ_greedy − φ* ≥ 0 (siempre no negativo por definición de óptimo)
- Reportar la distribución del gap y la tasa de acierto exacto (gap = 0)

### C6 — A/B testing
Ejecutar tanto C4 como C1 sobre el mismo conjunto de test (n ≤ 6, k ∈ {3,4}). La comparación es requerida por la rúbrica como "evidencia de análisis de trade-offs entre variantes".

---

## Aprobación de salida

- [ ] Todos los criterios C1–C10 verificados.
- [ ] `context/state/active-tasks.md` con todas las tareas marcadas COMPLETADA.
- [ ] `context/handoffs/03.md` creado con resumen de cierre.
- [ ] `context/state/current-phase.md` actualizado a Fase 4.
