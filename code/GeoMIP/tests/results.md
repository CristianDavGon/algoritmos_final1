# Benchmark Geometric vs PyPhi

Cada sección se actualiza automáticamente al correr `test_geometric_vs_pyphi.py` con la red correspondiente.

---

<!-- BEGIN:N5A -->
## N5A — 5 nodos · 4 pruebas · 2026-05-27 17:04

#### Prueba 1 · Alcance: `ABCDE` · Mecanismo: `ABCDE`

|                | Partición | φ (pérdida) | Tiempo (s) |
|----------------|-----------|-------------|------------|
| **PyPhi**      | ∣ D ∣∣ A,B,C,E ∣ ∣ ∅ ∣∣ a,b,c,d,e ∣ | 0.000000 | 0.010 s |
| **Geometric** | ∣ A,B,C,E ∣∣ D ∣ ∣ a,b,c,d,e ∣∣ ∅ ∣ | 0.000000 | 0.014 s |
| **Match**      | ✓ | ✓ Δφ = 0.000000 | 0.7x speedup |

#### Prueba 2 · Alcance: `ABCDE` · Mecanismo: `ABCD`

|                | Partición | φ (pérdida) | Tiempo (s) |
|----------------|-----------|-------------|------------|
| **PyPhi**      | ∣ D ∣∣ A,B,C,E ∣ ∣ ∅ ∣∣ a,b,c,d ∣ | 0.000000 | 0.016 s |
| **Geometric** | ∣ A,B,C,E ∣∣ D ∣ ∣ a,b,c,d ∣∣ ∅ ∣ | 0.000000 | 0.023 s |
| **Match**      | ✓ | ✓ Δφ = 0.000000 | 0.7x speedup |

#### Prueba 3 · Alcance: `ABCDE` · Mecanismo: `BCDE`

|                | Partición | φ (pérdida) | Tiempo (s) |
|----------------|-----------|-------------|------------|
| **PyPhi**      | ∣ C ∣∣ A,B,D,E ∣ ∣ ∅ ∣∣ b,c,d,e ∣ | 0.000000 | 0.114 s |
| **Geometric** | ∣ A,B,D,E ∣∣ C ∣ ∣ b,c,d,e ∣∣ ∅ ∣ | 0.000000 | 0.256 s |
| **Match**      | ✓ | ✓ Δφ = 0.000000 | 0.5x speedup |

#### Prueba 4 · Alcance: `ABCDE` · Mecanismo: `BCD`

|                | Partición | φ (pérdida) | Tiempo (s) |
|----------------|-----------|-------------|------------|
| **PyPhi**      | ∣ C ∣∣ A,B,D,E ∣ ∣ ∅ ∣∣ b,c,d ∣ | 0.000000 | 1.682 s |
| **Geometric** | ∣ A,B,D,E ∣∣ C ∣ ∣ b,c,d ∣∣ ∅ ∣ | 0.000000 | 2.181 s |
| **Match**      | ✓ | ✓ Δφ = 0.000000 | 0.8x speedup |

### Resumen

| Métrica | Valor |
|---------|-------|
| Exactitud φ | 4/4 (100.0%) |
| Exactitud partición | 4/4 (100.0%) |
| Speedup promedio | 0.66x |
| Δφ promedio | 0.000000 |
| Δφ máximo | 0.000000 |
| Tolerancia φ | 0.0001 |
<!-- END:N5A -->
