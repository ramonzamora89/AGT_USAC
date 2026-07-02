# Proyecto AGT_USAC: Portal de Scrollytelling

Este documento resume la visión, arquitectura técnica y decisiones tomadas durante el desarrollo del portal de scrollytelling interactivo del proyecto, enfocado en **Ana Glenda Tager, USAC, Ricardo Quiñonez y el plan de infraestructura**.

## 0. Metodología de datos

Se identificaron 29 publicaciones en Brand24 con un alcance mayor a 20,000 vistas. A partir de esas publicaciones semilla se extrajeron comentarios, quote-tweets y redes de followers/following, y se separaron las cuentas de medios de comunicación del resto de la conversación.

La red completa tiene 55,309 nodos y 114,126 relaciones. El sitio no carga esa red completa: `scripts/export_executive_json.py` la recorta a un subconjunto liviano (medios, actores de cada narrativa, los 20 hubs principales, una muestra de las cuentas inorgánicas más activas, y las cuentas de mayor centralidad para dar textura visual), y ese subconjunto — no la red completa — es lo que se guarda en `visuals/executive_network.json` y se dibuja en el canvas. Esto es lo que permite que el navegador cargue y anime el grafo sin trabarse y haga zooms fluidos a cada clúster.

## 1. Visión Narrativa

El objetivo del portal es guiar al lector a través de una historia estructurada que revela de forma interactiva los hallazgos de la red de conversación digital:

1. **Macro-Grafo Inicial:** Se presenta un recorte representativo de la red (~1,800 nodos, ~31,600 relaciones) sobre un total de 55,309 nodos y 114,126 relaciones.
2. **Orgánico vs. Inorgánico:** Se iluminan de color rojo las cuentas con patrones anómalos de followers/following o de interacción (9.23%) frente a los perfiles con patrones normales, en azul.
3. **Medios de comunicación (clúster aparte):** Los 7 medios confirmados se agrupan de forma natural en su propio clúster de la red; se muestra qué narrativas dominan en las reacciones a sus tuits.
4. **Clústeres Narrativos (Zoom Focalizado):** La cámara se traslada hacia los centros de gravedad de las 5 narrativas temáticas del debate (decepción política, USAC/fraude, pactos y corrupción, figura de Ana Glenda Tager, plan de infraestructura/Quiñonez).
5. **Caracterización de cuentas inorgánicas:** Se expone una muestra de cuentas con relación anómala entre followers y following.
6. **Top Hubs:** Se identifican las 20 cuentas con mayor centralidad como las que más impulsan las narrativas del debate, junto con los medios de comunicación confirmados.

No se generaron nubes de palabras al inicio por falta de spaCy/wordcloud instalados; ya se agregaron después (ver README del proyecto raíz). No se clasificó individualmente cada una de las ~55k cuentas como medio/usuario — se prioriza el agrupamiento por narrativa, con los medios como el único subconjunto de cuentas verificado a mano.

## 2. Arquitectura de Software

La aplicación sigue una arquitectura **split-pane (pantalla dividida)** altamente responsiva y desacoplada, programada 100% en Vanilla web estándar para facilitar su despliegue y portabilidad:

- **Estructura Portátil (`scrollytelling-site/`):** Todos los archivos de la aplicación (incluyendo su propia subcarpeta local `visuals/`) se encuentran auto-contenidos, permitiendo desplegar de manera inmediata únicamente esta carpeta.
- **Control de Acceso Privado:** Un script bloqueador en el `<head>` interrumpe el renderizado hasta que el usuario digita la clave correcta: `"pikachu"`.
- **Controlador de Scroll (`js/app.js`):** Implementa el API nativo `IntersectionObserver` de JS para detectar cuando una tarjeta de texto entra al 50% central de la pantalla, aplicando transiciones CSS suaves y despachando eventos a la simulación.
- **Motor Gráfico de Redes (`js/network.js`):** Desarrollado sobre D3.js (v7) implementando renderizado en **Canvas 2D** en lugar de SVG.
  - **Físicas Pre-calculadas:** Ejecuta la simulación de fuerzas (enlace a `40` de distancia y repulsión de carga a `-80`, valores compactos para legibilidad con más de 55,000 nodos) estáticamente por 300 ticks al cargar la página y la congela. Esto reduce el uso de CPU a cero durante el scroll y elimina cualquier vibración de nodos.
  - **Encuadre Dinámico (`resetZoom`):** Mide la distribución espacial del grafo y usa la media aritmética (`d3.mean`) para centrarlo en pantalla, cubriendo el 90% del lienzo según la distribución real de los nodos.
  - **Zoom por clúster ajustado al tamaño real:** al enfocar una narrativa, calcula el área que ocupan sus cuentas más relevantes y ajusta el zoom (entre 1.5x y 4x) para encuadrarlas con margen, en vez de usar un nivel de zoom fijo.
  - **Tooltips Viewport-Aware:** Un gestor de posicionamiento evalúa si el tooltip flotante colisiona con el borde inferior o derecho de la pantalla, invirtiendo su renderizado automáticamente para evitar recortes de texto.

## 3. Despliegue

La carpeta del proyecto está lista para ser servida localmente con un comando simple:
```bash
python3 -m http.server 8000
```
Y empujada de forma totalmente aislada a **GitHub Pages** para una visualización segura y veloz desde cualquier parte del mundo.
