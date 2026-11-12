import asyncio
import sys
import time

from cip_contracts import DraftRequest

from cip_agents.config import Settings
from cip_agents.models import AnthropicModel, ModelError
from cip_agents.routing import ModelRouter, Task
from cip_agents.schemas import ClaimToCheck, EvidenceItem, SectionPlan

MISSING_CREDENTIALS = """No encontré una credencial de Anthropic.

1. Crea una API key en https://console.anthropic.com/settings/keys
2. Copia .env.example como .env y pega la key en ANTHROPIC_API_KEY
3. Vuelve a ejecutar: make check-ai"""


SAMPLE_PASSAGES = [
    (
        "Quispe et al., 2019",
        1,
        "Under progressive soil drying, potato plants closed their stomata early: stomatal conductance decreased by "
        "58 percent when soil water content fell below 60 percent of field capacity, before any visible wilting. "
        "Leaf abscisic acid (ABA) concentration increased fourfold during the first week of water deficit.",
    ),
    (
        "Condori y Flores, 2021",
        1,
        "In rhizotron experiments with 24 cultivars, root length density below 40 cm explained 63 percent of the "
        "variation in tuber yield under terminal drought.",
    ),
]


def evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(label=f"E{index}", citation=citation, page=page, text=text)
        for index, (citation, page, text) in enumerate(SAMPLE_PASSAGES, start=1)
    ]


async def run(model: AnthropicModel, router: ModelRouter) -> None:
    request = DraftRequest(library_id="check", prompt="Estado del arte sobre tolerancia a sequía en papa")
    items = evidence()
    started = time.perf_counter()
    plan = await model.plan(request)
    print(f"✓ Planificador ({router.route(Task.PLAN).model}) en {time.perf_counter() - started:.1f} s: «{plan.title}»")
    started = time.perf_counter()
    section = SectionPlan(
        section_id="s1",
        heading="Respuestas fisiológicas",
        goal="Explicar cómo responde la papa al déficit hídrico",
        queries=["stomatal conductance drought potato"],
    )
    draft = await model.write(request, section, items)
    sentences = [sentence for paragraph in draft.paragraphs for sentence in paragraph.sentences]
    elapsed = time.perf_counter() - started
    print(f"✓ Redactor ({router.route(Task.WRITE).model}) en {elapsed:.1f} s: {len(sentences)} afirmaciones")
    if sentences:
        print(f"  «{sentences[0].text}» {sentences[0].evidence}")
    started = time.perf_counter()
    claims = [
        ClaimToCheck(
            claim_id=f"c{index}",
            text=sentence.text,
            evidence=[item for item in items if item.label in sentence.evidence],
        )
        for index, sentence in enumerate(sentences)
    ]
    verdicts = await model.verify("es", claims)
    summary = ", ".join(judgment.verdict for judgment in verdicts.judgments)
    print(f"✓ Verificador ({router.route(Task.VERIFY).model}) en {time.perf_counter() - started:.1f} s: {summary}")


def main() -> int:
    settings = Settings(llm_provider="anthropic")
    if Settings().resolved_provider != "anthropic":
        print(MISSING_CREDENTIALS)
        return 2
    router = ModelRouter(settings)
    print("Probando el modo IA real con una sección de ejemplo (costo aproximado: menos de US$0.10)…")
    try:
        asyncio.run(run(AnthropicModel(router), router))
    except ModelError as error:
        print(f"✗ {error} (código: {error.code})")
        return 1
    print("Todo listo: el asistente usará Claude al ejecutar make demo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
