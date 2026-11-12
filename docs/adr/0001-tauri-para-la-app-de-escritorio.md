# ADR 0001 · Tauri 2 para la app de escritorio

**Estado:** aceptada

## Contexto
La app actual del CIP está en Rust y el reto valora GPUI. El peso de la evaluación está en la UX: había que iterar pantallas rápido, verificarlas visualmente y cumplir con la accesibilidad (lectores de pantalla, teclado, escalado).

## Decisión
Tauri 2: un núcleo en Rust (ventana nativa, diálogos, ciclo de vida del sidecar) y la interfaz en React/TypeScript sobre WebView2.

## Consecuencias
- Semántica ARIA y herramientas de accesibilidad maduras; las mismas pantallas se prueban en navegador con Playwright.
- Empaquetado NSIS/MSI y *sidecar* incluidos en el bundler.
- La app solo depende del contrato REST + SSE del gateway: migrar la interfaz a **GPUI** no cambia el backend y puede hacerse pantalla por pantalla.

## Alternativas
- **GPUI**: más nativo y alineado con la app actual, pero con menos componentes de accesibilidad e iteración visual más lenta para un prototipo. Queda como camino de producción.
- **Electron**: binario más pesado y sin núcleo en Rust.
