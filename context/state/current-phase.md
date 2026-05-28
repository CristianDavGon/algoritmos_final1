# Fase Actual

**Fase**: Fase 1 — Comprensión profunda del proyecto
**Estado**: 🟡 EN CURSO
**Inicio**: 2026-05-27
**SDD asociado**: `context/SDD-0/`

## Objetivo

Entender a fondo el código existente antes de modificar nada: flujo de ejecución, contratos entre módulos, puntos de extensión y deuda técnica conocida.

## Criterio de salida

- El agente puede explicar el flujo completo `exec.py → iniciar() → aplicar_estrategia()` sin leer el código.
- `context/state/known-issues.md` actualizado con todos los problemas identificados.
- Decisiones bloqueantes para k-particiones resueltas o formalmente documentadas como pendientes.

## Siguiente fase

→ **Fase 2 — Validación del funcionamiento** (ejecutar GeoMIP y QNodes para n=5 y n=8, comparar con BruteForce/PyPhi).
