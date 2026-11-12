# ADR 0004 · Índice híbrido embebido en SQLite

**Estado:** aceptada

## Contexto
El índice vive en la laptop de la investigadora, debe instalarse sin servicios adicionales y alcanzar para cientos de PDFs.

## Decisión
SQLite con FTS5 (BM25) y los embeddings en la misma base; la búsqueda combina las dos señales con Reciprocal Rank Fusion y limita los pasajes por artículo. Los embeddings están detrás de un puerto: `hashing` para CI y `fastembed` multilingüe en producción.

## Consecuencias
- Un solo archivo portátil, transaccional y sin servidor.
- La búsqueda vectorial es por fuerza bruta en memoria: sobra para miles de pasajes; a escala institucional se cambia el adaptador por Qdrant o LanceDB sin tocar a los agentes.

## Alternativas
- **Chroma / Qdrant / LanceDB**: más dependencias y procesos para el volumen de una sola investigadora.
