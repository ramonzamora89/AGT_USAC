# Proyecto AGT_USAC - Mandatos y Convenciones (GEMINI.md)

## Contexto
Este archivo contiene las instrucciones de alto nivel para el mantenimiento y evolución del proyecto de análisis de la red de conversación digital sobre Ana Glenda Tager, USAC, Ricardo Quiñonez y el plan de infraestructura.

## Mandatos Principales
1. **Neutralidad de Lenguaje**: Los reportes deben utilizar lenguaje descriptivo y objetivo. Los adjetivos se reservan exclusivamente para las citas textuales.
2. **Capitalización en Español**: Los títulos de temas y narrativas deben seguir la norma: mayúscula inicial solo en la primera palabra (ej: "Resistencia al desarrollo").
3. **Formatos de Salida**: Cada actualización de datos debe resultar en una regeneración sincronizada del reporte en .md, .html y .pdf.
4. **Protección de Datos**: No mencionar figuras políticas o partidos a menos que tengan una persistencia demostrada en el dataset (mínimo 5% de menciones o relevancia narrativa crítica).
5. **Reglas de citas textuales**: Las citas deben ser oraciones completas, de 5 o más palabras. Incluir signos de puntuación.
6. **Separación de Medios**: Las cuentas de medios de comunicación se identifican y verifican a mano; se documentan en `Dataset/account_categories.csv`. El resto de las cuentas no se clasifica individualmente — se agrupan por narrativa temática.
7. **Selección de semillas**: Las publicaciones semilla del análisis provienen de Brand24, filtradas por un alcance mayor a 20,000 vistas.
8. **Actores clave**: Se identifican las 20 cuentas con mayor centralidad de la red como las que más impulsan las narrativas del debate.

## Convenciones de Desarrollo
- **Fuentes**: Siempre utilizar 'Poppins' para reportes ejecutivos y el sitio de scrollytelling.
- **Dimensiones**: El reporte vertical estándar es 1080x1920. El portal web interactivo utiliza un diseño adaptable full-screen de tipo split-pane.
- **Visualización**: Las nubes de palabras deben usar un color propio y consistente por narrativa.
- **Separación Medios/Resto**: En visualizaciones de red, diferenciar visualmente (color o forma de nodo) las cuentas de medios de comunicación frente al resto de la conversación, agrupada por narrativa.
- **Rendimiento**: El sitio de scrollytelling consume un único JSON precalculado (`executive_network.json`) con los nodos, aristas y narrativas relevantes, para poder cargar y animar la red sin trabarse y hacer zoom fluido a cada clúster.
