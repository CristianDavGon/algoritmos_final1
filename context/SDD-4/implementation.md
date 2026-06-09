# SDD-4 — Implementation Notes: KGeoMIP (E4)

**Fase**: 4
**Estado**: 🔴 Pendiente de implementación
**Referencia principal**: `temp/Diseno_KGeoMIP_Fase4.md`

---

## 1. Pseudocódigo del algoritmo KGeoMIP-E4

```
ENTRADA: V (variables), n, T (tabla de costos YA calculada), k

SALIDA: Π* (k-partición de mínima información aproximada), Φ(Π*)

ALGORITMO KGeoMIP-E4(V, n, T, k):

  // ─── FASE 0: caso base k=1 ──────────────────────────────────────────
  SI k == 1: RETORNAR {V}, 0.0

  // ─── FASE 1: matriz de similitud (una vez, guía global) ─────────────
  // Costo: O(n²·2ⁿ) — dominante; lectura de T
  PARA cada par (Xᵢ, Xⱼ), i ≠ j:
    sim(Xᵢ,Xⱼ) ← Σ_{δ: bit Xⱼ activo en δ} T[Xᵢ][δ]
    sim(Xⱼ,Xᵢ) ← Σ_{δ: bit Xᵢ activo en δ} T[Xⱼ][δ]
    S[Xᵢ][Xⱼ] ← (sim(Xᵢ,Xⱼ) + sim(Xⱼ,Xᵢ)) / 2
  // S[Xᵢ][Xⱼ] alto ⟹ dependencia causal fuerte ⟹ costoso separarlos
  // S[Xᵢ][Xⱼ] ≈ 0 ⟹ cuasi-independientes ⟹ corte barato

  // ─── FASE 2: ancla k=2 = GeoMIP (regresión exacta) ──────────────────
  (P_a, P_b), φ₂ ← GeoMIP_bipartir(V, T)   // candidatos BFS + EMD exacto
  Π ← {P_a, P_b}
  SI k == 2: RETORNAR Π, φ₂

  // ─── FASE 3: refinamiento divisivo por corte marginal mínimo ────────
  // Cola de prioridad por ΔΦ del MEJOR corte de cada parte partible.
  PQ ← MinHeap()
  PARA cada parte P ∈ Π con |P| ≥ 2:
    (Pa, Pb), ΔΦ_P ← MejorCorte(P, T, S)   // S propone, EMD confirma
    PQ.insertar(clave = (ΔΦ_P, bfs_order, |P|, min_idx(P)), valor = (P, Pa, Pb))

  PARA j = 3 HASTA k:
    SI PQ vacía: ROMPER   // V no admite j partes no triviales → aviso en log
    (_, (P_sel, Pa, Pb)) ← PQ.extraer_min()   // min ΔΦ (criterio C4 geométrico)
    Π ← (Π ∖ {P_sel}) ∪ {Pa, Pb}             // refinamiento anidado
    PARA cada hijo H ∈ {Pa, Pb} con |H| ≥ 2:
      (Ha, Hb), ΔΦ_H ← MejorCorte(H, T, S)
      PQ.insertar(clave = (ΔΦ_H, bfs_order, |H|, min_idx(H)), valor = (H, Ha, Hb))

  // ─── FASE 4: pérdida total (UNA EMD completa, k-aria) ───────────────
  // Costo: O(k·2ⁿ) — una sola vez
  PARA cada parte Pₘ ∈ Π:
    p_{Pₘ} ← marginal(Pₘ, TPM)    // columnas: SUMAR; filas descartadas: PROMEDIAR
  p_recon ← p_{P₁} ⊗ p_{P₂} ⊗ … ⊗ p_{Pₖ}   // ⊗ del proyecto (expande columnas)
  Φ* ← EMD(p_original, p_recon)   // MISMA función EMD que GeoMIP en producción

  RETORNAR Π, Φ*

SUBRUTINA MejorCorte(P, T, S):
  // S restringe los candidatos de P a los cortes de baja similitud inter-grupo (baratos)
  // GeoMIP_bipartir confirma evaluando EMD sobre el bloque P.
  candidatos ← cortes_baja_similitud(S|P)  ∪  candidatos_BFS_GeoMIP(P, T)
  (A*, B*) ← argmin_{(A,B) ∈ candidatos} EMD_bloque(A, B, T)
  ΔΦ ← EMD_bloque(A*, B*, T)
  RETORNAR (A*, B*), ΔΦ

FIN ALGORITMO
```

---

## 2. Construcción de la matriz de similitud S desde T

**Definición** (§1.4 del diseño):
```
sim(Xᵢ, Xⱼ) = Σ_{δ: bit Xⱼ activo en δ} T[Xᵢ][δ]

S[Xᵢ][Xⱼ] = (sim(Xᵢ,Xⱼ) + sim(Xⱼ,Xᵢ)) / 2
```

**"Bit Xⱼ activo en δ"**: las claves XOR δ cuyo bit correspondiente a la dimensión Xⱼ está activo (la transición incluye cambio en la dirección de Xⱼ). A Nivel 1 (solo d_H=1), es la única transición δ = (1 << posición_Xⱼ).

**Por qué se simetriza**: `sim(Xᵢ,Xⱼ) ≠ sim(Xⱼ,Xᵢ)` en general (T es simétrica en estados pero no en variables). S promedia ambos sentidos para obtener una afinidad simétrica apta para clustering y grafos.

**Implementación**:
- Iterar sobre todos los pares (i, j) con i < j.
- Para cada par, sumar los valores T[Xᵢ][δ] donde el bit j-ésimo de δ está activo, y simétricamente.
- Almacenar como matriz n×n (o diccionario {(i,j): valor}).
- Calcular una sola vez por sistema; reutilizar para todos los k.

**Valores extremos y su interpretación**:
- S[Xᵢ][Xⱼ] ≈ 0 ⟹ Xᵢ, Xⱼ son causalmente (cuasi-)independientes ⟹ separarlos es barato.
- S[Xᵢ][Xⱼ] alto ⟹ dependencia causal fuerte ⟹ separarlos es caro.

---

## 3. Anclaje de k=2 en GeoMIP (Fase 2 del pseudocódigo)

El primer corte de E4 **es** GeoMIP exacto, no una aproximación:

```python
# Fase 2: llamada directa a la maquinaria existente de GeoMIP
(P_a, P_b), phi_2 = geomip_bipartir(V, T)
# geomip_bipartir = GeometricSIA._identificar_biparticion_optima()
# Misma T, mismos candidatos BFS (Heurística 1 + 2), misma EMD
# Garantía: KGeoMIP(k=2) ≡ GeoMIP por construcción
if k == 2:
    return {P_a, P_b}, phi_2
```

**Regla de reutilización**: no duplicar la lógica de GeoMIP. Invocar el método existente sobre V completo con su tabla T.

---

## 4. Criterio de corte marginal mínimo con cola de prioridad (Fase 3)

La cola de prioridad gestiona las partes partibles ordenadas por su ΔΦ (el costo del mejor corte disponible):

```python
# Clave de prioridad: tupla para desempate determinístico (D4-03)
clave = (delta_phi, bfs_order, len(P), min(P))
# bfs_order: posición en el orden de candidatos BFS de GeoMIP
# menor clave ⟹ corte más barato ⟹ se extrae primero

PQ = []  # heapq de Python (min-heap nativo)
heapq.heappush(PQ, (clave, (P, Pa, Pb)))

# En cada iteración:
clave, (P_sel, Pa, Pb) = heapq.heappop(PQ)
```

**Invariante**: en cada paso j, se extrae la parte cuyo mejor corte tiene el menor ΔΦ disponible. Al añadir los hijos, se pre-calculan sus mejores cortes antes de insertarlos.

---

## 5. Subrutina MejorCorte: S propone, EMD confirma

```python
def mejor_corte(P: frozenset, T, S) -> tuple[frozenset, frozenset, float]:
    # 1. S propone los cortes candidatos de baja similitud inter-grupo
    candidatos_s = cortes_baja_similitud(S, P)   # biparticiones de P con
                                                  # mínima suma de S inter-grupo
    # 2. Candidatos BFS de GeoMIP como red de seguridad
    candidatos_bfs = candidatos_bfs_geomip(P, T)
    
    # 3. Union de candidatos (S puede no proponer el óptimo si proxy falla)
    candidatos = candidatos_s | candidatos_bfs
    
    # 4. EMD confirma: elegir el que minimiza ΔΦ real
    mejor = None
    mejor_delta = float('inf')
    for (A, B) in candidatos:
        delta = emd_bloque(A, B, T)   # EMD sobre el bloque P con vista de T
        if delta < mejor_delta:
            mejor_delta = delta
            mejor = (A, B)
    
    return mejor[0], mejor[1], mejor_delta
```

**Nota**: `candidatos_bfs_geomip(P, T)` invoca la **maquinaria BFS existente de GeoMIP** sobre el subconjunto P. No duplicar: usar el método interno de `GeometricSIA` con vista local de T.

---

## 6. Marginalización correcta

**Reglas críticas** (§1.2 del diseño; errores aquí son la causa más común de fallos en EMD):

| Operación | Regla | Por qué |
|-----------|-------|---------|
| Columnas fuera de Pₘ | **SUMAR** | Son eventos mutuamente excluyentes sobre los estados del sistema completo |
| Filas de variables descartadas | **PROMEDIAR** | Equiprobabilidad sobre los estados iniciales de las variables no en Pₘ |
| Normalización | **NO normalizar** | La suma ya está implícita en la estructura del ⊗ del proyecto |
| Producto tensorial ⊗ | **Expande solo columnas** | ⊗ del proyecto ≠ Kronecker; [a,b]⊗[c,d] = [ac,ad,bc,bd], filas invariantes |

**Consistencia con GeoMIP k=2**: para k=2, la marginalización de Pₘ = {variables de una parte} debe producir el mismo resultado que `System.distribucion_marginal(dims_de_la_parte)` que ya usa GeoMIP. Verificar antes de implementar.

---

## 7. Estrategia A (baseline de comparación A/B)

La Estrategia A es el **clustering jerárquico aglomerativo** sobre S (dendrograma por enlace promedio, corte en k):

```
sim_cluster(Ca, Cb) = (1 / |Ca|·|Cb|) · Σ_{Xᵢ∈Ca, Xⱼ∈Cb} S[Xᵢ][Xⱼ]

Dendrograma: aglomerativo por enlace promedio sobre S
Resultado: cortar el dendrograma en k grupos
```

**Implementación recomendada**: `scipy.cluster.hierarchy.linkage(S_distancia, method='average')` donde `S_distancia = max(S) - S` (convertir similitud en distancia).

**Propósito**: línea base para la comparación A/B (criterio C6). No es la respuesta final porque no garantiza regresión k=2 ni monotonicidad anidada.

---

## 8. Llamadas a la maquinaria existente de GeoMIP — reglas de reutilización

**Regla dura (no copiar código):** `KGeoMIP` invoca la maquinaria existente de GeoMIP. No duplicar:

| Qué necesita KGeoMIP | Qué invocar (NO duplicar) |
|---------------------|--------------------------|
| Bipartición de V (Fase 2) | `GeometricSIA.aplicar_estrategia(k=2)` o su método interno de bipartición |
| Candidatos BFS sobre bloque P | Método BFS interno de `GeometricSIA` sobre subconjunto P con vista de T |
| EMD final (Fase 4) | `emd_efecto(...)` de `GeoMIP/src/funcs/base.py` — **la misma que usa GeoMIP** |
| Distribución marginal de Pₘ | `System.distribucion_marginal(dims)` existente |

**Estructura de clase sugerida** (coherente con DEC-02: KGeoMIP recibe Manager):
```python
class KGeoMIP(SIA):
    """k-partición geométrica por refinamiento divisivo E4."""

    def __init__(self, gestor: Manager):
        ...

    def aplicar_estrategia(self, k: int) -> Solution:
        ...

    def _construir_S(self) -> np.ndarray:
        """Matriz de similitud n×n desde T. Una sola vez por sistema."""
        ...

    def _mejor_corte(self, P: frozenset, S: np.ndarray) -> tuple[frozenset, frozenset, float]:
        """S propone, EMD confirma. Llama a maquinaria BFS de GeoMIP sobre P."""
        ...

    def _calcular_phi_total(self, particion: list[frozenset]) -> float:
        """EMD(p(s_{t+1}), ⊗_{Pₘ} p_{Pₘ}). Una sola vez al final."""
        ...
```

---

## 9. Análisis de complejidad (referencia)

| Componente | Costo |
|-----------|-------|
| Construcción de T (ya existente) | O(n·2ⁿ) — una sola vez por sistema |
| Construcción de S desde T | O(n²·2ⁿ) — **término dominante** |
| Refinamiento divisivo (Fases 2+3) | O(k·D³) — ≤ 2k−1 llamadas a GeoMIP_bipartir sobre bloques |
| Evaluación final de Φ* | O(k·2ⁿ) — una sola vez |
| **Total KGeoMIP** | **O(n²·2ⁿ)** |

**Comparación con fuerza bruta** (n=10, k=3):
- KGeoMIP: n²·2ⁿ = 100·1024 ≈ 1.0×10⁵
- BruteForce: S(10,3)·EMD ≈ 9330·1024 ≈ 9.6×10⁶
- Ratio: ~96× más rápido (y crece sin cota con n)
