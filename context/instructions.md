# Contexto de desarrollo

> Este archivo acumula notas técnicas descubiertas durante el desarrollo. Actualizarlo cada sesión.

---

## Diferencias estructurales: QNodes vs GeoMIP

### Punto de entrada

| Aspecto | QNodes | GeoMIP |
|---------|--------|--------|
| Entry point | `QNodes/exec.py` → `src/main.py` | `GeoMIP/exec.py` → `src/main.py` |
| Estrategia principal | `src/strategies/q_nodes.py` (QNodes) | `src/controllers/strategies/geometric.py` (GeometricSIA) |
| Clase base estrategia | `src/models/base/sia.py` — `SIA(tpm: np.ndarray)` | `src/models/base/sia.py` — `SIA(gestor: Manager)` |

> **Diferencia clave en SIA:** QNodes recibe directamente la TPM como ndarray; GeoMIP recibe un `Manager` que encapsula estado_inicial + ruta al CSV.

---

### Algoritmo

| Aspecto | QNodes (`q_nodes.py`) | GeoMIP (`geometric.py`) |
|---------|-----------------------|-------------------------|
| Nombre | Queyranne submodular | GeométricoTopológico |
| Complejidad base | O(D³·N) | O(2^(m+n)) candidatos |
| Métrica de corte | EMD efecto (suma ∣u−v∣) | EMD efecto (suma ∣u−v∣) |
| Cómo genera candidatos | Maximum Adjacency Ordering (MAO) sobre vértices (t₀, t₁) | Recorre niveles de distancia Hamming desde estado_inicial → estado_final |
| Memoización | `memoria_delta` + `memoria_grupo_candidato` | `tabla_transiciones` (costo de transición por nivel Hamming) |
| Representación de partición | Tuplas `(tiempo, índice)` — vértices bipartitos | Mismas tuplas, calcula EMD al final sobre candidatos |

---

### Estructura de archivos

```
QNodes/                              GeoMIP/
├── src/
│   ├── strategies/                  ├── src/controllers/strategies/
│   │   └── q_nodes.py  ← principal  │   └── geometric.py  ← principal
│   ├── funcs/iit.py    ← EMD, labels ├── src/funcs/base.py ← EMD, Hamming
│   ├── controllers/manager.py       ├── src/controllers/manager.py
│   │   PATH_SAMPLES = "src/.samples/"│   auto-resuelve candidates list
│   └── src/.samples/N8A.csv         └── data/samples/N8A.csv
```

---

### Carga de la red (TPM)

- **QNodes:** `Manager(estado_inicial)` → `cargar_red()` lee `src/.samples/N{n}A.csv` relativo al directorio de ejecución.
- **GeoMIP:** `Manager(estado_inicial)` resuelve automáticamente (en `__post_init__`) entre tres candidatos de directorio; el canónico es `GeoMIP/data/samples/N{n}A.csv`.

---

### Bugs corregidos (sesión 2026-05-18)

| Módulo | Bug | Corrección |
|--------|-----|------------|
| `QNodes/src/main.py` | Importaba `src.strategies.qnodes` que usa `src.iit.*` (no existe) | Cambiado a `src.strategies.q_nodes` |
| `GeoMIP/src/main.py` | `GEOMIP_ROOT = parents[3]` = `Analisis/` en lugar de `GeoMIP/` | Corregido a `parents[1]` |
| `GeoMIP/src/main.py` | Salida en Excel (`.xlsx`), no en CSV | Cambiado a `to_csv(...)` en `results/resultados_N8A.csv` |
| Ambos | Leían `Pruebas_Metodo2.xlsx` con formato `Alcance\|Mecanismo` | Actualizado para leer `DatosPruebas2026_1.xlsx` (cols B, C separadas) |

---

## Próxima sesión

Continuar desde **Fase 1** de `sdd-2.md`:
- Crear `QNodes/src/strategies/kqnodes.py` — extensión Queyranne para k grupos
- Crear `QNodes/kexec.py` con punto de entrada para k configurable

Siempre debo avisar al usuario que acciones debe tomar para validar lo que hice (ejecuciones o ficheros nuevos)
