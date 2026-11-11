from cip_agents.library_client import LibraryUnavailableError
from cip_agents.models import ModelError
from cip_agents.offline import OfflineModel
from cip_agents.schemas import (
    ClaimJudgment,
    DraftedParagraph,
    DraftedSentence,
    PlanOutput,
    RepairedClaim,
    RepairOutput,
    SectionDraftOutput,
    SectionOutline,
    VerificationOutput,
)
from cip_contracts import Draft


def completed_draft(events: list[dict]) -> Draft:
    assert events[-1]["type"] == "job.completed", events[-1]
    return Draft.model_validate(events[-1]["data"]["draft"])


class ScriptedModel(OfflineModel):
    provider = "scripted"

    def __init__(self) -> None:
        self.repair_calls = 0

    async def plan(self, request):
        return PlanOutput(
            title="Estado del arte: sequía en papa",
            sections=[
                SectionOutline(heading="Fisiología", goal="Mecanismos", queries=["stomatal conductance abscisic acid"])
            ],
        )

    async def write(self, request, plan, evidence):
        return SectionDraftOutput(
            paragraphs=[
                DraftedParagraph(
                    sentences=[
                        DraftedSentence(text="La conductancia estomática cayó 58 %.", evidence=["E1"]),
                        DraftedSentence(text="La conductancia cayó 90 % en todos los clones.", evidence=["[E1]"]),
                        DraftedSentence(text="Una afirmación inventada sin fuente.", evidence=["E99"]),
                        DraftedSentence(text="Otra afirmación sin respaldo.", evidence=[]),
                    ]
                )
            ]
        )

    async def verify(self, language, claims):
        return VerificationOutput(
            judgments=[ClaimJudgment(claim_id=claim.claim_id, verdict="supported", rationale="") for claim in claims]
        )

    async def repair(self, language, claims, evidence):
        self.repair_calls += 1
        first, second = (claim for claim, _ in claims)
        return RepairOutput(
            claims=[
                RepairedClaim(
                    claim_id=first.claim_id,
                    action="rewrite",
                    text="El ABA foliar aumentó durante el déficit hídrico.",
                    evidence=["E1"],
                ),
                RepairedClaim(claim_id=second.claim_id, action="drop", text="", evidence=[]),
            ]
        )


class FailingModel(OfflineModel):
    async def plan(self, request):
        raise ModelError("Hay mucha demanda en el servicio de IA.", "rate_limited")


def test_offline_pipeline_streams_progress_and_returns_grounded_draft(make_client, run):
    events = run(make_client())
    kinds = [event["type"] for event in events]

    assert kinds[0] == "job.started"
    assert kinds.count("section.planned") == 5
    assert "source.found" in kinds
    assert "claim.checked" in kinds
    draft = completed_draft(events)
    assert draft.title == "Estado del arte: tolerancia a sequía en papa"
    assert draft.sections
    for claim in draft.claims():
        assert all(link.passage_id in draft.evidence for link in claim.citations)
    assert {reference.paper_id for reference in draft.references} == {
        passage.paper_id for passage in draft.evidence.values()
    }


def test_sections_are_researched_in_parallel_with_english_queries(make_client, run, library_factory):
    library = library_factory()
    run(make_client(library=library))

    assert len(library.requests) == 5
    assert all("drought" in " ".join(request.queries) for request in library.requests)


def test_guardrails_drop_invented_citations_flag_numbers_and_repair(make_client, run):
    model = ScriptedModel()
    events = run(make_client(model=model))
    draft = completed_draft(events)
    claims = {claim.text: claim for claim in draft.claims()}
    warnings = [event["message"] for event in events if event["type"] == "warning"]

    assert claims["La conductancia estomática cayó 58 %."].verdict == "supported"
    partial = claims["La conductancia cayó 90 % en todos los clones."]
    assert partial.verdict == "partial"
    assert "90" in partial.rationale
    assert "El ABA foliar aumentó durante el déficit hídrico." in claims
    assert "Otra afirmación sin respaldo." not in claims
    assert model.repair_calls == 1
    assert any("Descarté 1 citas" in warning for warning in warnings)


def test_empty_library_results_fail_with_guidance(make_client, run, library_factory):
    events = run(make_client(library=library_factory(passages=[])))

    assert events[-1]["type"] == "job.failed"
    assert events[-1]["data"]["code"] == "no_evidence"
    assert sum(event["type"] == "warning" for event in events) == 5


def test_library_outage_is_reported(make_client, run, library_factory):
    library = library_factory(error=LibraryUnavailableError("No pude consultar tu biblioteca de PDFs."))

    events = run(make_client(library=library))

    assert events[-1]["data"]["code"] == "library_unavailable"


def test_model_errors_are_translated_for_the_researcher(make_client, run):
    events = run(make_client(model=FailingModel()))

    assert events[-1] == events[-1] | {"type": "job.failed", "message": "Hay mucha demanda en el servicio de IA."}
    assert events[-1]["data"]["code"] == "rate_limited"


def test_health_reports_provider_and_model_routing(make_client):
    body = make_client().get("/health").json()

    assert body["provider"] == "offline"
    assert set(body["models"]) == {"planner", "writer", "verifier"}
