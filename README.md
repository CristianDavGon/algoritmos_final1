# Proyecto V03 FINAL — MIP / IIT k-particiones

Dos implementaciones de la **Minimum Information Partition (MIP)** en el marco de IIT 4.0,
extendidas para k-particiones (k ∈ {2, 3, 4, 5}):

| Módulo | Estrategia | Estado |
|--------|-----------|--------|
| `QNodes/` | Queyranne submodular O(D³·N) | ✅ Base funcional |
| `GeoMIP/` | Geométrico-topológico (Hamming) | ✅ Base funcional |

---

## Requisitos

- Python 3.11+ con **`uv`** instalado
- Windows 10 / Linux (Ubuntu)

```bash
pip install uv
```

---

## Estructura del proyecto

```
Proyecto V03 FINAL/
├── data/
│   └── DatosPruebas2026_1.xlsx   ← dataset canónico (N=5,8,10,...)
├── QNodes/
│   ├── exec.py                   ← punto de entrada bipartición
│   ├── src/
│   │   ├── .samples/N8A.csv      ← TPM red N=8
│   │   └── strategies/q_nodes.py ← algoritmo Queyranne
│   └── results/                  ← CSVs de salida (se crean al ejecutar)
├── GeoMIP/
│   ├── exec.py                   ← punto de entrada bipartición
│   ├── data/samples/N8A.csv      ← TPM red N=8
│   └── results/                  ← CSVs de salida (se crean al ejecutar)
└── context/
    └── sdd-2.md                  ← hoja de ruta del desarrollo
```

---

## Ejecución y validación

### QNodes

```bash
cd QNodes
uv sync
uv run exec.py
```

**Qué hace:**
1. Lee las pruebas de `data/DatosPruebas2026_1.xlsx` hoja `8A-Elementos`.
2. Para cada fila (Alcance en col B, Mecanismo en col C) ejecuta QNodes sobre `N8A.csv`.
3. Guarda resultados en **`QNodes/results/resultados_N8A.csv`**.

**Criterio de validación — ejecución correcta:**
- El archivo `QNodes/results/resultados_N8A.csv` existe al terminar.
- Las columnas del CSV son:

| Columna | Descripción |
|---------|-------------|
| `Prueba` | Número de prueba (1-N) |
| `Alcance` | Letras del purview, ej. `ABCDEFGH` |
| `Mecanismo` | Letras del mecanismo, ej. `ABCDEFG` |
| `Partición` | Texto de la bipartición óptima |
| `Pérdida (φ)` | Valor φ mínimo (float) |
| `Tiempo (s)` | Tiempo de ejecución en segundos |

**Valores esperados para las primeras pruebas de N=8:**

| Prueba | Alcance | Mecanismo | φ esperado |
|--------|---------|-----------|------------|
| 1 | ABCDEFGH | ABCDEFGH | 0.5 |
| 2 | ABCDEFGH | ABCDEFG | verificar |
| 3 | ABCDEFGH | BCDEFGH | verificar |

> Prueba 1 ya verificada: φ = 0.5 ✓

---

### GeoMIP

```bash
cd GeoMIP
uv sync
uv run exec.py
```

> **Windows:** GeoMIP usa `multiprocessing`. Ejecutar desde PowerShell o CMD directamente
> (no desde el REPL interactivo de Python), o agregar el flag si hay problemas:
> `uv run --no-isolation exec.py`

**Qué hace:**
1. Lee las pruebas de `data/DatosPruebas2026_1.xlsx` hoja `8A-Elementos`.
2. Para cada prueba lanza un subproceso con timeout de 1 hora.
3. Guarda resultados en **`GeoMIP/results/resultados_N8A.csv`**.

**CSV generado — mismas columnas que QNodes:**

| Columna | Descripción |
|---------|-------------|
| `Prueba` | Número de prueba |
| `Alcance` | Letras del purview |
| `Mecanismo` | Letras del mecanismo |
| `Partición` | Texto de la bipartición óptima |
| `Pérdida (φ)` | Valor φ mínimo |
| `Tiempo (s)` | Tiempo de ejecución en segundos |

---

## Validación cruzada (Fase 0 ✓)

Para confirmar que todo funciona correctamente, verificar:

1. **Archivos generados:**
   ```
   QNodes/results/resultados_N8A.csv   ← debe existir con filas de datos
   GeoMIP/results/resultados_N8A.csv   ← debe existir con filas de datos
   ```

2. **φ no negativo:** ninguna fila en `Pérdida (φ)` debe tener valores negativos.

3. **Filas sin error:** la columna `Partición` no debe estar vacía en las primeras pruebas
   (las primeras filas del Excel son las más simples — si fallan, hay un bug).

4. **Consistencia Prueba 1:** ambos módulos deben dar el mismo φ para la misma prueba
   (bipartición óptima puede diferir en representación pero φ debe ser igual).

---

## Variables de entorno (opcional)

Permiten sobreescribir rutas sin editar código:

| Variable | Módulo | Por defecto |
|----------|--------|-------------|
| `GEOMIP_INPUT_XLSX` | GeoMIP | `data/DatosPruebas2026_1.xlsx` |
| `GEOMIP_OUTPUT_CSV` | GeoMIP | `GeoMIP/results/resultados_N8A.csv` |
| `GEOMIP_ESTADO_INICIO` | GeoMIP | `10000000` (N=8) |

Ejemplo PowerShell:
```powershell
$env:GEOMIP_ESTADO_INICIO = "10000"   # cambiar a N=5
cd GeoMIP
uv run exec.py
```

---

## Cambiar la red de prueba

Edita el `estado_inicio` en `QNodes/src/main.py` → función `iniciar()`:

```python
estado_inicio = "10000"      # N=5 — más rápido para desarrollo
estado_inicio = "10000000"   # N=8 — canónico
```

Para GeoMIP usar la variable de entorno o editar `GeoMIP/src/main.py` → `iniciar()`.

---

## Hoja de ruta del desarrollo

Ver [`context/sdd-2.md`](context/sdd-2.md) para el plan completo de fases.

| Fase | Objetivo | Estado |
|------|----------|--------|
| 0 | Base funcional — ambos módulos corren y generan CSV | ✅ Completada |
| 1 | KQNodes — Queyranne extendido a k particiones | 🔲 Pendiente |
| 2 | KGeoMIP — Geométrico extendido a k particiones | 🔲 Pendiente |
| 3 | Experimentación — comparativa φ vs k en N=8 | 🔲 Pendiente |
| 4 | Documentación — manuales LaTeX técnico y usuario | 🔲 Pendiente |
