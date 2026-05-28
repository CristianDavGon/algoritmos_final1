# Tareas Activas — Fase 1

## Tareas del Agente IA

### 1.1 — Trazar flujo GeoMIP [EN CURSO]
**Objetivo**: Leer `code/GeoMIP/exec.py` → `src/main.py` → `GeometricSIA.aplicar_estrategia()` y documentar el flujo con contratos reales.

**Entregable**: Sección en `context/SDD-0/implementation.md` con el flujo de ejecución anotado.

---

### 1.2 — Trazar flujo QNodes [PENDIENTE]
**Objetivo**: Leer `code/QNodes/exec.py` → `src/main.py` → `QNodes.aplicar_estrategia()` y documentar diferencias con GeoMIP.

**Entregable**: Sección en `context/SDD-0/implementation.md` con comparativo GeoMIP vs QNodes.

---

### 1.3 — Verificar contratos de módulos [PENDIENTE]
**Objetivo**: Para cada clase (`SIA`, `System`, `NCube`, `Solution`, `Manager`) verificar en código real: entradas, salidas, invariantes.

**Archivos a leer**:
- `code/GeoMIP/src/models/base/sia.py`
- `code/GeoMIP/src/models/core/system.py`
- `code/GeoMIP/src/models/core/ncube.py`
- `code/GeoMIP/src/models/core/solution.py`
- `code/GeoMIP/src/controllers/manager.py`
- Los equivalentes en `code/QNodes/src/`

---

### 1.4 — Identificar diferencias reales GeoMIP vs QNodes [PENDIENTE]
**Objetivo**: Más allá de lo documentado en `architecture.md`, encontrar diferencias en el código real: nombres, comportamientos, acoplamiento, etc.

**Entregable**: Tabla actualizada en `context/SDD-0/implementation.md`.

---

### 1.5 — Mapear deuda técnica [PENDIENTE]
**Objetivo**: Buscar `print(`, `TODO`, `FIXME`, `#!`, código duplicado, falta de type hints, métodos sin docstring.

**Entregable**: Lista en `context/state/known-issues.md`.

---

### 1.6 — Documentar decisiones bloqueantes [PENDIENTE]
**Objetivo**: Registrar formalmente las 4 decisiones bloqueantes de `context/project/decisions.md` en el SDD-0 y escalar al usuario para resolución.

---

## Tareas del Usuario

### U.1 — Leer el flujo de ejecución de GeoMIP [PENDIENTE]
Archivos a leer en orden:
1. [exec.py](../../code/GeoMIP/exec.py) — punto de entrada
2. [src/main.py](../../code/GeoMIP/src/main.py) — función `iniciar()`
3. [src/controllers/manager.py](../../code/GeoMIP/src/controllers/manager.py) — qué hace `Manager`
4. [src/models/base/sia.py](../../code/GeoMIP/src/models/base/sia.py) — contrato de `SIA`
5. [src/controllers/strategies/geometric.py](../../code/GeoMIP/src/controllers/strategies/geometric.py) — algoritmo geométrico

**Pregunta guía**: ¿Cómo llega la TPM desde el archivo CSV hasta el cálculo de EMD?

---

### U.2 — Responder preguntas de comprensión [PENDIENTE]
Ver `context/SDD-0/testing.md` — son 10 preguntas de trazado de flujo.

---

### U.3 — Ejecutar GeoMIP para n=5 [PENDIENTE]
```bash
cd code/GeoMIP
python exec.py
```
Observar: ¿qué se imprime?, ¿qué CSV se genera?, ¿cuánto tarda?

---

### U.4 — Confirmar decisiones bloqueantes [PENDIENTE]
Ver `context/SDD-0/decisions.md` — hay 4 preguntas que requieren tu decisión antes de empezar Fase 4 (KQNodes).
