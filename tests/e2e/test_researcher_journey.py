import json
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from cip_agents.api import create_app as create_agents
from cip_agents.config import Settings as AgentsSettings
from cip_agents.library_client import HttpLibrary
from cip_agents.offline import OfflineModel
from cip_documents.api import create_app as create_documents
from cip_gateway.api import create_app as create_gateway
from cip_gateway.config import Settings as GatewaySettings
from cip_library.api import create_app as create_library
from cip_library.config import Settings as LibrarySettings
from cip_testkit import build_corpus
from docx import Document
from fastapi.testclient import TestClient

PROMPT = (
    "Redáctame un borrador del estado del arte sobre tolerancia a sequía en papa, "
    "con citas y bibliografía, en un .docx que pueda editar."
)


def events_of(client: TestClient, job_id: str) -> list[dict]:
    with client.stream("GET", f"/v1/jobs/{job_id}/events") as response:
        body = "".join(response.iter_text())
    return [
        json.loads(line.removeprefix("data: "))
        for block in body.split("\n\n")
        for line in block.splitlines()
        if line.startswith("data: ")
    ]


@pytest.fixture
def gateway(tmp_path: Path):
    library = httpx.ASGITransport(app=create_library(LibrarySettings(data_dir=tmp_path / "library")))
    agents = create_agents(
        AgentsSettings(llm_provider="offline"), OfflineModel(), HttpLibrary("http://library", transport=library)
    )
    settings = GatewaySettings(
        library_url="http://library",
        agents_url="http://agents",
        documents_url="http://documents",
        data_dir=tmp_path / "gateway",
        exports_dir=tmp_path / "exports",
    )
    mounts = {
        "http://library": library,
        "http://agents": httpx.ASGITransport(app=agents),
        "http://documents": httpx.ASGITransport(app=create_documents()),
    }
    with TestClient(create_gateway(settings, mounts=mounts)) as client:
        yield client


def test_researcher_goes_from_pdf_folder_to_editable_docx(gateway: TestClient, tmp_path: Path):
    corpus = tmp_path / "articulos"
    build_corpus(corpus)

    opened = gateway.post("/v1/libraries", json={"path": str(corpus)}).json()
    ingestion = events_of(gateway, opened["job_id"])
    assert ingestion[-1]["data"]["counts"]["indexed"] == 7
    assert gateway.get("/v1/health").json()["status"] == "ok"

    job = gateway.post("/v1/drafts", json={"library_id": opened["library"]["library_id"], "prompt": PROMPT}).json()
    progress = events_of(gateway, job["job_id"])
    kinds = {event["type"] for event in progress}
    assert {"section.planned", "source.found", "section.drafted", "claim.checked", "job.completed"} <= kinds

    draft_id = progress[-1]["data"]["draft_id"]
    draft = gateway.get(f"/v1/drafts/{draft_id}").json()
    pending = [
        claim
        for section in draft["sections"]
        for paragraph in section["paragraphs"]
        for claim in paragraph["claims"]
        if claim["verdict"] != "supported" and claim["review"] == "pending"
    ]
    assert pending
    for claim in draft["sections"][0]["paragraphs"][0]["claims"]:
        assert all(link["passage_id"] in draft["evidence"] for link in claim["citations"])
    gateway.patch(f"/v1/drafts/{draft_id}/claims/{pending[0]['claim_id']}", json={"action": "accept"})

    exported = gateway.post(f"/v1/drafts/{draft_id}/exports", json={"format": "docx"}).json()
    document = Document(BytesIO(gateway.get(exported["files"][0]["url"]).content))
    headings = [paragraph.text for paragraph in document.paragraphs if paragraph.style.name == "Heading 1"]
    assert headings[-1] == "Referencias"
    assert len(list(document.comments)) == len(pending) - 1
    assert exported["pending_review"] == len(pending) - 1
