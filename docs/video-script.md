# Guion del video (Loom, máximo 5:00)

Graba la pantalla con la cámara activada. Ten abierto el tablero en Excalidraw (`board/cip-research-assistant.excalidraw`) y, si quieres mostrarla en vivo, la app con `make dev`.

> Regla de tiempos: **≈ 3:00 en UX** (el corazón del reto), **≈ 1:20 en arquitectura**, **≈ 0:30 en uso de IA**.

> Si muestras la app en modo demostración, dilo una vez al abrirla: *“Esta demo corre en modo demostración: sin IA externa ni costo, arma el borrador con frases de los PDFs de un corpus de prueba. En producción, el mismo flujo redacta con Claude.”*

| Tiempo | Dónde | Qué decir |
|---|---|---|
| **0:00 – 0:20** | Cámara + encabezado del tablero | “Soy [nombre]. Diseñé cómo una investigadora en mejoramiento genético de papa pasa de una carpeta con 200 PDFs a un estado del arte en Word con citas que puede verificar. Primero la experiencia, que es donde está el valor; luego la arquitectura.” |
| **0:20 – 0:40** | Tarjetas *Para quién diseño* y *Principios* | “Ella es experta en su tema, no en software. Su miedo es una cita inventada con su nombre. Por eso el principio rector es **confianza antes que magia**: cada afirmación muestra de qué PDF y de qué página sale, y ella decide.” |
| **0:40 – 1:05** | ① Bienvenida → ② ③ Biblioteca | “Antes de pedirle nada le digo qué pasa con sus PDFs. Luego elige su carpeta y ve el avance archivo por archivo. Los problemas van primero y en su idioma: *escaneado → pásalo por OCR*, *falta el año → complétalo aquí*. Puede empezar a escribir sin esperar al 100 %.” |
| **1:05 – 1:25** | ④ Solicitud | “Lo pide como a un colega. Solo hay opciones que cambian el resultado (extensión, idioma, desde qué año) y un recuadro *Qué voy a hacer* que fija método y tiempo esperado.” |
| **1:25 – 1:55** | ⑤ Progreso | “Una espera de minutos se tolera si se ve trabajo real: etapas en lenguaje humano, la estructura del documento aparece primero —si no es su enfoque, cancela— y las fuentes consultadas en vivo. Si se suspende la laptop, al volver no pierde nada.” |
| **1:55 – 2:35** | ⑥ Revisión (la pantalla más importante) | “Aquí está el corazón. El borrador se lee como prosa. Solo lo dudoso va subrayado —punteado si el respaldo es parcial, ondulado si no lo hay— con icono y texto, nunca solo color. Al hacer clic, a la derecha ve el pasaje exacto, la página y por qué lo marqué: *la fuente dice 58 %, no 60 %*; con *Ver en el PDF* abre la página con el pasaje resaltado, sin salir de la app. Acepta, edita o quita, también con el teclado, y puede deshacer. Revisa 7 afirmaciones, no 48.” |
| **2:35 – 2:55** | ⑦ Exportar + Word resultante | “Su trabajo real sigue en Word con su asesor. Exporta un .docx con estilos nativos, APA 7, bibliografía y declaración de uso de IA. Lo que no revisó viaja como comentario de Word con la fuente. No la bloqueo: le informo y ella decide.” |
| **2:55 – 3:10** | Fila roja + accesibilidad | “Cada error dice qué pasó y qué puede hacer: sin conexión, sin evidencia, IA saturada, PDFs dañados. Y es accesible por defecto: tipografía Atkinson Hyperlegible, teclado completo, lector de pantalla, texto escalable.” |
| **3:10 – 3:40** | Parte B · diagrama | “Arquitectura: una app de escritorio en **Tauri** (núcleo en Rust y la interfaz en React) habla con un **gateway**. Detrás hay tres microservicios en Python 3.12: **library** hace la ingesta y el RAG conservando autor, año, DOI y página; **agents** orquesta con **LangGraph**; **documents** genera el .docx. En la laptop corren en un solo proceso empaquetado con PyInstaller, así que el instalador de Windows no pide instalar Python. En servidor, los mismos servicios corren con Docker.” |
| **3:40 – 4:05** | Profundización 1 · comunicación | “Elegí **REST para las órdenes y SSE para los resultados**. El flujo es asimétrico: pocas órdenes y muchos eventos. EventSource reconecta solo y manda `Last-Event-ID`; el gateway guarda los eventos y reenvía lo que faltó. WebSocket me obligaba a reinventar eso, y el polling agrega latencia.” |
| **4:05 – 4:30** | Profundización 2 · multiagente | “Un planificador arma secciones y búsquedas en inglés; por cada sección, en paralelo: investigador, redactor, verificador y un reparador si algo no tiene respaldo. **Ruteo**: Haiku, barato y rápido, para planificar y verificar; Opus para redactar, que es donde se nota la calidad. **Guardrails**: el redactor solo puede citar pasajes recuperados, los números se comparan con la fuente y lo dudoso pasa a revisión humana. Y lo medimos: una evaluación en cada PR mostró que preguntar en español fallaba con embeddings simples (0.25) y funciona con multilingües (1.00).” |
| **4:30 – 4:55** | Cámara | **Uso de IA** (ver abajo, en tus palabras). |
| **4:55 – 5:00** | Cámara | “Todo el diseño parte de lo mismo: que ella pueda confiar en cada cita. Gracias.” |

## Uso de IA (personalízalo antes de grabar)

Dilo con tus palabras y con lo que realmente hiciste. Puntos de partida honestos según cómo se construyó este repositorio:

- **Qué le pedí:** que, a partir del PDF del reto, me ayudara a estructurar la propuesta, a programar el prototipo por microservicios, a generar el tablero de Excalidraw como archivo y a revisar la accesibilidad.
- **Qué acepté:** REST + SSE con reanudación; el índice embebido en SQLite (FTS5 + vectores) en lugar de un servidor vectorial; el ruteo Haiku/Opus; los comentarios de Word para lo pendiente; Tauri para iterar la UX rápido con un núcleo en Rust.
- **Qué descarté y por qué:**
  - **PyMuPDF** → por su licencia AGPL en una app distribuida; usé pypdf.
  - **WebSocket** → bidireccional innecesario, con reconexión manual.
  - **Un “chat” como interfaz principal** → la investigadora necesita revisar un documento, no conversar.
  - **Verificar todas las citas a mano** → solo se revisa lo dudoso.
  - **GPUI en el prototipo** → lo dejé como camino de producción: el contrato REST/SSE no depende del framework de UI.
- **Uso responsable:** no puse datos personales ni confidenciales en los prompts; el corpus de prueba es sintético (DOIs `10.5555`, marcado como no real).

## Checklist antes de grabar

La preparación paso a paso está en [`grabacion.md`](grabacion.md).

- [ ] Cámara activa y la pantalla a 100 % de zoom
- [ ] Tablero abierto en Excalidraw con zoom en el encabezado
- [ ] `make demo` corriendo, con un borrador ya listo en *Mis borradores*
- [ ] Ensayar con cronómetro: si pasas de 5:00, recorta la parte de arquitectura, nunca la de UX
