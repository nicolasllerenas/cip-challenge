# ADR 0005 · `.docx` con comentarios de revisión y exportación compatible con Pandoc

**Estado:** aceptada

## Contexto
La investigadora edita en Word con su asesor. Lo que no alcanzó a revisar en la app no debe perderse ni pasar como verificado.

## Decisión
python-docx genera el documento con estilos nativos, citas APA 7 y bibliografía; cada afirmación pendiente se resalta y lleva un comentario de Word con el motivo y la fuente con página. Además se exporta Markdown con citas Pandoc y `references.bib`.

## Consecuencias
- El flujo de revisión continúa en la herramienta habitual.
- `pandoc --citeproc` lleva el Markdown a LaTeX (hay prueba automatizada).
- El estilo APA está implementado en código; sumar estilos CSL arbitrarios queda como extensión con citeproc.

## Alternativas
- **Pandoc como generador principal**: excelente para ida y vuelta, pero sin control de los comentarios de Word y con un binario extra en el instalador.
