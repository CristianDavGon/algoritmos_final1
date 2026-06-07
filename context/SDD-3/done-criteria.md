# SDD-3 — Done Criteria: Extensión KQNodes (k-particiones submodular)

**Fase**: 3
**Estado**: 🔴 PENDIENTE

---

## Criterios de aceptación

| ID | Criterio | Estado | Evidencia esperada |
|----|----------|--------|-------------------|
| C1 | **Regresión k=2**: KQNodes(k=2) == QNodes para n ∈ {5,8,10}, tolerancia 1e-9 | 🔴 | Test en `code/QNodes/tests/test_kqnodes_regression.py` — misma partición, mismo φ |
| C2 | **Monotonicidad correcta**: φ(k+1) ≥ φ(k) para k ∈ {2,3,4} (con tolerancia ε) | 🔴 | Assert en tests: `phi[k+1] >= phi[k] - 1e-9`. **No** `≤`. |
| C3 | **Gap de optimalidad k=3**: φ_greedy − φ* ≥ 0 medido contra BruteForce para n ≤ 6 | 🔴 | CSV con columnas: n, k, phi_greedy, phi_optimo, gap, exacto (bool) |
| C4 | **Gap de optimalidad k=4**: ídem para k=4, n ≤ 6 | 🔴 | Misma estructura CSV |
| C5 | **Tasa de acierto exacto** reportada para k ∈ {3,4}: % de casos con gap = 0 | 🔴 | Tabla resumen en `context/SDD-3/implementation.md` al cerrar |
| C6 | **A/B testing C1 vs C4**: gap medio y % acierto comparados para k ∈ {3,4} | 🔴 | CSV o tabla comparativa — evidencia experimental para rúbrica |
| C7 | **CSV de resultados**: k ∈ {2,3,4,5}, n ∈ {5,8,10} generados y coherentes | 🔴 | En `code/QNodes/results/kqnodes_*.csv` |
| C8 | **Cobertura ≥ 85%** en módulo `kqnodes.py` | 🔴 | Reporte pytest-cov |
| C9 | **Tipado completo**: mypy sin errores críticos en módulo KQNodes | 🔴 | Output de `mypy code/QNodes/src/strategies/kqnodes.py` |
| C10 | **Docstrings** en todos los métodos públicos de KQNodes | 🔴 | Revisión manual |

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
