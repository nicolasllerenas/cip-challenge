import time
from pathlib import Path

from cip_contracts import EventType, JobEvent
from cip_gateway.api import create_app
from cip_gateway.store import GatewayStore, JobKind
from fastapi.testclient import TestClient


def start_draft(client: TestClient) -> str:
    response = client.post("/v1/drafts", json={"library_id": "lib-1", "prompt": "Estado del arte sobre sequía en papa"})
    assert response.status_code == 202
    return response.json()["job_id"]


def wait_for_status(client: TestClient, job_id: str, status: str) -> dict:
    for _ in range(100):
        job = client.get(f"/v1/jobs/{job_id}").json()
        if job["status"] == status:
            return job
        time.sleep(0.02)
    raise AssertionError(f"job stayed {job['status']}")


def test_draft_progress_is_streamed_as_sse_and_draft_is_persisted(client, sse):
    job_id = start_draft(client)

    events = sse(client, job_id)

    assert [event["type"] for event in events] == ["job.started", "section.planned", "source.found", "job.completed"]
    assert [event["sse_id"] for event in events] == [1, 2, 3, 4]
    completed = events[-1]["data"]
    assert "draft" not in completed
    assert completed["stats"]["pending_review"] == 2
    draft = client.get(f"/v1/drafts/{completed['draft_id']}").json()
    assert draft["title"] == "Estado del arte: tolerancia a sequía en papa"
    assert client.get("/v1/drafts").json()[0]["draft_id"] == completed["draft_id"]


def test_reconnecting_with_last_event_id_replays_only_missing_events(client, sse):
    job_id = start_draft(client)
    sse(client, job_id)

    resumed = sse(client, job_id, headers={"Last-Event-ID": "2"})

    assert [event["sse_id"] for event in resumed] == [3, 4]


def test_cancel_stops_running_job_and_notifies_subscribers(client, sse, slow_agents):
    job_id = start_draft(client)
    wait_for_status(client, job_id, "running")
    time.sleep(0.1)

    assert client.post(f"/v1/jobs/{job_id}/cancel").json() == {"cancelled": True}
    events = sse(client, job_id)

    assert [event["type"] for event in events] == ["job.started", "job.cancelled"]
    assert client.get(f"/v1/jobs/{job_id}").json()["status"] == "cancelled"
    assert client.post(f"/v1/jobs/{job_id}/cancel").json() == {"cancelled": False}


def test_unreachable_service_fails_job_with_friendly_message(client, sse, services):
    services.down.add("agents")
    job_id = start_draft(client)

    events = sse(client, job_id)

    assert events[-1]["type"] == "job.failed"
    assert events[-1]["data"]["code"] == "service_unavailable"
    assert "no responde" in events[-1]["message"]


def test_health_reports_degraded_services(client, services):
    services.down.add("documents")

    body = client.get("/v1/health").json()

    assert body["status"] == "degraded"
    assert {service["name"]: service["ok"] for service in body["services"]} == {
        "library": True,
        "agents": True,
        "documents": False,
    }


def test_opening_a_library_starts_an_ingestion_job(client, sse):
    response = client.post("/v1/libraries", json={"path": "/tmp/pdfs"})

    assert response.status_code == 201
    events = sse(client, response.json()["job_id"])
    assert [event["type"] for event in events] == ["job.started", "job.completed"]


def test_researcher_reviews_claims(client, sse):
    job_id = start_draft(client)
    draft_id = sse(client, job_id)[-1]["data"]["draft_id"]
    url = f"/v1/drafts/{draft_id}/claims"

    accepted = client.patch(f"{url}/c2", json={"action": "accept"}).json()
    edited = client.patch(f"{url}/c4", json={"action": "edit", "text": "Los drones reducen costos."}).json()

    assert accepted["sections"][0]["paragraphs"][0]["claims"][1]["review"] == "accepted"
    claim = edited["sections"][1]["paragraphs"][0]["claims"][1]
    assert (claim["text"], claim["review"]) == ("Los drones reducen costos.", "accepted")
    assert client.patch(f"{url}/c4", json={"action": "edit", "text": "  "}).status_code == 422
    assert client.patch(f"{url}/missing", json={"action": "accept"}).status_code == 404


def test_export_saves_docx_and_serves_it(client, sse, services, settings):
    job_id = start_draft(client)
    draft_id = sse(client, job_id)[-1]["data"]["draft_id"]

    result = client.post(f"/v1/drafts/{draft_id}/exports", json={"format": "docx"}).json()

    exported = result["files"][0]
    assert result["pending_review"] == 2
    assert Path(exported["path"]).read_bytes() == b"PK-fake"
    assert client.get(exported["url"]).content == b"PK-fake"
    assert services.renders[0]["include_review_comments"] is True


def test_markdown_export_ships_bibliography_alongside(client, sse):
    job_id = start_draft(client)
    draft_id = sse(client, job_id)[-1]["data"]["draft_id"]

    result = client.post(f"/v1/drafts/{draft_id}/exports", json={"format": "md"}).json()

    assert [file["file_name"] for file in result["files"]] == ["estado-del-arte.md", "references.bib"]


def test_exports_cannot_escape_their_folder(client):
    assert client.get("/v1/exports/draft/..%2F..%2Fgateway.db").status_code == 404


def test_jobs_interrupted_by_a_restart_are_closed(settings):
    store = GatewayStore(settings.data_dir / "gateway.db")
    job = store.create_job(JobKind.DRAFT, "lib-1")
    store.append_event(job.job_id, JobEvent(type=EventType.JOB_STARTED, message="Empecé"))

    with TestClient(create_app(settings)) as client:
        body = client.get(f"/v1/jobs/{job.job_id}").json()

    assert body["status"] == "failed"
    assert body["last_seq"] == 2
