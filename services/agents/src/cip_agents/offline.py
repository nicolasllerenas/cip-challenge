import re

from cip_contracts import DraftRequest

from cip_agents.prompts import SECTIONS_BY_LENGTH
from cip_agents.schemas import (
    ClaimJudgment,
    ClaimToCheck,
    DraftedParagraph,
    DraftedSentence,
    EvidenceItem,
    PlanOutput,
    RepairedClaim,
    RepairOutput,
    SectionDraftOutput,
    SectionOutline,
    SectionPlan,
    VerificationOutput,
)

GLOSSARY = {
    "sequía": "drought",
    "sequia": "drought",
    "déficit hídrico": "water deficit",
    "estrés hídrico": "water stress",
    "tolerancia": "tolerance",
    "papa": "potato",
    "rendimiento": "yield",
    "raíz": "root",
    "raíces": "roots",
    "mejoramiento": "breeding",
    "tizón": "late blight",
    "calor": "heat",
}
FACETS = [
    ("Contexto y relevancia", "Por qué el problema importa para la producción", ["{topic} constraint production"]),
    (
        "Respuestas fisiológicas",
        "Qué mecanismos fisiológicos explican la tolerancia",
        ["{topic} stomatal conductance abscisic acid", "{topic} osmotic adjustment proline root water uptake"],
    ),
    (
        "Bases genéticas",
        "Qué genes, QTL y marcadores se han asociado al rasgo",
        ["{topic} QTL candidate genes markers heritability"],
    ),
    (
        "Estrategias de mejoramiento y fenotipado",
        "Cómo se está seleccionando y evaluando el rasgo",
        ["{topic} breeding wild relatives participatory selection", "{topic} phenotyping thermal imagery UAV"],
    ),
    (
        "Brechas y perspectivas",
        "Qué falta validar y hacia dónde avanzar",
        ["{topic} limitations validation must be calibrated", "{topic} future breeding cycles"],
    ),
]
FACET_ORDER = {3: [0, 1, 4], 5: [0, 1, 2, 3, 4], 7: [0, 1, 2, 3, 4]}
SENTENCE = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"[a-záéíóúñ]+")


def topic_of(prompt: str) -> tuple[str, str]:
    lowered = prompt.lower()
    match = re.search(r"sobre (.+?)(?:,| con | en un|\.|$)", lowered)
    topic = (match.group(1) if match else lowered).strip()
    english = topic
    for spanish, translation in sorted(GLOSSARY.items(), key=lambda item: -len(item[0])):
        english = english.replace(spanish, translation)
    english = " ".join(word for word in english.split() if word not in {"a", "en", "de", "la", "el"})
    return topic, english


def synthesize(sentences: list[DraftedSentence]) -> list[DraftedSentence]:
    if len(sentences) < 3:
        return sentences
    first, second, third = sentences
    merged = f"{second.text.rstrip('.')}; in addition, {third.text[0].lower()}{third.text[1:]}"
    return [first, DraftedSentence(text=merged, evidence=second.evidence)]


def overlap(left: str, right: str) -> float:
    left_words, right_words = set(WORD.findall(left.lower())), set(WORD.findall(right.lower()))
    return len(left_words & right_words) / max(len(left_words), 1)


class OfflineModel:
    provider = "offline"

    def assignments(self) -> dict[str, str]:
        return {"planner": "demo-offline", "writer": "demo-offline", "verifier": "demo-offline"}

    async def plan(self, request: DraftRequest) -> PlanOutput:
        topic, english = topic_of(request.prompt)
        facets = [FACETS[index] for index in FACET_ORDER[SECTIONS_BY_LENGTH[request.options.length]]]
        return PlanOutput(
            title=f"Estado del arte: {topic}",
            sections=[
                SectionOutline(heading=heading, goal=goal, queries=[query.format(topic=english) for query in queries])
                for heading, goal, queries in facets
            ],
        )

    async def write(self, request: DraftRequest, plan: SectionPlan, evidence: list[EvidenceItem]) -> SectionDraftOutput:
        focus = " ".join(plan.queries)
        sentences = []
        for item in evidence[:6]:
            first_author = item.citation.split(",")[0].split()[0]
            candidates = [
                sentence
                for sentence in SENTENCE.split(item.text)
                if 40 < len(sentence) < 280 and first_author not in sentence
            ]
            if candidates:
                best = max(candidates, key=lambda sentence: overlap(focus, sentence))
                sentences.append(DraftedSentence(text=best, evidence=[item.label]))
        chunks = [sentences[index : index + 3] for index in range(0, len(sentences), 3)]
        paragraphs = [synthesize(chunk) if position == 0 else chunk for position, chunk in enumerate(chunks)]
        return SectionDraftOutput(paragraphs=[DraftedParagraph(sentences=chunk) for chunk in paragraphs])

    async def verify(self, language: str, claims: list[ClaimToCheck]) -> VerificationOutput:
        judgments = []
        for claim in claims:
            support = max((overlap(claim.text, item.text) for item in claim.evidence), default=0.0)
            verdict = "supported" if support >= 0.8 else "partial" if support >= 0.4 else "unsupported"
            rationale = "" if verdict == "supported" else "Coincidencia parcial con el pasaje citado."
            judgments.append(ClaimJudgment(claim_id=claim.claim_id, verdict=verdict, rationale=rationale))
        return VerificationOutput(judgments=judgments)

    async def repair(
        self, language: str, claims: list[tuple[ClaimToCheck, str]], evidence: list[EvidenceItem]
    ) -> RepairOutput:
        return RepairOutput(
            claims=[RepairedClaim(claim_id=claim.claim_id, action="drop", text="", evidence=[]) for claim, _ in claims]
        )
