# SDD-3 — Implementation Notes: KQNodes

**Fase**: 3
**Estado**: 🔴 Pendiente de implementación
**Referencia principal**: `temp/Diseno_KQNodes_Fase3.md`

---

## 1. Pseudocódigo del algoritmo KQNodes (Criterio C4)

```
ENTRADA: V (conjunto de dimensiones), k (número de partes deseadas),
         oracle f (función submodular simétrica del subsistema)
SALIDA : Π* (k-partición de mínima información greedy), Φ* (pérdida total)

ALGORITMO KQNodes(V, k, f):

  // ── Paso 0: Inicialización ────────────────────────────────────────
  Π ← { V }
  // Calcular el mejor corte de V completo (1 llamada inicial a QNodes)
  (A*, B*), φ_local ← QNodes(V, f|_V)
  PQ ← MinHeap()
  // Clave: φ_local. Desempate: −|P| (mayor tamaño primero), luego índice menor.
  PQ.insertar( clave=(φ_local, −|V|, id(V)), valor=(V, A*, B*) )

  // ── Paso 1: k−1 refinamientos por corte marginal mínimo ──────────
  PARA j = 1 HASTA k−1:

    // 1a. Selección C4: parte con el corte MÁS BARATO
    (φ_sel, _, _), (P_sel, A_sel, B_sel) ← PQ.extraer_min()

    // 1b. Refinamiento de la partición
    Π ← (Π ∖ {P_sel}) ∪ {A_sel, B_sel}

    // 1c. Calcular el mejor corte de cada hijo y encolarlo
    //     (solo si |hijo| ≥ 2; singletons no son partibles)
    SI |A_sel| ≥ 2:
        (Aa, Ab), φ_A ← QNodes(A_sel, f|_{A_sel})   // oracle restringido
        PQ.insertar( clave=(φ_A, −|A_sel|, id(A_sel)), valor=(A_sel, Aa, Ab) )
    SI |B_sel| ≥ 2:
        (Ba, Bb), φ_B ← QNodes(B_sel, f|_{B_sel})
        PQ.insertar( clave=(φ_B, −|B_sel|, id(B_sel)), valor=(B_sel, Ba, Bb) )

    // Salvaguarda: si PQ vacía antes de j=k−1, V no admite k partes no triviales.
    // Devolver la partición más fina alcanzable + aviso en log.

  // ── Paso 2: Pérdida total (UNA sola EMD completa al final) ────────
  Φ* ← EMD( p(s_{t+1}), ⊗_{Pi ∈ Π} p_{Pi} )

  RETORNAR Π, Φ*
FIN ALGORITMO
```

### Variante C1 (para A/B testing)
Idéntico, excepto el paso 1a se reemplaza por:
```
P_sel ← argmax_{Pi ∈ Π} |Pi|   // sin MinHeap; solo lista de partes
```
Con desempate por índice menor si hay empate de tamaño.

---

## 2. Oracle restringido — remapeo de máscaras

Al operar sobre un subconjunto Pi ⊊ V, las máscaras de bits globales (D bits) deben remapearse al espacio local (|Pi| bits).

**Sea** Pi = {g₀ < g₁ < ... < g_{m−1}} (índices globales ordenados, m = |Pi|).

**Remapeo biyectivo:**
```
ρ(gᵣ) = r    (índice global gᵣ → índice local r)

Conversión global → local de una máscara:
    mask_local = 0
    PARA r = 0 HASTA m−1:
        bit_r = (mask_global >> g_r) & 1
        mask_local |= (bit_r << r)

full_mask_local = (1 << m) - 1
```

**Las dimensiones fuera de Pi** se condicionan al estado pivote (igual que QNodes condiciona el complemento en bipartición). Esto garantiza que f|_{Pi} mide la pérdida de partir Pi en el contexto del resto ya separado.

**Preservación de simetría:**
```
f|_{Pi}(A) = f|_{Pi}(Pi ∖ A)  ∀ A ⊆ Pi
```
porque el `min` en el oracle es invariante al intercambio A ↔ Pi ∖ A. Esta simetría es requerida por el MAO de Queyranne.

---

## 3. Caché del oracle por bloque

**Regla**: el caché del oracle se **reinicia** entre llamadas a QNodes sobre distintos bloques.

**Por qué no se puede compartir globalmente**: tras el remapeo de §2, las claves del caché son máscaras **locales** (de |Pi| bits). La misma clave entera (p.ej. `0b0101`) refiere a subconjuntos distintos según el bloque (Pi vs. Pj tienen distintos índices globales). Reutilizar el caché global provocaría **colisiones silenciosas** y resultados incorrectos.

**Implementación recomendada:**
```python
def aplicar_qnodes_sobre_bloque(bloque: set[int], oracle_global) -> tuple[set, set, float]:
    cache_local: dict[int, float] = {}   # caché vacío para este bloque
    oracle_restringido = OracleRestringido(bloque, oracle_global, cache_local)
    return qnodes(bloque, oracle_restringido)
```

**Costo espacial**: O(D²) para el bloque más grande (el MAO toca O(D²) máscaras por llamada). El caché se libera al salir del scope de cada llamada.

---

## 4. Llamadas a oracle() y qnodes() — reglas de reutilización

**Regla dura (no copiar código):** `KQNodes` invoca el oracle() y qnodes() **ya implementados** en `code/QNodes/src/strategies/qnodes.py`. No duplicar el MAO.

**Estructura de clase sugerida:**
```python
class KQNodes(SIA):
    """k-partición submodular por refinamiento iterativo con criterio C4."""

    def aplicar_estrategia(self, k: int) -> Solution:
        ...

    def _qnodes_sobre_bloque(self, bloque: frozenset[int]) -> tuple[frozenset, frozenset, float]:
        """Llama a qnodes() con oracle restringido al bloque. Caché local."""
        ...

    def _calcular_phi_total(self, particion: list[frozenset]) -> float:
        """EMD(p(s_{t+1}), ⊗_{Pi} p_{Pi}). Una sola llamada al final."""
        ...
```

**Llamadas a hacer (no duplicar internamente):**
- `oracle(mask, dims_activos)` — función existente en qnodes.py, invocar con dims remapeados.
- `qnodes(dims, oracle)` — función existente, invocar sobre el subconjunto Pi.
- `emd_efecto(dist_original, dist_reconstruida)` — función existente en `GeoMIP/src/funcs/base.py` o equivalente en QNodes.
- `System.distribucion_marginal(dims)` — para calcular p_{Pi} de cada parte.

---

## 5. Cálculo de Φ* al final

```python
# Construcción de la distribución reconstruida por producto tensorial de k marginales
dist_original = sistema.distribucion_marginal()          # p(s_{t+1}), vector 2^D
dist_reconstruida = marginal(Π[0])
PARA Pi EN Π[1:]:
    dist_reconstruida = tensor_product(dist_reconstruida, marginal(Pi))
# Producto tensorial del proyecto: [a,b] ⊗ [c,d] = [ac, ad, bc, bd] (filas fijas, columnas multiplicadas)

Φ* = emd_efecto(dist_original, dist_reconstruida)
```

Esta es la **única** llamada a EMD durante toda la ejecución de KQNodes. El oracle restringido φ_local solo se usa como proxy de ranking durante la búsqueda, no como valor final de Φ.

---

## 6. Análisis de complejidad (referencia)

| Componente | Costo |
|-----------|-------|
| Llamadas a QNodes | ≤ 2k−1 (C4) ó k−1 (C1) |
| Costo de cada QNodes sobre bloque de tamaño D' | O(D'³) |
| Costo total de búsqueda | O(k·D³) |
| Cálculo final de Φ* | O(k·2^D) — una sola vez |
| Espacio (caché por bloque) | O(D²) pico, O(k·D) estructura |

Cumple la restricción de diseño no negociable O(k·D³) de DB-02.

---

## 7. Resultados a registrar aquí al cerrar la fase

*(Sección vacía — llenar durante implementación)*

| n | k | φ_greedy (C4) | φ* (BruteForce) | gap | acierto exacto |
|---|---|---------------|-----------------|-----|----------------|
| — | — | — | — | — | — |
