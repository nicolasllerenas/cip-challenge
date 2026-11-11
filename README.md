# Asistente de Investigación CIP

Propuesta para el reto técnico del CIP: una investigadora selecciona su carpeta de PDFs y pide
*“Redáctame un borrador del estado del arte sobre tolerancia a sequía en papa, con citas y bibliografía,
en un .docx que pueda editar.”* Este repositorio muestra cómo fluye esa solicitud de punta a punta.

## Estructura

```
apps/desktop        App de escritorio (Tauri 2 · Rust · React)
services/gateway    BFF: REST + SSE hacia la app
services/library    Ingesta de PDFs y recuperación híbrida (RAG)
services/agents     Orquestación multiagente con LangGraph
services/documents  Generación de .docx, Markdown y BibTeX
packages/contracts  Contratos Pydantic compartidos
board               Tablero de Excalidraw (wireframes + arquitectura)
docs                UX, arquitectura, ADRs y guion del video
```

## Desarrollo

```bash
uv sync --all-packages
uv run pytest
```
