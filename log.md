# Log de Trabajo: Generación de Reportes PDF, PPTX y Sitio de Scrollytelling

## 0. Migración a Nuevo Proyecto: AGT_USAC (2026-07-02)

Este proyecto (`AGT_USAC`) se creó copiando una estructura de carpetas y scripts ya existente, sin los datos crudos recolectados (`Dataset/`) ni los reportes/visualizaciones generados para ese caso (que quedaron ligados a temas específicos como "Aerómetro" y "Gestión Municipal").

- **Nuevo alcance:** monitoreo de conversación en redes sociales sobre Ana Glenda Tager, USAC, Ricardo Quiñonez y el plan de infraestructura.
- **Nueva dimensión de análisis:** clasificación de cuentas entre **usuarios comunes** y **medios de comunicación**, reflejada en la estructura de `Dataset/<categoría>/{Medios,Usuarios}/`.
- **Se conserva:** los scripts de procesamiento y generación de reportes (`scripts/`), el sitio de scrollytelling (`scrollytelling-site/`) y las convenciones documentadas más abajo en este log, ya que la base técnica (Apify → Python → HTML/PDF/PPTX/D3) sigue siendo válida para el nuevo caso.
- **Pendiente:** generar un nuevo listado semilla de cuentas a partir de los datos que se extraigan de Apify (el anterior `apify_users_list.txt` no se migró, por estar ligado al dataset del caso previo).

Las secciones siguientes documentan el trabajo técnico del proyecto original (`AGT`) y se mantienen como referencia de implementación.

## 1. Objetivo Inicial
El objetivo era convertir un reporte HTML (`reporte_ejecutivo_final.html`), cuyo contenido se generaba parcialmente con JavaScript, a dos formatos finales: un PDF de alta fidelidad y una presentación de PowerPoint (.pptx) con texto editable.

## 2. Proceso de Desarrollo y Desafíos

El proceso fue iterativo y presentó varios desafíos técnicos que requirieron múltiples ajustes a la estrategia.

### Intento 1: Conversión Directa y Replicación de Lógica
- **Estrategia:** Se intentó convertir el HTML directamente. Para el PPTX, se creó un script de Python que leía el HTML y el JSON por separado, intentando replicar la lógica del JavaScript para generar las diapositivas dinámicas. Para el PDF, se confió en que WeasyPrint manejaría el HTML.
- **Problemas:**
    - **Contenido Faltante:** Las partes del reporte que eran generadas por JavaScript no aparecían en los documentos finales. WeasyPrint no ejecuta JS, y la lógica replicada en Python para el PPTX era propensa a errores.
    - **Desorden en Diapositivas:** El script de PPTX no insertaba las diapositivas dinámicas en el orden correcto.
    - **Errores de Formato:** El formato (fuentes, colores, márgenes) no se respetaba en el archivo PPTX.
    - **División de Páginas en PDF:** El contenido de una "slide" de HTML se dividía en múltiples páginas en el PDF debido a problemas de overflow en el CSS.

### Intento 2: La Solución - Un Flujo de Dos Etapas

Tras los fracasos iniciales, se identificó que el problema raíz era la falta de una **fuente de verdad única y estática**. La solución fue implementar un flujo de trabajo de dos etapas:

**Etapa 1: Pre-renderizado a un HTML Estático**
- Se creó un nuevo script, `scripts/pre_render_html.py`.
- **Función:** Este script actúa como un "renderizador del lado del servidor". Carga el HTML dinámico (`reporte_ejecutivo_final.html`) y el archivo de datos (`visuals/executive_network.json`).
- **Ejecución:** Usando la librería `BeautifulSoup`, el script ejecuta la misma lógica que el JavaScript: crea el HTML para las diapositivas de "narrativas" y lo inyecta en la posición correcta, y puebla la lista de "bots".
- **Resultado:** Se genera un nuevo archivo, `reports/reporte_final_estatico.html`, que es un documento HTML completo, con las 8 diapositivas y todo el contenido, sin depender de JavaScript.

**Etapa 2: Conversión desde el HTML Estático**
- **PDF:** El script `scripts/generate_pdf.py` se simplificó para apuntar al nuevo HTML estático.
- **PPTX:** El script `scripts/generate_ppt_from_html.py` se reescribió y simplificó enormemente, eliminando toda la lógica de manejo de JSON y de creación dinámica. Ahora, simplemente parsea el HTML estático, que es una tarea mucho más simple y fiable.

### 3. Ajustes Finos para Calidad de Exportación

Incluso con el HTML estático, fueron necesarios ajustes finos:

- **Para el PDF (WeasyPrint):**
    - Se añadió una regla `@page { size: 1280px 720px; }` al CSS para forzar el tamaño de página 16:9.
    - Se luchó contra el desbordamiento de contenido (`overflow`) que cortaba las diapositivas. La solución final fue una combinación de:
        1.  Ajustes de CSS para reducir márgenes, paddings y tamaños de fuente (`h1`, `h2`, etc.).
        2.  Añadir `overflow: hidden` a la clase `.slide` como medida de seguridad.
        3.  **Ajuste de Contenido:** Se redujo la cantidad de elementos en las listas largas (influencers y bots) para asegurar que cupieran físicamente en la diapositiva.
- **Para el PPTX (python-pptx):**
    - Se mejoró la función de parseo para manejar correctamente texto con formato mixto (usando `runs` en `python-pptx`).
    - Se aseguró que el script leyera el HTML estático para garantizar que las 8 diapositivas se generaran en el orden correcto.

## 4. Lecciones Aprendidas
1.  **La Fuente de Verdad Única es Clave:** Intentar replicar lógicas complejas (como la de un JS) en diferentes lenguajes o scripts es frágil. Generar una fuente de datos estática y canónica (`reporte_final_estatico.html` en este caso) es una estrategia mucho más robusta.
2.  **El "Print CSS" es un Mundo Aparte:** El CSS que funciona en un navegador no siempre se traduce bien a medios paginados como el PDF. El manejo del `overflow`, el tamaño de página (`@page`) y el modelo de caja (márgenes, padding) debe ser mucho más estricto.
3.  **Iterar es Fundamental:** La solución final no fue obvia desde el principio. Fue necesario un proceso de depuración iterativo, respondiendo al feedback específico del usuario ("la slide 5 se corta"), para llegar a un resultado de alta calidad.

## 5. Implementación del Sitio de Scrollytelling Interactivo (AGT & Aerómetro)

### Objetivo:
Transformar el análisis estático de red de Ana Glenda Tager (AGT) y el Aerómetro en una experiencia web narrativa, responsiva e interactiva ("split-pane" scrollytelling), con total de control de acceso y alta fluidez de desplazamiento en cualquier navegador.

### Proceso de Implementación y Desafíos:
1. **Estructura Portátil y Auto-contenida:** Agrupamos todos los recursos visuales e interactivos en el directorio autónomo `/scrollytelling-site` (incluyendo su propia copia local de `visuals/`). Esto elimina la dependencia de carpetas padre y permite desplegar única y directamente este folder en GitHub Pages.
2. **Control de Acceso de Privacidad:** Se integró un script de bloqueo nativo en el `<head>` de `index.html` que solicita la contraseña `"pikachu"` antes de procesar el renderizado o scripts, denegando el acceso si el usuario cancela o falla.
3. **Físicas y Centrado Estelar de D3.js (Canvas 2D):**
   - **Eliminación del clumping:** Se removieron fuerzas de compresión x/y. Para evitar que la red se uniera en una bola densa ("un blob"), escalamos el radio de los nodos a un tamaño super estilizado de `Math.sqrt(val) * 0.65`.
   - **Separación de nodos:** Incrementamos la repulsión de carga (`chargeForce`) a `-140` y la distancia de enlaces a `70`, logrando un grafo amplio, aireado e increíblemente limpio donde las relaciones brillan por sí solas.
   - **Centrado de masa estable:** En `resetZoom`, cambiamos la lógica para centrar la cámara con base en el **centro de gravedad real (d3.mean)** de los nodos de la red, resolviendo la desviación que generaban cuentas aisladas en los bordes de la pantalla. Ampliamos el zoom inicial a un factor de `0.93`.
   - **Framing cómodo en narrativas:** Calibramos los zooms automáticos a un cómodo `0.85` en las vistas de clústeres (Pasos 2 a 5) para que todos los actores clave y conexiones de la comunidad se encuadren perfectamente sin recortarse.
4. **Tooltips Viewport-Aware:** Dotamos al tooltip de lógica responsiva al viewport. Mide su propio tamaño antes de pintarse y, si el cursor toca los límites inferiores o derechos de la pantalla, el tooltip invierte automáticamente su dirección de visualización (hacia arriba o hacia la izquierda), previniendo desbordamientos.

### Aprendizajes de Valor:
- **Decoplamiento de Física y Viewport:** Correr simulaciones de física estáticas parametrizadas (300 ticks iniciales y detenerlas) con factores de zoom calculados dinámicamente sobre la media posicional de los nodos garantiza una consistencia visual perfecta y un desplazamiento ultra fluido a 60 FPS en cualquier dispositivo.
- **Anomalías de Red vs. Contexto Humano:** El caso de `@Eriol_Gt` (clasificado algorítmicamente como orgánico, pero con nexos confirmados al netcenter *la Bendición*) demuestra el inmenso valor de combinar el análisis automatizado con la curaduría y el periodismo de contexto humano para validar hipótesis de desinformación.

## 6. Nubes de Palabras, Metodología y Ajustes de Texto (2026-07-02)

### Instalación de dependencias:
Se instalaron spaCy, wordcloud y el modelo `es_core_news_sm` (hubo que agregar `click` a mano, faltaba como dependencia de la CLI de spaCy). `scripts/generate_narrative_clouds.py` genera una nube por narrativa con color propio, más una nube aparte de "Medios" con todo el texto de reacciones a tuits de medios (sin filtrar por palabra clave).

### Ajustes de presentación:
- **Mayúsculas en títulos:** el CSS forzaba minúsculas a todo el texto de `h1`/`h2` y solo capitalizaba la primera letra (`text-transform: lowercase` + `::first-letter uppercase`), lo que rompía nombres propios como "Ana Glenda Tager" o "USAC". Se quitó ese CSS; los títulos ahora se escriben directamente con el casing correcto en el HTML.
- **Zoom por clúster:** en vez de un nivel de zoom fijo, ahora se calcula el área real que ocupan los actores de cada narrativa y se ajusta el zoom (entre 1.5x y 4x) para encuadrarlos con margen.
- **Físicas de la red:** distancia de enlace y repulsión de carga más compactas (`40`/`-80` en vez de `70`/`-140`) para mayor legibilidad con más de 55,000 nodos; `resetZoom` ya no tiene un tope artificial de escala.
- **Metodología explícita:** se documentó en el sitio, el README y GEMINI.md que la red parte de 29 publicaciones identificadas en Brand24 con alcance mayor a 20,000 vistas, y que se identifican las 20 cuentas con mayor centralidad como las que más impulsan cada narrativa.
- **Lenguaje:** se evita la palabra "heurística" en las descripciones — las reglas de clasificación (bots, medios) se describen de forma directa, sin nombrarlas como tales.
