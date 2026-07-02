# AGT_USAC: Sitio de Scrollytelling Interactivo

Este es un portal interactivo de **scrollytelling** diseñado para guiar al usuario a través del análisis de redes sociales (SNA) en torno a Ana Glenda Tager, USAC, Ricardo Quiñonez y el plan de infraestructura. La red se construyó a partir de 29 publicaciones identificadas en Brand24 con un alcance mayor a 20,000 vistas, separando desde el inicio las cuentas de medios de comunicación del resto de la conversación.

## Características Principales

1. **Visión Macro a Micro:** Visualiza la topología completa del debate de forma interactiva.
2. **Clasificación Orgánica e Inorgánica:** Revela las cuentas coordinadas (inorgánicas) que amplifican la conversación de forma artificial, coloreadas en rojo, frente a los perfiles legítimos (azules).
3. **Medios como clúster aparte:** Los medios de comunicación confirmados (color ámbar) se muestran como su propio grupo, con las narrativas dominantes en las reacciones a sus tuits.
4. **Filtro de Clústeres Narrativos:** Al desplazarse, el grafo realiza transiciones y acercamientos fluidos (*pan & zoom*) hacia los centros de gravedad de las 5 narrativas temáticas del dataset.
5. **Top Nodos Hubs:** Zoom interactivo sobre las 20 cuentas con mayor centralidad, identificadas como las que más impulsan las narrativas del debate.
6. **Protección por Contraseña:** El portal incluye un control de acceso mediante contraseña nativa en Javascript para mantener la privacidad de la investigación.
7. **Interactividad:** Los nodos en Canvas responden al posicionamiento del cursor mostrando información de centralidad y autenticidad en tiempo real.

## Arquitectura del Sitio (100% Auto-contenido)

El sitio ha sido completamente refactorizado para ser autónomo y portátil, agrupando todos sus recursos en un único folder:

```
scrollytelling-site/
├── index.html          # Estructura del sitio con contraseña, narrativa y enlaces CDN
├── README.md           # Guía de documentación y despliegue rápido
├── css/
│   └── style.css       # Estilos (layout sticky, diseño responsivo, legendas y tooltips)
├── js/
│   ├── app.js          # Controlador de scroll (IntersectionObserver puro en ES6)
│   └── network.js      # Motor gráfico (físicas base de D3.js, renderizado en Canvas 2D)
└── visuals/            # DATOS LOCALES (Sitio Autónomo)
    ├── executive_network.json   # generado por scripts/export_executive_json.py
    └── wc_*.png                 # nubes de palabras, generadas por scripts/generate_narrative_clouds.py
```

## Optimización de Rendimiento

- **D3 + Canvas 2D:** En lugar de renderizar miles de elementos SVG (que colapsarían el rendimiento de los navegadores), se utiliza un lienzo de `canvas` para asegurar animaciones y transiciones a 60 FPS en cualquier dispositivo.
- **Físicas Pre-calculadas (Layout Estático):** En lugar de correr la pesada simulación de fuerzas físicas de D3.js de forma continua durante el desplazamiento (lo cual causa tirones de rendimiento), la simulación se ejecuta de forma estática (pre-cálculo de 300 ticks) al cargar la página y luego se "congela" la geometría de coordenadas. Esto hace que el desplazamiento del usuario por los pasos sea inmediato, suave e increíblemente fluido.

## Cómo Visualizar Localmente

Debido a restricciones de seguridad del navegador para cargar archivos JSON locales mediante peticiones HTTP virtuales (`fetch`), el sitio debe ser levantado utilizando un servidor web simple de desarrollo.

Puedes ejecutar cualquiera de las siguientes opciones desde la raíz del proyecto:

### Opción 1: Servidor Python (Recomendado)
Abre tu terminal y ejecuta:
```bash
python3 -m http.server 8000
```
Luego, abre tu navegador e ingresa a: `http://localhost:8000/scrollytelling-site/`

### Opción 2: VS Code Live Server
Si usas VS Code, haz clic derecho sobre `scrollytelling-site/index.html` y selecciona **"Open with Live Server"**.

## Despliegue en GitHub Pages (Guía de Git)

Dado que la carpeta `scrollytelling-site/` es ahora **100% independiente y auto-contenida**, puedes elegir empujar únicamente este directorio a tu repositorio de GitHub para publicar el sitio de forma inmediata.

### Pasos para publicar usando GitHub Pages:

#### Paso 1: Inicializar y subir el folder a GitHub
Abre tu terminal y ejecuta los siguientes comandos:

```bash
# 1. Asegúrate de estar en el directorio de la aplicación
cd scrollytelling-site/

# 2. Inicializa un nuevo repositorio de Git local (si deseas subir solo esta carpeta)
git init

# 3. Agrega todos los archivos locales del sitio (HTML, CSS, JS, visuals)
git add .

# 4. Crea tu primer commit
git commit -m "feat: implementar portal interactivo de scrollytelling con protección"

# 5. Crea una rama principal
git branch -M main

# 6. Vincula tu repositorio remoto de GitHub (reemplaza con tu URL real)
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git

# 7. Empuja los archivos a GitHub
git push -u origin main
```

#### Paso 2: Activar GitHub Pages en el panel
1. Ve a tu repositorio en **GitHub.com**.
2. Haz clic en la pestaña **Settings** (Ajustes) en el menú superior.
3. En la barra lateral izquierda, selecciona la opción **Pages**.
4. En la sección **Build and deployment**:
   - En **Source**, asegúrate de que esté seleccionado `Deploy from a branch`.
   - En **Branch**, selecciona la rama `main` y la carpeta `/ (root)`.
5. Haz clic en **Save** (Guardar).

¡Tu sitio estará publicado y en línea en unos minutos bajo la URL `https://TU_USUARIO.github.io/TU_REPOSITORIO/`! Al ingresar, te solicitará la contraseña de acceso: `pikachu`.
