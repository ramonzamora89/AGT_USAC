# AGT_USAC - Análisis de Redes Sociales

Proyecto de monitoreo digital y análisis de redes sociales sobre la conversación sobre Ana Glenda Tager, USAC, Ricardo Quiñonez y el plan de infraestructura.

## Descripción
Este proyecto analiza la conversación en redes sociales (principalmente Twitter/X) en torno a Ana Glenda Tager, la Universidad de San Carlos (USAC), Ricardo Quiñonez y el plan de infraestructura. Se enfoca en identificar narrativas, actores relevantes y la estructura de la red de conversación, distinguiendo entre **cuentas de usuarios comunes** y **cuentas de medios de comunicación**.

## Estructura del Proyecto
- `Dataset/`: Datos extraídos de redes sociales mediante Apify (tuits, comentarios, quotes y redes de seguidores). Cada subcategoría se divide en:
  - `Medios/`: Contenido y cuentas identificadas como medios de comunicación.
  - `Usuarios/`: Contenido y cuentas de usuarios comunes.
- `reports/`: Entregables finales en formatos Markdown, HTML y PDF (formato vertical 1080x1920).
- `scripts/`: Herramientas de procesamiento de lenguaje natural (NLP) y generación de reportes.
- `visuals/`: Visualizaciones de datos y nubes de palabras temáticas.
- `scrollytelling-site/`: Sitio web interactivo de tipo scrollytelling para presentar el análisis de red.
- `Referencias/`: Documentación de soporte de proyectos base.
- `templates/`: Plantillas para reportes de monitoreo.
- `Literatura/`: Bibliografía de referencia (agenda setting, framing, análisis de redes sociales).

## Metodología
- **Selección de semillas:** 29 publicaciones identificadas en Brand24 con un alcance mayor a 20,000 vistas sobre Ana Glenda Tager, USAC, Ricardo Quiñonez y el plan de infraestructura.
- **Extracción:** Apify (Twitter/X) — comentarios, quote tweets y datos de red (followers/following) de esas publicaciones semilla.
- **Construcción de la red:** A partir de esas relaciones se arma el grafo de la conversación, separando desde el inicio las cuentas de medios de comunicación del resto.
- **Narrativas:** Agrupamiento de la conversación en narrativas temáticas por palabra clave, y detección de las 20 cuentas con mayor centralidad como las que más impulsan cada narrativa.
- **Procesamiento:** Python (Pandas, NetworkX, spaCy).
- **Visualización:** WordCloud (Python) y D3.js (sitio de scrollytelling).
- **Generación:** WeasyPrint para exportación a PDF de alta fidelidad.

## Uso
Para regenerar el reporte tras actualizar los datasets:
1. Clasificar los datos extraídos en `Dataset/<categoría>/Medios/` y `Dataset/<categoría>/Usuarios/`.
2. Ejecutar los scripts de procesamiento en `scripts/` (`process_network.py`, `process_executive.py`).
3. Ejecutar `python scripts/generate_pdf.py` para generar el reporte final.
