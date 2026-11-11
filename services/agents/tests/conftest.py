import json
import re

import pytest
from cip_agents.api import create_app
from cip_agents.config import Settings
from cip_agents.offline import OfflineModel
from cip_contracts import Author, PaperMetadata, Passage, SearchRequest
from cip_testkit import PAPERS
from fastapi.testclient import TestClient

WORD = re.compile(r"[a-z0-9]+")


def corpus_passages() -> list[Passage]:
    passages = []
    for paper in PAPERS:
        metadata = PaperMetadata(
            title=paper.title,
            authors=[Author(family=family, given=given) for family, given in paper.authors],
            year=paper.year,
            doi=paper.doi,
            journal=paper.journal,
        )
        for page, paragraphs in enumerate(paper.pages, start=1):
            passages.append(
                Passage(
                    passage_id=f"{paper.slug}:{page}",
                    paper_id=paper.slug,
                    page=page,
                    text=" ".join(paragraphs),
                    file_name=f"{paper.slug}.pdf",
                    metadata=metadata,
                )
            )
    return passages


class FakeLibrary:
    def __init__(self, passages: list[Passage] | None = None, error: Exception | None = None) -> None:
        self.passages = corpus_passages() if passages is None else passages
        self.error = error
        self.requests: list[SearchRequest] = []

    async def search(self, library_id: str, request: SearchRequest) -> list[Passage]:
        self.requests.append(request)
        if self.error:
            raise self.error
        terms = set(WORD.findall(" ".join(request.queries).lower()))
        scored = [(len(terms & set(WORD.findall(p.text.lower()))), p) for p in self.passages]
        ranked = [passage for score, passage in sorted(scored, key=lambda item: -item[0]) if score > 1]
        return ranked[: request.top_k]


PROMPT = "Redáctame un borrador del estado del arte sobre tolerancia a sequía en papa"


@pytest.fixture
def run():
    def execute(client: TestClient) -> list[dict]:
        response = client.post("/runs", json={"library_id": "lib-1", "prompt": PROMPT})
        assert response.status_code == 200
        return [json.loads(line) for line in response.text.splitlines() if line]

    return execute


@pytest.fixture
def library_factory():
    return FakeLibrary


@pytest.fixture
def settings() -> Settings:
    return Settings(llm_provider="offline")


@pytest.fixture
def make_client(settings: Settings):
    def factory(model=None, library=None) -> TestClient:
        return TestClient(create_app(settings, model or OfflineModel(), library or FakeLibrary()))

    return factory
