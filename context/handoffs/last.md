# Handoff — Estado actual del proyecto

> Actualizar este archivo al terminar cada sesión de trabajo.
> Fecha última actualización: 2026-05-18

---

## Fase activa

**Fase 0 — Base funcional del sistema** (completada ✓) → pasando a **Fase 1**

---

## Lo que está hecho

- [x] Arquitectura de QNodes y GeoMIP explorada y documentada en [context/instructions.md](/context/instructions.md).
- [x] `QNodes/src/main.py` corregido: import roto (`qnodes` → `q_nodes`) + nueva función `ejecutar_desde_excel` que lee `DatosPruebas2026_1.xlsx` (cols B y C) y escribe CSV en `QNodes/results/resultados_N8A.csv`.
- [x] `GeoMIP/src/main.py` corregido: `GEOMIP_ROOT` bug (`parents[3]` → `parents[1]`), salida cambiada de Excel a CSV en `GeoMIP/results/resultados_N8A.csv`, lee desde `DatosPruebas2026_1.xlsx`.
- [x] QNodes verificado: φ=0.5 para prueba 1 (ABCDEFGH|ABCDEFGH sobre N8A). Algoritmo corre sin errores.
- [ ] GeoMIP no se ejecutó completamente (usa `multiprocessing`, requiere prueba manual desde terminal).

---

## Lo que viene (próximo paso concreto)

**Fase 1 — KQNodes:**
1. Crear `QNodes/src/strategies/kqnodes.py` — extensión del algoritmo Queyranne para k grupos.
   - El método recibe `(tpm, k)` y retorna `(particion_optima, phi_min)`.
   - Para k=2 debe coincidir con `q_nodes.py`.
2. Crear `QNodes/kexec.py` — punto de entrada que itera k ∈ {2,3,4,5} y guarda un CSV por k.
3. Validar k=2 contra `q_nodes.py` en `N5A.csv`.

---

## Decisiones de diseño ya tomadas

| Decisión | Detalle |
|----------|---------|
| Dónde viven las nuevas estrategias | Dentro de los módulos existentes: `QNodes/src/strategies/kqnodes.py` y `GeoMIP/src/strategies/kgeomip.py`. **No** se crean directorios nuevos `/KQNodes/` ni `/KGeoMIP/`. |
| Punto de entrada para k-particiones | `QNodes/kexec.py` y `GeoMIP/kexec.py` (separado del `exec.py` original). |
| Formato de resultados | CSV por cada k: `QNodes/results/resultados_N{i}A_k{k}.csv` y `GeoMIP/results/resultados_N{i}A_k{k}.csv`. |
| Valores de k | Solo `k ∈ {2, 3, 4, 5}`. Para k=2 el resultado debe coincidir con el algoritmo base. |
| Red de prueba canónica | N=8 via `DatosPruebas2026_1.xlsx`. Redes de desarrollo: N5A (rápida), N8A (canónica). |
| LOC por archivo | Máximo 300 líneas — respetar siempre. |
| Excel canónico | `DatosPruebas2026_1.xlsx` hoja `8A-Elementos` (sheet_idx=2), `skiprows=5`, cols B=Alcance, C=Mecanismo. |

---

## Arquitectura de QNodes (base para KQNodes)

```
QNodes/
├── exec.py                          # Punto de entrada actual (bipartición)
├── src/
│   ├── controllers/manager.py       # Carga TPM desde src/.samples/N{n}A.csv
│   ├── funcs/
│   │   ├── force.py
│   │   ├── format.py                # fmt_biparticion_q
│   │   └── iit.py                   # emd_efecto, ABECEDARY, labels
│   ├── models/
│   │   ├── base/sia.py              # SIA(tpm: np.ndarray) — clase base abstracta
│   │   ├── base/application.py      # Singleton config (pagina_red_muestra, etc.)
│   │   ├── core/system.py           # System — condicionar, substraer, bipartir
│   │   ├── core/solution.py         # Solution — perdida, particion, tiempo_ejecucion
│   │   └── core/ncube.py
│   └── strategies/
│       ├── q_nodes.py               # QNodes(tpm) — ESTRATEGIA ACTIVA (Queyranne MAO)
│       └── qnodes.py                # Versión refactorizada — usa src.iit.* (NO FUNCIONA aún)
│           # KQNodes irá aquí → kqnodes.py
└── src/main.py                      # ejecutar_desde_excel + iniciar()
```

**Flujo QNodes:**
1. `exec.py` → `iniciar()` en `main.py`
2. `main.py` lee pruebas de `DatosPruebas2026_1.xlsx` (sheet=2, skiprows=5)
3. Por cada prueba: `QNodes(tpm).aplicar_estrategia(estado, cond, alcance, mecanismo)`
4. `q_nodes.py` → `sia_preparar_subsistema` → `algorithm(vertices)` → `funcion_submodular`
5. `funcion_submodular` llama `sia_subsistema.bipartir(...)` + `emd_efecto(...)`
6. Retorna `Solution(perdida, particion, tiempo_ejecucion)`

**Función clave a extender:** `algorithm(vertices)` en `q_nodes.py` — actualmente busca bipartición. Para KQNodes se extiende para k grupos.

---

## Arquitectura de GeoMIP (base para KGeoMIP)

```
GeoMIP/
├── exec.py                          # Punto de entrada
├── src/
│   ├── controllers/
│   │   ├── manager.py               # SIA(gestor: Manager) — resuelve TPM automáticamente
│   │   └── strategies/
│   │       └── geometric.py         # GeometricSIA — ESTRATEGIA ACTIVA
│   ├── funcs/
│   │   ├── base.py                  # emd_efecto, hamming_distance, ABECEDARY
│   │   ├── format.py                # fmt_biparte_q
│   │   └── system.py
│   ├── models/base/sia.py           # SIA(gestor: Manager) — diferente de QNodes
│   └── data/samples/N8A.csv        # TPM canónica N=8
└── src/main.py                      # ejecutar_desde_excel + iniciar()
```

**Diferencias clave GeoMIP vs QNodes:**
- SIA en GeoMIP recibe `Manager` (no TPM directa).
- Algoritmo geométrico: niveles de distancia Hamming vs Queyranne MAO.
- Usa `multiprocessing.Process` con timeout de 1h por prueba.
- Samples en `GeoMIP/data/samples/` (no `src/.samples/`).

---

## Datos y archivos clave

| Archivo | Propósito |
|---------|-----------|
| `data/DatosPruebas2026_1.xlsx` | Dataset canónico — N=8 sheet_idx=2, skiprows=5, cols B+C |
| `QNodes/src/.samples/N5A.csv` | Red pequeña para desarrollo rápido |
| `QNodes/src/.samples/N8A.csv` | Red canónica QNodes |
| `GeoMIP/data/samples/N8A.csv` | Red canónica GeoMIP |

---

## Contexto del entorno

- Python 3.12 con gestor `uv`
- Ejecución: `cd QNodes && uv run exec.py`
- OS de desarrollo: Windows 10 (PowerShell). Producción en Linux (Ubuntu).
- Dependencias clave: `numpy`, `pandas`, `colorama`, `pyttsx3`, `pyinstrument`
- **Nota:** `pyttsx3` puede causar error al imprimir `Solution` en terminal Windows (Unicode cp1252). El CSV se guarda correctamente con UTF-8.

---

## Referencias

- Hoja de ruta completa: [context/sdd-2.md](/context/sdd-2.md)
- Criterios manuales técnico: [context/tecnico.md](/context/tecnico.md)
- Criterios manual usuario: [context/usuario.md](/context/usuario.md)
- Criterios de calidad globales: [context/criterios.md](/context/criterios.md)
