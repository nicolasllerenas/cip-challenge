import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from cip_contracts import (
    Claim,
    Draft,
    DraftRequest,
    EventType,
    JobEvent,
    Paragraph,
    Passage,
    SearchRequest,
    Section,
    Stage,
    Verdict,
)
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from cip_agents.config import Settings
from cip_agents.evidence import (
    build_references,
    cited_passages,
    label_evidence,
    resolve_citations,
    short_citation,
    unsupported_numbers,
)
from cip_agents.library_client import Library
from cip_agents.models import LanguageModel
from cip_agents.prompts import SECTIONS_BY_LENGTH
from cip_agents.schemas import ClaimToCheck, EvidenceItem, SectionDraftOutput, SectionPlan

NO_CITATION = "La afirmación no cita ninguna fuente de tu biblioteca."


class NoEvidenceError(Exception):
    pass


@dataclass
class SectionResult:
    plan: SectionPlan
    section: Section | None
    evidence: list[Passage]
    warnings: list[str] = field(default_factory=list)


class DraftState(TypedDict, total=False):
    request: DraftRequest
    title: str
    plan: list[SectionPlan]
    results: Annotated[list[SectionResult], operator.add]
    draft: Draft


class SectionState(TypedDict, total=False):
    request: DraftRequest
    plan: SectionPlan
    evidence: list[Passage]
    section: Section | None
    pending: list[str]
    repairs: int
    warnings: list[str]
    results: Annotated[list[SectionResult], operator.add]


class SectionOutput(TypedDict):
    results: Annotated[list[SectionResult], operator.add]


def emit(kind: EventType, message: str, stage: Stage, **data: Any) -> None:
    get_stream_writer()(JobEvent(type=kind, stage=stage, message=message, data=data))


def evidence_items(by_label: dict[str, Passage]) -> list[EvidenceItem]:
    return [
        EvidenceItem(
            label=label,
            citation=short_citation(passage.metadata, passage.file_name),
            page=passage.page,
            text=passage.text,
        )
        for label, passage in by_label.items()
    ]


def build_section(plan: SectionPlan, output: SectionDraftOutput, by_label: dict[str, Passage]) -> tuple[Section, int]:
    paragraphs, invalid, counter = [], 0, 0
    for drafted in output.paragraphs:
        claims = []
        for sentence in drafted.sentences:
            citations, rejected = resolve_citations(sentence.evidence, by_label)
            invalid += rejected
            counter += 1
            claims.append(Claim(claim_id=f"{plan.section_id}-c{counter}", text=sentence.text, citations=citations))
        if claims:
            paragraphs.append(Paragraph(claims=claims))
    return Section(section_id=plan.section_id, heading=plan.heading, paragraphs=paragraphs), invalid


def replace_claims(section: Section, updates: dict[str, Claim | None]) -> Section:
    paragraphs = []
    for paragraph in section.paragraphs:
        claims = [updates.get(claim.claim_id, claim) for claim in paragraph.claims]
        kept = [claim for claim in claims if claim is not None]
        if kept:
            paragraphs.append(Paragraph(claims=kept))
    return section.model_copy(update={"paragraphs": paragraphs})


def without_repetitions(sections: list[Section]) -> list[Section]:
    seen: set[str] = set()
    unique = []
    for section in sections:
        updates: dict[str, Claim | None] = {}
        for claim in section.claims():
            fingerprint = " ".join(claim.text.lower().split())
            if fingerprint in seen:
                updates[claim.claim_id] = None
            seen.add(fingerprint)
        cleaned = replace_claims(section, updates)
        if cleaned.claims():
            unique.append(cleaned)
    return unique


def build_graph(model: LanguageModel, library: Library, settings: Settings):
    async def plan(state: DraftState) -> DraftState:
        request = state["request"]
        emit(EventType.STAGE_STARTED, "Planificando la estructura del documento", Stage.PLANNING)
        output = await model.plan(request)
        limit = SECTIONS_BY_LENGTH[request.options.length]
        sections = [
            SectionPlan(section_id=f"s{index}", heading=item.heading, goal=item.goal, queries=item.queries[:3])
            for index, item in enumerate(output.sections[:limit], start=1)
        ]
        for section in sections:
            emit(
                EventType.SECTION_PLANNED,
                section.heading,
                Stage.PLANNING,
                section_id=section.section_id,
                goal=section.goal,
                queries=section.queries,
            )
        emit(EventType.STAGE_COMPLETED, f"Estructura lista: {len(sections)} secciones", Stage.PLANNING)
        return {"title": output.title, "plan": sections}

    def fan_out(state: DraftState) -> list[Send]:
        return [
            Send("draft_section", {"request": state["request"], "plan": section, "repairs": 0, "warnings": []})
            for section in state["plan"]
        ]

    async def retrieve(state: SectionState) -> SectionState:
        request, section = state["request"], state["plan"]
        emit(
            EventType.STAGE_STARTED,
            f"Buscando evidencia para «{section.heading}»",
            Stage.RETRIEVING,
            section_id=section.section_id,
        )
        passages = await library.search(
            request.library_id,
            SearchRequest(
                queries=section.queries,
                top_k=settings.evidence_per_section,
                per_paper=2,
                year_from=request.options.year_from,
            ),
        )
        for passage in {passage.paper_id: passage for passage in passages}.values():
            emit(
                EventType.SOURCE_FOUND,
                passage.metadata.title or passage.file_name,
                Stage.RETRIEVING,
                section_id=section.section_id,
                paper_id=passage.paper_id,
                citation=short_citation(passage.metadata, passage.file_name),
                page=passage.page,
            )
        return {"evidence": passages}

    async def write(state: SectionState) -> SectionState:
        section_plan = state["plan"]
        emit(
            EventType.STAGE_STARTED,
            f"Redactando «{section_plan.heading}»",
            Stage.WRITING,
            section_id=section_plan.section_id,
        )
        by_label = label_evidence(state["evidence"])
        output = await model.write(state["request"], section_plan, evidence_items(by_label))
        section, invalid = build_section(section_plan, output, by_label)
        warnings = list(state.get("warnings", []))
        if invalid:
            warnings.append(f"Descarté {invalid} citas que no correspondían a fuentes de tu biblioteca.")
        first = next(iter(section.claims()), None)
        emit(
            EventType.SECTION_DRAFTED,
            section_plan.heading,
            Stage.WRITING,
            section_id=section_plan.section_id,
            claims=len(section.claims()),
            preview=first.text if first else "",
        )
        return {"section": section, "pending": [claim.claim_id for claim in section.claims()], "warnings": warnings}

    async def verify(state: SectionState) -> SectionState:
        section, request = state["section"], state["request"]
        by_passage = {passage.passage_id: passage for passage in state["evidence"]}
        pending_ids = set(state["pending"])
        pending = [claim for claim in section.claims() if claim.claim_id in pending_ids]
        emit(
            EventType.STAGE_STARTED,
            f"Verificando {len(pending)} citas de «{section.heading}»",
            Stage.VERIFYING,
            section_id=section.section_id,
        )
        updates: dict[str, Claim | None] = {
            claim.claim_id: claim.model_copy(update={"verdict": Verdict.UNSUPPORTED, "rationale": NO_CITATION})
            for claim in pending
            if not claim.citations
        }
        to_check = [
            ClaimToCheck(
                claim_id=claim.claim_id,
                text=claim.text,
                evidence=evidence_items(
                    {f"E{i}": by_passage[link.passage_id] for i, link in enumerate(claim.citations, 1)}
                ),
            )
            for claim in pending
            if claim.citations
        ]
        if to_check:
            judgments = {
                item.claim_id: item for item in (await model.verify(request.options.language, to_check)).judgments
            }
            for claim in pending:
                judgment = judgments.get(claim.claim_id)
                if judgment is None or not claim.citations:
                    continue
                verdict, rationale = Verdict(judgment.verdict), judgment.rationale
                missing = unsupported_numbers(
                    claim.text, [by_passage[link.passage_id].text for link in claim.citations]
                )
                if verdict == Verdict.SUPPORTED and missing:
                    verdict = Verdict.PARTIAL
                    rationale = f"Los valores {', '.join(missing)} no aparecen en la fuente citada."
                updates[claim.claim_id] = claim.model_copy(update={"verdict": verdict, "rationale": rationale})
        checked = replace_claims(section, updates)
        verdicts = [claim.verdict for claim in checked.claims()]
        emit(
            EventType.CLAIM_CHECKED,
            f"Verifiqué las citas de «{section.heading}»",
            Stage.VERIFYING,
            section_id=section.section_id,
            supported=verdicts.count(Verdict.SUPPORTED),
            partial=verdicts.count(Verdict.PARTIAL),
            unsupported=verdicts.count(Verdict.UNSUPPORTED),
        )
        return {"section": checked, "pending": []}

    async def repair(state: SectionState) -> SectionState:
        section, request = state["section"], state["request"]
        by_label = label_evidence(state["evidence"])
        items = evidence_items(by_label)
        item_for_passage = {passage.passage_id: item for item, passage in zip(items, by_label.values(), strict=True)}
        flagged = [claim for claim in section.claims() if claim.verdict == Verdict.UNSUPPORTED]
        targets = [
            (
                ClaimToCheck(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    evidence=[item_for_passage[link.passage_id] for link in claim.citations],
                ),
                claim.rationale,
            )
            for claim in flagged
        ]
        output = await model.repair(request.options.language, targets, items)
        updates: dict[str, Claim | None] = {claim.claim_id: None for claim in flagged}
        rewritten = []
        for item in output.claims:
            if item.action == "rewrite" and item.text and item.claim_id in updates:
                citations, _ = resolve_citations(item.evidence, by_label)
                updates[item.claim_id] = Claim(claim_id=item.claim_id, text=item.text, citations=citations)
                rewritten.append(item.claim_id)
        emit(
            EventType.PROGRESS,
            f"Corregí {len(rewritten)} y descarté {len(flagged) - len(rewritten)} afirmaciones sin respaldo",
            Stage.VERIFYING,
            section_id=section.section_id,
        )
        return {"section": replace_claims(section, updates), "pending": rewritten, "repairs": state["repairs"] + 1}

    def finish(state: SectionState) -> SectionState:
        section_plan, section = state["plan"], state.get("section")
        warnings = list(state.get("warnings", []))
        if section is None or not section.claims():
            warnings.append(f"No encontré evidencia suficiente en tu biblioteca para «{section_plan.heading}».")
        return {"results": [SectionResult(section_plan, section, state.get("evidence", []), warnings)]}

    def after_retrieve(state: SectionState) -> str:
        return "write" if state["evidence"] else "finish"

    def after_verify(state: SectionState) -> str:
        flagged = any(claim.verdict == Verdict.UNSUPPORTED for claim in state["section"].claims())
        return "repair" if flagged and state["repairs"] < settings.max_repairs else "finish"

    def after_repair(state: SectionState) -> str:
        return "verify" if state["pending"] else "finish"

    section_graph = StateGraph(SectionState, output_schema=SectionOutput)
    for node in (retrieve, write, verify, repair, finish):
        section_graph.add_node(node.__name__, node)
    section_graph.add_edge(START, "retrieve")
    section_graph.add_conditional_edges("retrieve", after_retrieve, ["write", "finish"])
    section_graph.add_edge("write", "verify")
    section_graph.add_conditional_edges("verify", after_verify, ["repair", "finish"])
    section_graph.add_conditional_edges("repair", after_repair, ["verify", "finish"])
    section_graph.add_edge("finish", END)

    async def assemble(state: DraftState) -> DraftState:
        request = state["request"]
        emit(EventType.STAGE_STARTED, "Armando el documento y la bibliografía", Stage.ASSEMBLING)
        order = {section.section_id: index for index, section in enumerate(state["plan"])}
        results = sorted(state.get("results", []), key=lambda result: order[result.plan.section_id])
        for result in results:
            for warning in result.warnings:
                emit(EventType.WARNING, warning, Stage.ASSEMBLING, section_id=result.plan.section_id)
        sections = without_repetitions([result.section for result in results if result.section])
        if not sections:
            raise NoEvidenceError(
                "No encontré en tu biblioteca artículos que respalden este tema. "
                "Revisa que la carpeta sea la correcta o reformula la solicitud con otros términos."
            )
        evidence = {passage.passage_id: passage for result in results for passage in result.evidence}
        cited = cited_passages(sections, evidence)
        draft = Draft(
            draft_id=uuid4().hex,
            library_id=request.library_id,
            prompt=request.prompt,
            title=state["title"],
            language=request.options.language,
            sections=sections,
            references=build_references(list(cited.values())),
            evidence=cited,
            models=model.assignments(),
        )
        emit(EventType.STAGE_COMPLETED, f"Documento armado con {draft.stats.sources} fuentes", Stage.ASSEMBLING)
        return {"draft": draft}

    builder = StateGraph(DraftState)
    builder.add_node("plan", plan)
    builder.add_node("draft_section", section_graph.compile())
    builder.add_node("assemble", assemble)
    builder.add_edge(START, "plan")
    builder.add_conditional_edges("plan", fan_out, ["draft_section"])
    builder.add_edge("draft_section", "assemble")
    builder.add_edge("assemble", END)
    return builder.compile()
