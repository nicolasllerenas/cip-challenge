# ADR 0003 · LangGraph con ruteo de modelos por tarea

**Estado:** aceptada

## Contexto
Un estado del arte requiere planificar, buscar evidencia, redactar y verificar cada cita. El costo y la latencia importan con 200 artículos, y una cita inventada es inaceptable.

## Decisión
- Grafo de LangGraph: planificador → `Send` por sección a un subgrafo (investigador → redactor → verificador ⟲ reparador) → ensamblador.
- Llamadas con el SDK oficial de Anthropic y salidas estructuradas Pydantic.
- Ruteo: `claude-haiku-5-5` (esfuerzo bajo) para planificar y verificar; `claude-opus-5-5` para redactar (alto) y reparar (medio); escalamiento a Opus si Haiku falla; fallback del servidor en Opus.
- Guardrails deterministas además del verificador: solo se citan pasajes recuperados, se comparan los números y se exige al menos una cita por afirmación.

## Consecuencias
- Las secciones se redactan en paralelo y el progreso sale de cada nodo.
- El costo se concentra en el paso que más aporta (la redacción).
- Existe un modo sin conexión determinista que recorre el mismo grafo para CI y demos.

## Alternativas
- **Un solo prompt largo** con los 200 PDFs: caro, sin trazabilidad por afirmación y difícil de verificar.
- **Agente autónomo con herramientas**: menos predecible para una tarea con estructura conocida.
