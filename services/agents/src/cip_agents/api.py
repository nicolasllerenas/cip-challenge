from cip_contracts import DraftRequest
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from cip_agents.config import Settings
from cip_agents.graph import build_graph
from cip_agents.library_client import HttpLibrary, Library
from cip_agents.models import AnthropicModel, LanguageModel
from cip_agents.offline import OfflineModel
from cip_agents.routing import ModelRouter
from cip_agents.runner import DraftRunner


def build_model(settings: Settings) -> LanguageModel:
    if settings.resolved_provider == "anthropic":
        return AnthropicModel(ModelRouter(settings))
    return OfflineModel()


def create_app(
    settings: Settings | None = None, model: LanguageModel | None = None, library: Library | None = None
) -> FastAPI:
    settings = settings or Settings()
    model = model or build_model(settings)
    runner = DraftRunner(build_graph(model, library or HttpLibrary(settings.library_url), settings), model)
    app = FastAPI(title="CIP Agents Service", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "provider": model.provider, "models": model.assignments()}

    @app.post("/runs")
    async def run(request: DraftRequest) -> StreamingResponse:
        lines = (event.to_ndjson() async for event in runner.run(request))
        return StreamingResponse(lines, media_type="application/x-ndjson")

    return app
