**ANÁLISIS DE ENTREGABLES**

Proyecto K-QGMIP · Universidad de Caldas

Análisis y Diseño de Algoritmos · 2026-1

_Guía estructurada de requisitos: Manual de Usuario + Manual Técnico_

# **Introducción**

Este documento sintetiza de forma clara y estructurada todo lo que se solicita en los dos manuales del proyecto K-QGMIP. El objetivo es que tengas una referencia única, organizada por secciones, para saber exactamente qué debes entregar en cada documento.

| **Documento**         | **Naturaleza**                                                                                                                                                              |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MANUAL DE USUARIO** | Referencia/modelo a adaptar: describe el uso de GeoMIP desde la perspectiva del usuario final (instalación, configuración, ejecución, interpretación de resultados).        |
| ---                   | ---                                                                                                                                                                         |
| **MANUAL TÉCNICO**    | Especificación oficial de la materia: define exactamente qué secciones, diagramas, análisis y resultados debes incluir en la documentación técnica de tu extensión K-QGMIP. |
| ---                   | ---                                                                                                                                                                         |

**PARTE 1**

**MANUAL DE USUARIO - GeoMIP (Referencia)**

El Manual de Usuario de GeoMIP es el documento de referencia que muestra CÓMO debe estar estructurado tu propio Manual de Usuario para la extensión K-QGMIP. A continuación se detalla cada sección que contiene y qué se espera en cada una.

## **§1 · Introducción**

Qué se pide:

- Describir el propósito del framework desde la perspectiva del usuario final.
- Indicar a quién va dirigido el manual (perfil del lector: conocimientos básicos de Python y análisis computacional).
- Aclarar qué NO es necesario que el usuario sepa (por ejemplo, el desarrollo interno o los algoritmos subyacentes).

## **§2 · ¿Qué es el software y para qué sirve?**

Qué se pide:

- Descripción concisa de qué hace el sistema (en GeoMIP: calcula la Minimum Information Partition).
- Explicar qué puede hacer el usuario con él: analizar sistemas de distintos tamaños, seleccionar el método de cálculo y obtener la partición óptima con su pérdida.
- Indicar el contexto de uso: investigación académica, experimentos exploratorios o análisis sistemáticos reproducibles.

## **§3 · Requisitos del usuario**

Qué se pide:

- Listar los prerrequisitos de entorno y conocimiento:
  - Entorno Python funcional.
  - Máquina con recursos acordes al tamaño del sistema a analizar.
  - Familiaridad básica con ejecución de scripts desde línea de comandos o IDE.
- Mencionar si se requiere hardware especializado (GPU opcional para acelerar un método).

## **§4 · Instalación y configuración**

Qué se pide:

- Explicar cómo se distribuye el software (código fuente descargable).
- Indicar que se recomienda crear un entorno virtual para aislar dependencias.
- Describir cómo instalar las dependencias declaradas en los archivos de configuración del proyecto.
- Aclarar que si hay GPU disponible el entorno puede configurarse para paralelización multinúcleo; si no, el software corre en CPU sin ajustes adicionales.

## **§5 · Uso básico del software**

Qué se pide:

- Describir el flujo general de uso: script principal que orquesta la carga del sistema, selección del método y ejecución del cálculo.
- Indicar qué debe especificar el usuario: estado inicial del sistema, máscaras binarias (condición, mecanismo, alcance) y método de cálculo.
- Explicar cómo pueden proporcionarse los parámetros (directamente en el script o mediante archivos de entrada).

## **§6 · Ejecución del software**

Esta es la sección más extensa del manual. Se divide en tres subsecciones:

### **§6.1 · Entrada de datos del sistema**

Qué se pide documentar:

- Matriz de Transición Probabilística (TPM): qué es, para qué sirve, cómo se carga (ejemplo con numpy.genfromtxt desde un CSV), dónde están las redes de prueba (carpeta .samples/).
- Estado inicial del sistema: definición, formato (cadena binaria), ejemplo para red de 20 nodos.
- Máscaras binarias: definir y ejemplificar condiciones, alcance y mecanismo.
- Inicialización del sistema: uso de la clase Manager y cómo se construye el objeto de configuración.
- Preparación del subsistema: indicar que es automática (clase base SIA) y que el usuario no interviene directamente.

### **§6.2 · Método Geométrico (Método 1)**

Qué se pide documentar:

- Para qué tipo de sistemas es adecuado (sistemas grandes).
- Prerrequisito: objeto Manager configurado correctamente.
- Clase que lo implementa: Geometry (en geometry.py) y método público aplicar_estrategia(...).
- Pasos de ejecución numerados: inicializar datos → crear Manager → instanciar Geometry → llamar aplicar_estrategia.
- Ejemplo de código completo con comentarios.
- Descripción del objeto resultado: bipartición óptima, pérdida asociada, metadatos.

### **§6.3 · Método de Programación Dinámica (Método 2)**

Qué se pide documentar (7 pasos):

- Ubicar el archivo de ejecución: GeoMIPMetodo2/src/main.py, función ejecutar_desde_excel(...).
- Identificar y seleccionar la TPM de trabajo (archivo CSV en .samples/).
- Preparar el archivo Excel con los subsistemas en el formato esperado.
- Verificar el estado inicial y condiciones globales del sistema.
- Inicializar el sistema con la clase Manager.
- Ejecutar el método con los parámetros ruta_excel, ruta_salida, inicio y cantidad.
- Ubicar los resultados generados en la ruta de salida.

- Incluir ejemplo de ejecución sobre una red de 4 nodos (archivo exec.py en la raíz).

## **§7 · Interpretación de resultados**

Qué se pide:

- Describir la estructura de la solución que retorna el framework:
  - Partición óptima identificada.
  - Valor de la pérdida asociada.
  - Información del subsistema evaluado.
- Explicar qué significa la partición (división del sistema en dos subconjuntos).
- Explicar qué cuantifica la pérdida (impacto en términos de información integrada).
- Indicar cómo pueden usarse los resultados (análisis posteriores, exportación).

**Nota importante:** El Manual de Usuario de GeoMIP es el MODELO. Tu entrega debe replicar esta misma estructura pero para la extensión K-QGMIP (k-particiones), adaptando cada sección a los dos nuevos métodos: KGeoMIP y KQNodes.

**PARTE 2**

**MANUAL TÉCNICO - Especificación oficial de entregables**

El Manual Técnico es la especificación detallada que tu equipo debe cumplir al 100%. Cada subsección a continuación corresponde a una sección obligatoria del documento final.

## **Convenciones de nomenclatura obligatorias**

Antes de escribir una sola línea de documentación, debes aplicar estas convenciones de forma consistente en el repositorio Git, carpetas, clases y referencias:

| **Estrategia**           | **Nombre de repositorio / carpeta / clase principal** |
| ------------------------ | ----------------------------------------------------- |
| **GeoMIP K-particiones** | KGeoMIP                                               |
| ---                      | ---                                                   |
| **QNodes K-particiones** | KQNodes                                               |
| ---                      | ---                                                   |

La 'K' inicial distingue estas extensiones de las implementaciones originales de bi-particiones (GeoMIP y QNodes).

## **§2.1 · Resumen Ejecutivo**

Qué debes incluir:

- Descripción concisa del problema abordado y su relevancia.
- Enfoque algorítmico implementado en términos generales.
- Principales resultados obtenidos y contribuciones del proyecto.
- Limitaciones encontradas y recomendaciones de uso.

## **§2.2 · Fundamentos Teóricos**

Qué debes incluir:

- **Definición formal de k-particiones:** Notación matemática precisa, propiedades fundamentales y ejemplos ilustrativos para n=3 o n=4.
- **Formulación del problema de optimización:** Función(es) objetivo a optimizar y restricciones del problema.
- **Extensión del marco teórico:** Cómo se extiende GeoMIP/QNodes de bi-particiones a k-particiones. Justificación de que las estrategias obtienen una 'buena' respuesta.
- **Análisis de complejidad del espacio de soluciones:** Crecimiento del problema y comparación con el caso de bi-particiones.

## **§2.3 · Arquitectura del Software**

Qué debes incluir (todos los diagramas deben seguir notación UML 2.x estándar, estar numerados y tener título descriptivo):

| **Diagrama de Arquitectura General**                                                               |
| -------------------------------------------------------------------------------------------------- |
| • Representación visual de los componentes principales del sistema.                                |
| ---                                                                                                |
| • Cómo se integra la extensión k-particiones con la infraestructura existente del proyecto GeoMIP. |
| ---                                                                                                |

| **Diagrama de Clases (UML)**                                                         |
| ------------------------------------------------------------------------------------ |
| • Clase base SIA y su relación de herencia con KGeoMIP y KQNodes.                    |
| ---                                                                                  |
| • Clases auxiliares y estructuras de datos (N-Cubos, gestores de particiones, etc.). |
| ---                                                                                  |
| • Atributos principales de cada clase con sus tipos.                                 |
| ---                                                                                  |
| • Métodos públicos y privados más importantes.                                       |
| ---                                                                                  |
| • Relaciones de composición, agregación y dependencia.                               |
| ---                                                                                  |

| **Diagrama de Paquetes**                                                                               |
| ------------------------------------------------------------------------------------------------------ |
| • Estructura de directorios del proyecto (src/controllers/strategies/, src/models/, src/utils/, etc.). |
| ---                                                                                                    |
| • Dependencias entre paquetes y módulos.                                                               |
| ---                                                                                                    |
| • Ubicación de archivos de configuración, tests y documentación.                                       |
| ---                                                                                                    |

| **Diagrama(s) de Secuencia (UML)**                                |
| ----------------------------------------------------------------- |
| • Inicialización del sistema y carga de datos.                    |
| ---                                                               |
| • Búsqueda de k-MIP para un valor específico de k.                |
| ---                                                               |
| • Evaluación de una k-partición candidata.                        |
| ---                                                               |
| • Interacción entre componentes principales durante la ejecución. |
| ---                                                               |

| **Patrones de Diseño Aplicados**                                                                |
| ----------------------------------------------------------------------------------------------- |
| • Identificación y justificación de patrones usados (Strategy, Template Method, Factory, etc.). |
| ---                                                                                             |
| • Explicar cómo facilitan la extensibilidad y mantenibilidad del código.                        |
| ---                                                                                             |

| **Decisiones Arquitectónicas Clave**                                               |
| ---------------------------------------------------------------------------------- |
| • Estrategia de reutilización de componentes existentes (o si se reimplementaron). |
| ---                                                                                |
| • Trade-offs considerados entre flexibilidad y rendimiento.                        |
| ---                                                                                |
| • Separación de responsabilidades entre componentes.                               |
| ---                                                                                |

## **§2.4 · Diseño Algorítmico**

Esta es la sección central del manual. Debe permitir reproducir el algoritmo. Qué debes incluir:

- **Visión general del algoritmo:** Descripción en alto nivel del enfoque, filosofía de diseño y relación con GeoMIP/QNodes originales.
- **Pseudocódigo detallado:** Algoritmos principales y subrutinas clave, con notación consistente con los fundamentos teóricos.
- **Estructuras de datos:** Descripción de N-Cubos, tabla de costos, representación de particiones; justificación y diagramas cuando aplique.
- **Estrategia de búsqueda:** Cómo se genera y explora el espacio de k-particiones candidatas. Técnicas empleadas: PD, D&V, voraz, B&B, aproximados, etc. Si hay heurísticas, describir su funcionamiento y justificación.
- **Evaluación de particiones:** Procedimiento para calcular la pérdida de información de una k-partición candidata.
- **Optimizaciones implementadas:** Técnicas específicas para mejorar eficiencia: caching, paralelización, etc.

## **§2.5 · Análisis de Complejidad**

Análisis teórico riguroso. Qué debes incluir:

- **Complejidad temporal:** Cotas asintóticas fuertes en función de n (número de variables) y k (número de particiones). Identificar operaciones dominantes y cuellos de botella.
- **Complejidad espacial:** Análisis del uso de memoria, estructuras permanentes y temporales.
- **Análisis de casos:** Mejor caso y peor caso. Qué características del sistema o valor de k conducen a cada caso.
- **Comparación con alternativas:** Contrastar con búsqueda exhaustiva/fuerza bruta y con las estrategias originales de bi-particiones.

## **§2.6 · Detalles de Implementación**

Aspectos específicos de la implementación en Python. Qué debes incluir:

- **Métodos principales:** Funcionalidad de cada método público importante: firma de función, parámetros, valores de retorno y excepciones.
- **Dependencias externas:** Bibliotecas utilizadas (NumPy, SciPy, etc.), versiones requeridas y para qué se usan.
- **Aspectos de ingeniería de software:** Manejo de errores, logging, validación de inputs y estrategias de debugging.
- **Tests implementados:** Tests unitarios y de integración, casos de prueba específicos y estrategia de validación.

## **§2.7 · Resultados Experimentales**

Presentación de los resultados obtenidos. Qué debes incluir:

- **Datasets utilizados:** Descripción de los sistemas de prueba y sus características relevantes (tamaño, origen, etc.).
- **Métricas de evaluación:** Definición clara de métricas: tiempo de ejecución, tasa de acierto, error relativo, speedup, etc.
- **Tablas de resultados:** Tablas bien formateadas con resultados numéricos para diferentes combinaciones de n y k. Incluir desviaciones estándar donde aplique.
- **Gráficas y visualizaciones:** Gráficos de escalabilidad (tiempo vs n, tiempo vs k), curvas de precisión, visualizaciones de k-particiones sobre hipercubos, comparaciones con métodos baseline.
- **Análisis de resultados:** Interpretación de patrones, casos donde el algoritmo funciona mejor/peor, comparación entre KGeoMIP y KQNodes.
- **Validación de correctitud:** Evidencia de que los resultados son correctos: comparación con búsqueda exhaustiva para casos pequeños y verificación de consistencia para k=2.

## **§2.8 · Limitaciones y Trabajo Futuro**

Reflexión crítica. Qué debes incluir:

- **Limitaciones conocidas:** Restricciones del enfoque actual, casos donde no funciona óptimamente y limitaciones de escalabilidad.
- **Supuestos y restricciones:** Suposiciones hechas durante el desarrollo que podrían no cumplirse en todos los contextos.
- **Mejoras potenciales:** Ideas concretas para optimizar el algoritmo, extender funcionalidad o mejorar robustez.
- **Direcciones de investigación futura:** Preguntas abiertas y extensiones interesantes del trabajo actual.

## **§2.9 · Apéndices Técnicos**

Material complementario. Qué debes incluir:

- **Demostraciones:** Pruebas detalladas de proposiciones mencionadas en el texto principal cuyo desarrollo completo interrumpiría el flujo.
- **Detalles algorítmicos adicionales:** Pseudocódigo de funciones auxiliares, optimizaciones menores o variantes exploradas.
- **Resultados experimentales de las pruebas:** Tablas completas, experimentos adicionales no incluidos en el cuerpo principal y análisis de sensibilidad de parámetros.
- **Referencias y bibliografía:** Lista completa de artículos, libros y recursos consultados con formato académico apropiado.

## **§3 · Estándares de Formato y Presentación**

Requisitos formales que DEBE cumplir el documento:

| **Elemento**              | **Requisito**                                                                                                         |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Formato del archivo**   | PDF o Word (.docx), tamaño carta                                                                                      |
| ---                       | ---                                                                                                                   |
| **Fuente**                | Arial o Times New Roman, 11 puntos                                                                                    |
| ---                       | ---                                                                                                                   |
| **Ecuaciones**            | Editor de ecuaciones (LaTeX, MathType o Word). Notación consistente en todo el documento                              |
| ---                       | ---                                                                                                                   |
| **Diagramas UML**         | UML 2.x estándar. Colores moderados para legibilidad. Cada diagrama numerado y con título descriptivo                 |
| ---                       | ---                                                                                                                   |
| **Figuras y tablas**      | Numeradas secuencialmente, con título descriptivo y referencia en el texto. Calidad de imagen apropiada para revisión |
| ---                       | ---                                                                                                                   |
| **Código / pseudocódigo** | Fuente monoespaciada (Courier New o Consolas), sangrado consistente, resaltado de sintaxis cuando sea posible         |
| ---                       | ---                                                                                                                   |
| **Organización**          | Tabla de contenidos al inicio, numeración de secciones, encabezados distintivos y páginas numeradas                   |
| ---                       | ---                                                                                                                   |
| **Calidad de redacción**  | Lenguaje técnico preciso, gramática y ortografía correctas, argumentación lógica y coherente                          |
| ---                       | ---                                                                                                                   |

## **§4 · Uso de Inteligencia Artificial Generativa**

Si usaste ChatGPT, Claude, GitHub Copilot u otras herramientas de IA durante el proyecto, DEBES incluir una subsección que documente:

- Qué herramientas se utilizaron y en qué etapas (diseño, implementación, debugging, optimización, documentación).
- Ejemplos específicos de prompts o consultas realizadas y cómo influyeron en decisiones de diseño.
- Qué partes del código o pseudocódigo fueron generadas o significativamente influenciadas por IA.
- Reflexión crítica sobre ventajas y limitaciones de usar estas herramientas.

**Esta sección NO penaliza tu calificación.** Por el contrario, documenta profesionalismo y honestidad académica. Lo evaluado es la comprensión profunda del trabajo y la capacidad de justificar las decisiones algorítmicas.