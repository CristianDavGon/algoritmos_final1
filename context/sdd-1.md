# Constitution

<!--
Todas las reglas de lo que se puede y no hacer en el proyecto, así como criterios de software, de calidad y principios del sistema.
-->

Reglas:

- Trabajar con redes de tamaño 10, 8, y 5, unicamente el humano ejecuta pruebas con tamaños superior.
- Cada archivo máximo 300LOC. Debe ser single-responsability >> Alta modularidad bajo acoplamiento.

# Clarificaction

<!--
Todas las preguntas que se deben resolver sobre el sistema y tener claro de inicio a fin el desarrollo
-->

# Especification

En el marco de la IIT4.0 (Integrated Information Theory) uno de sus principales enfoques es hallar la MIP (Partición de Mínima Información) en sistemas con datos discretos y continuos.

El objetivo de este proyecto es probar las siguientes estrategias:

- [GeoMIP](/GeoMIP/exec.py)
- [QNodes](/QNodes/exec.py)

Estas proveen una solución al problema en términos de una bipartición, donde se espera obtener el mínimo phi (pérdida) independiente a la forma en que quede bipartido el sistema.

Lo que se busca en este desarrollo es expandir el formato de biparticiones a k-particiones, donde trabajamos únicamente k=2,3,4,5.
Con esto se busca tener dos nuevas estrategias python llamadas KQNodes y KGEOMip.

La fuente de la verdad para hacer el proceso de pruebas está en:

- [DatosPruebas2026_1.xlsx](/data/DatosPruebas2026_1.xlsx)

Donde vamos a ejecutarlas siempre para la red de 8 para probar, y se generan los resultados en formato CSV.
Para cada k utilizado se guardan los resultados para ser comparados con respecto al algoritmo inicial y se deben hallar igualmente los optimos en términos de perdida


### Documentación

<!-- Se llega a la fase de documentación de resultados y graficas asociadas. -->
Para ello se escriben los manuales de la siguiente forma:

1. [Manual técnico](/manuals/tecnical/main.tex)
   - [Criterios de evaluación](/context/tecnico.md)
2. [Manual de usuario](/manuals/user/main.tex)
   - [Criterios de evaluación](/context/usuario.md)

[Criterios de calidad](/context/criterios.md)

# System Design

<!--
Todo lo relacionado a arquitectura actual y siguiente del sistema, diagramas mermaid de casos de uso, diagramas de secuencia, de clases y objetos, etc... Así como la escalabilidad y optimalidad del mismo.
-->

<!-- Test Driven Development -->

<!--
Desarrollo por objetivos y validación del sistema en cada una de las fases del desarrollo. Todo lo relacionado a pruebas unitarias, tests E2E, UX, DX.
-->
