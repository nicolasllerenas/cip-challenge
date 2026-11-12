# ADR 0002 · REST para comandos y SSE para resultados en vivo

**Estado:** aceptada

## Contexto
La investigadora necesita ver en tiempo real el avance de trabajos que duran minutos, aunque la laptop se suspenda o la app se reinicie.

## Decisión
REST para las órdenes (`POST /v1/drafts`, `PATCH …/claims`, `POST …/cancel`) y SSE para los eventos (`GET /v1/jobs/{id}/events`). El gateway persiste cada evento con un `seq` y lo usa como `id` de SSE; al reconectar, `Last-Event-ID` indica desde dónde reenviar. Entre microservicios, NDJSON en streaming.

## Consecuencias
- Reconexión y reanudación sin código adicional en el cliente (`EventSource`).
- Sirve igual con el backend local o en servidor, y atraviesa proxies corporativos.
- La cancelación cierra el stream aguas arriba, lo que cancela la tarea de LangGraph.

## Alternativas
- **WebSocket**: bidireccional innecesario; reconexión, reanudación y heartbeats manuales.
- **Polling**: latencia y carga.
- **IPC de Tauri**: ataría el backend al proceso de escritorio.
