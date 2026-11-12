import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from cip_contracts import EventType, JobEvent
from cip_gateway.api import create_app
from cip_gateway.config import Settings
from cip_testkit import sample_draft
from fastapi.testclient import TestClient

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def ndjson(*events: JobEvent) -> bytes:
    return "".join(event.to_ndjson() for event in events).encode()


def completed_run() -> bytes:
    return ndjson(
        JobEvent(type=EventType.JOB_STARTED, message="Empecé"),
        JobEvent(type=EventType.SECTION_PLANNED, message="Respuestas fisiológicas"),
        JobEvent(type=EventType.SOURCE_FOUND, message="Stomatal regulation"),
        JobEvent(
            type=EventType.JOB_COMPLETED,
            message="Listo",
            data={"draft": sample_draft().model_dump(mode="json")},
        ),
    )


async def endless_run():
    yield JobEvent(type=EventType.JOB_STARTED, message="Empecé").to_ndjson().encode()
    await asyncio.sleep(3600)


class FakeServices:
    def __init__(self) -> None:
        self.agents: Callable[[], object] = completed_run
        self.down: set[str] = set()
        self.renders: list[dict] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        host, path = request.url.host, request.url.path
        if host in self.down:
            raise httpx.ConnectError("down", request=request)
        if path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if host == "agents" and path == "/runs":
            return httpx.Response(200, content=self.agents())
        if host == "documents" and path == "/render":
            body = json.loads(request.content)
            self.renders.append(body)
            extension = body["format"]
            return httpx.Response(
                200,
                content=b"PK-fake" if extension == "docx" else b"# md",
                headers={"content-disposition": f'attachment; filename="estado-del-arte.{extension}"'},
            )
        if host == "library" and path == "/libraries":
            return httpx.Response(
                201,
                json={"library_id": "lib-1", "path": "/tmp/pdfs", "counts": {}, "papers": []},
            )
        if host == "library" and path.endswith("/ingest"):
            return httpx.Response(
                200,
                content=ndjson(
                    JobEvent(type=EventType.JOB_STARTED, message="Encontré 2 PDFs"),
                    JobEvent(type=EventType.JOB_COMPLETED, message="2 de 2 listos"),
                ),
            )
        return httpx.Response(404, json={"detail": "No encontré eso."})


@pytest.fixture
def services() -> FakeServices:
    return FakeServices()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        library_url="http://library",
        agents_url="http://agents",
        documents_url="http://documents",
        data_dir=tmp_path / "gateway",
        exports_dir=tmp_path / "exports",
        heartbeat_seconds=0.2,
    )


@pytest.fixture
def client(settings: Settings, services: FakeServices):
    app = create_app(settings, mounts={"all://": httpx.MockTransport(services.handle)})
    with TestClient(app) as test_client:
        yield test_client


def read_sse(client: TestClient, job_id: str, headers: dict[str, str] | None = None) -> list[dict]:
    with client.stream("GET", f"/v1/jobs/{job_id}/events", headers=headers or {}) as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    events = []
    for block in body.split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line and not line.startswith(":"))
        if "data" in fields:
            events.append(json.loads(fields["data"]) | {"sse_id": int(fields["id"])})
    return events


@pytest.fixture
def sse():
    return read_sse


@pytest.fixture
def slow_agents(services: FakeServices) -> FakeServices:
    services.agents = endless_run
    return services
