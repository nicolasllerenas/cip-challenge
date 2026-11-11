from collections.abc import AsyncIterator

from cip_contracts import Draft, DraftRequest, EventType, JobEvent

from cip_agents.evidence import assert_citations_are_grounded
from cip_agents.graph import NoEvidenceError
from cip_agents.library_client import LibraryUnavailableError
from cip_agents.models import LanguageModel, ModelError


def failed(message: str, code: str) -> JobEvent:
    return JobEvent(type=EventType.JOB_FAILED, message=message, data={"code": code})


class DraftRunner:
    def __init__(self, graph, model: LanguageModel) -> None:
        self._graph = graph
        self._model = model

    async def run(self, request: DraftRequest) -> AsyncIterator[JobEvent]:
        yield JobEvent(
            type=EventType.JOB_STARTED,
            message="Empecé a trabajar en tu borrador",
            data={"provider": self._model.provider, "models": self._model.assignments()},
        )
        draft: Draft | None = None
        try:
            async for chunk in self._graph.astream(
                {"request": request}, stream_mode=["custom", "values"], subgraphs=True, version="v2"
            ):
                if chunk["type"] == "custom":
                    yield chunk["data"]
                elif chunk["type"] == "values" and not chunk["ns"]:
                    draft = chunk["data"].get("draft", draft)
        except NoEvidenceError as error:
            yield failed(str(error), "no_evidence")
            return
        except ModelError as error:
            yield failed(str(error), error.code)
            return
        except LibraryUnavailableError as error:
            yield failed(str(error), "library_unavailable")
            return
        assert_citations_are_grounded(draft)
        stats = draft.stats
        yield JobEvent(
            type=EventType.JOB_COMPLETED,
            message=f"Tu borrador está listo: {stats.claims} afirmaciones, {stats.pending_review} por revisar",
            progress=1.0,
            data={"draft": draft.model_dump(mode="json"), "stats": stats.model_dump()},
        )
