# Benchmark QNodes vs PyPhi

Cada sección se actualiza automáticamente al correr `test_qnodes_vs_pyphi.py` con la red correspondiente.

---

<!-- BEGIN:N10A -->
## N10A — 10 nodos · 10 pruebas · 2026-05-27 14:55

#### Prueba 1 · Alcance: `ABCDEFGHIJ` · Mecanismo: `ABCDEFGHIJ`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ I ⎞⎛ A,B,C,D,E,F,G,H,J ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i,j ⎠ | 0.472656 | 191.082 s |
| **QNodes** | ⎛ I ⎞⎛ A,B,C,D,E,F,G,H,J ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i,j ⎠ | 0.480469 | 1.271 s |
| **Match**  | ✓ | ✗ Δφ = 0.007813 | 150.3x speedup |

#### Prueba 2 · Alcance: `ABCDEFGHIJ` · Mecanismo: `ABCDEFGHI`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I,J ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i ⎠ | 0.004883 | 93.716 s |
| **QNodes** | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I,J ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i ⎠ | 0.005859 | 0.771 s |
| **Match**  | ✓ | ✗ Δφ = 0.000976 | 121.5x speedup |

#### Prueba 3 · Alcance: `ABCDEFGHIJ` · Mecanismo: `BCDEFGHIJ`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I,J ⎞ ⎝ ∅ ⎠⎝ b,c,d,e,f,g,h,i,j ⎠ | 0.004883 | 103.433 s |
| **QNodes** | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I,J ⎞ ⎝ ∅ ⎠⎝ b,c,d,e,f,g,h,i,j ⎠ | 0.006836 | 0.765 s |
| **Match**  | ✓ | ✗ Δφ = 0.001953 | 135.2x speedup |

#### Prueba 4 · Alcance: `ABCDEFGHIJ` · Mecanismo: `BCDEFGHI`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ B ⎞⎛ A,C,D,E,F,G,H,I,J ⎞ ⎝ ∅ ⎠⎝ b,c,d,e,f,g,h,i ⎠ | 0.011719 | 50.964 s |
| **QNodes** | ⎛ H ⎞⎛ A,B,C,D,E,F,G,I,J ⎞ ⎝ ∅ ⎠⎝ b,c,d,e,f,g,h,i ⎠ | 0.011719 | 0.578 s |
| **Match**  | ✗ | ✓ Δφ = 0.000000 | 88.2x speedup |

#### Prueba 5 · Alcance: `ABCDEFGHIJ` · Mecanismo: `ABDEGHJ`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ J ⎞⎛ A,B,C,D,E,F,G,H,I ⎞ ⎝ ∅ ⎠⎝ a,b,d,e,g,h,j ⎠ | 0.005859 | 26.277 s |
| **QNodes** | ⎛ J ⎞⎛ A,B,C,D,E,F,G,H,I ⎞ ⎝ ∅ ⎠⎝ a,b,d,e,g,h,j ⎠ | 0.019531 | 0.469 s |
| **Match**  | ✓ | ✗ Δφ = 0.013672 | 56.0x speedup |

#### Prueba 6 · Alcance: `ABCDEFGHIJ` · Mecanismo: `ACEGI`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ E ⎞⎛ A,B,C,D,F,G,H,I,J ⎞ ⎝ ∅ ⎠⎝ a,c,e,g,i ⎠ | 0.015625 | 5.990 s |
| **QNodes** | ⎛ E ⎞⎛ A,B,C,D,F,G,H,I,J ⎞ ⎝ ∅ ⎠⎝ a,c,e,g,i ⎠ | 0.024414 | 0.357 s |
| **Match**  | ✓ | ✗ Δφ = 0.008789 | 16.8x speedup |

#### Prueba 7 · Alcance: `ABCDEFGHIJ` · Mecanismo: `BDFHJ`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ I ⎞⎛ A,B,C,D,E,F,G,H,J ⎞ ⎝ ∅ ⎠⎝ b,d,f,h,j ⎠ | 0.003906 | 6.191 s |
| **QNodes** | ⎛ I ⎞⎛ A,B,C,D,E,F,G,H,J ⎞ ⎝ ∅ ⎠⎝ b,d,f,h,j ⎠ | 0.011719 | 0.343 s |
| **Match**  | ✓ | ✗ Δφ = 0.007813 | 18.1x speedup |

#### Prueba 8 · Alcance: `ABCDEFGHI` · Mecanismo: `ABCDEFGHIJ`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ I ⎞⎛ A,B,C,D,E,F,G,H ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i,j ⎠ | 0.472656 | 97.557 s |
| **QNodes** | ⎛ I ⎞⎛ A,B,C,D,E,F,G,H ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i,j ⎠ | 0.480469 | 0.975 s |
| **Match**  | ✓ | ✗ Δφ = 0.007813 | 100.1x speedup |

#### Prueba 9 · Alcance: `ABCDEFGHI` · Mecanismo: `ABCDEFGHI`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i ⎠ | 0.004883 | 49.791 s |
| **QNodes** | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I ⎞ ⎝ ∅ ⎠⎝ a,b,c,d,e,f,g,h,i ⎠ | 0.019531 | 0.754 s |
| **Match**  | ✓ | ✗ Δφ = 0.014648 | 66.0x speedup |

#### Prueba 10 · Alcance: `ABCDEFGHI` · Mecanismo: `BCDEFGHIJ`

|            | Partición | φ (pérdida) | Tiempo (s) |
|------------|-----------|-------------|------------|
| **PyPhi**  | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I ⎞ ⎝ ∅ ⎠⎝ b,c,d,e,f,g,h,i,j ⎠ | 0.004883 | 47.733 s |
| **QNodes** | ⎛ G ⎞⎛ A,B,C,D,E,F,H,I ⎞ ⎝ ∅ ⎠⎝ b,c,d,e,f,g,h,i,j ⎠ | 0.006836 | 0.576 s |
| **Match**  | ✓ | ✗ Δφ = 0.001953 | 82.9x speedup |

### Resumen

| Métrica | Valor |
|---------|-------|
| Exactitud φ | 1/10 (10.0%) |
| Exactitud partición | 9/10 (90.0%) |
| Speedup promedio | 83.51x |
| Δφ promedio | 0.006543 |
| Δφ máximo | 0.014648 |
| Tolerancia φ | 0.0001 |
<!-- END:N10A -->
