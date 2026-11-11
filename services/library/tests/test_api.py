import json
from pathlib import Path

from fastapi.testclient import TestClient


def ingest(client: TestClient, library_id: str) -> list[dict]:
    response = client.post(f"/libraries/{library_id}/ingest")
    assert response.status_code == 200
    return [json.loads(line) for line in response.text.splitlines() if line]


def create_library(client: TestClient, folder: Path) -> str:
    response = client.post("/libraries", json={"path": str(folder)})
    assert response.status_code == 201
    return response.json()["library_id"]


def test_ingestion_streams_progress_and_classifies_problem_files(client: TestClient, corpus: Path):
    library_id = create_library(client, corpus)

    events = ingest(client, library_id)

    assert events[0]["type"] == "job.started"
    assert events[-1]["type"] == "job.completed"
    assert events[-1]["data"]["counts"] == {
        "total": 9,
        "indexed": 7,
        "needs_ocr": 1,
        "failed": 1,
        "incomplete_metadata": 0,
    }
    statuses = {event["message"]: event["data"]["paper"]["status"] for event in events[1:-1]}
    assert statuses["scanned-field-notebook.pdf"] == "needs_ocr"
    assert statuses["corrupted-download.pdf"] == "failed"


def test_extracted_metadata_is_ready_for_citation(client: TestClient, corpus: Path):
    library_id = create_library(client, corpus)
    ingest(client, library_id)

    papers = {paper["file_name"]: paper for paper in client.get(f"/libraries/{library_id}").json()["papers"]}
    metadata = papers["stomatal-aba-andean-potato.pdf"]["metadata"]

    assert metadata["doi"] == "10.5555/spp.2019.0142"
    assert metadata["year"] == 2019
    assert metadata["authors"][0] == {"family": "Quispe", "given": "Rosa Elena"}
    assert metadata["title"].startswith("Stomatal regulation")


def test_reingesting_unchanged_folder_reuses_index(client: TestClient, corpus: Path):
    library_id = create_library(client, corpus)
    ingest(client, library_id)

    second = ingest(client, library_id)

    assert all(event["data"]["reused"] for event in second if event["type"] == "paper.indexed")


def test_search_returns_citable_passages_ranked_by_relevance(client: TestClient, corpus: Path):
    library_id = create_library(client, corpus)
    ingest(client, library_id)

    response = client.post(
        f"/libraries/{library_id}/search",
        json={"queries": ["stomatal conductance abscisic acid drought"], "top_k": 3},
    )

    passages = response.json()
    assert response.status_code == 200
    assert passages[0]["metadata"]["doi"] == "10.5555/spp.2019.0142"
    assert passages[0]["page"] >= 1
    assert passages[0]["file_path"].endswith("stomatal-aba-andean-potato.pdf")
    assert all("late blight" not in passage["text"].lower() for passage in passages)


def test_search_respects_year_filter_and_per_paper_cap(client: TestClient, corpus: Path):
    library_id = create_library(client, corpus)
    ingest(client, library_id)

    passages = client.post(
        f"/libraries/{library_id}/search",
        json={"queries": ["drought tolerance potato yield"], "top_k": 10, "per_paper": 1, "year_from": 2021},
    ).json()

    assert passages
    assert all(passage["metadata"]["year"] >= 2021 for passage in passages)
    assert len({passage["paper_id"] for passage in passages}) == len(passages)


def test_researcher_can_complete_missing_metadata(client: TestClient, corpus: Path):
    library_id = create_library(client, corpus)
    ingest(client, library_id)
    paper = next(
        paper for paper in client.get(f"/libraries/{library_id}").json()["papers"] if paper["status"] == "indexed"
    )

    response = client.patch(f"/papers/{paper['paper_id']}", json={"year": 2015, "authors": []})

    assert response.json()["metadata"]["year"] == 2015
    assert response.json()["issues"] == ["Faltan datos para citarlo: autores. Puedes completarlos."]


def test_folder_without_pdfs_fails_with_guidance(client: TestClient, tmp_path: Path):
    empty = tmp_path / "vacia"
    empty.mkdir()
    library_id = create_library(client, empty)

    events = ingest(client, library_id)

    assert events[-1]["type"] == "job.failed"
    assert events[-1]["data"]["code"] == "empty_folder"


def test_unknown_folder_and_library_are_reported(client: TestClient, tmp_path: Path):
    assert client.post("/libraries", json={"path": str(tmp_path / "nope")}).status_code == 422
    assert client.get("/libraries/unknown").status_code == 404
