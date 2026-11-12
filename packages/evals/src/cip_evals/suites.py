import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import httpx
import pandas as pd
from cip_agents.api import create_app as create_agents
from cip_agents.config import Settings as AgentsSettings
from cip_agents.evidence import number_guardrail
from cip_agents.library_client import HttpLibrary
from cip_agents.models import LanguageModel
from cip_agents.schemas import ClaimToCheck, EvidenceItem
from cip_contracts import Draft, Verdict
from cip_library.api import create_app as create_library
from cip_library.config import Settings as LibrarySettings
from cip_testkit import build_corpus
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cip_evals.gold import RetrievalCase, VerifierCase, gold_citation, gold_page
from cip_evals.metrics import rank_of

PROMPT = "Redáctame un borrador del estado del arte sobre tolerancia a sequía en papa, con citas y bibliografía."


@dataclass
class Workspace:
    app: FastAPI
    client: TestClient
    library_id: str


def prepare(root: Path, embedder: str) -> Workspace:
    corpus = root / "corpus"
    build_corpus(corpus)
    app = create_library(LibrarySettings(data_dir=root / "library", embedder=embedder))
    client = TestClient(app)
    library_id = client.post("/libraries", json={"path": str(corpus)}).json()["library_id"]
    client.post(f"/libraries/{library_id}/ingest")
    return Workspace(app, client, library_id)


def retrieval_suite(workspace: Workspace, cases: list[RetrievalCase], k: int) -> pd.DataFrame:
    rows = []
    for case in cases:
        passages = workspace.client.post(
            f"/libraries/{workspace.library_id}/search",
            json={"queries": [case.query], "top_k": k, "per_paper": 1},
        ).json()
        retrieved = [passage["file_name"].removesuffix(".pdf") for passage in passages]
        rows.append(
            {
                "query": case.query,
                "language": case.language,
                "expected": case.expected,
                "rank": rank_of(case.expected, retrieved),
                "top_1": retrieved[0] if retrieved else "",
            }
        )
    return pd.DataFrame(rows).astype({"rank": "Float64"})


async def _verify(model: LanguageModel, cases: list[VerifierCase]) -> pd.DataFrame:
    claims = [
        ClaimToCheck(
            claim_id=f"v{index}",
            text=case.claim,
            evidence=[
                EvidenceItem(
                    label="E1",
                    citation=gold_citation(case.paper),
                    page=case.page,
                    text=gold_page(case.paper, case.page),
                )
            ],
        )
        for index, case in enumerate(cases)
    ]
    judgments = {item.claim_id: item for item in (await model.verify("es", claims)).judgments}
    rows = []
    for index, case in enumerate(cases):
        judgment = judgments.get(f"v{index}")
        raw = Verdict(judgment.verdict) if judgment else Verdict.UNSUPPORTED
        final, _ = number_guardrail(
            raw, judgment.rationale if judgment else "", case.claim, [gold_page(case.paper, case.page)]
        )
        rows.append(
            {
                "claim": case.claim,
                "note": case.note,
                "expected": case.expected,
                "model": raw.value,
                "predicted": final.value,
            }
        )
    return pd.DataFrame(rows)


def verifier_suite(model: LanguageModel, cases: list[VerifierCase]) -> pd.DataFrame:
    return asyncio.run(_verify(model, cases))


def pipeline_suite(workspace: Workspace, model: LanguageModel) -> dict:
    library = HttpLibrary("http://library", transport=httpx.ASGITransport(app=workspace.app))
    agents = create_agents(AgentsSettings(llm_provider="offline"), model, library)
    with TestClient(agents) as client:
        response = client.post("/runs", json={"library_id": workspace.library_id, "prompt": PROMPT})
    events = [json.loads(line) for line in response.text.splitlines() if line]
    final = events[-1]
    if final["type"] != "job.completed":
        return {"completed": False, "message": final["message"], "grounded": False, "supported_ratio": 0.0}
    draft = Draft.model_validate(final["data"]["draft"])
    claims = draft.claims()
    stats = draft.stats
    return {
        "completed": True,
        "sections": len(draft.sections),
        "claims": stats.claims,
        "supported_ratio": round(stats.supported / max(stats.claims, 1), 3),
        "pending_review": stats.pending_review,
        "citations_per_claim": round(mean(len(claim.citations) for claim in claims), 2),
        "sources": stats.sources,
        "grounded": all(link.passage_id in draft.evidence for claim in claims for link in claim.citations),
        "events": len(events),
    }
