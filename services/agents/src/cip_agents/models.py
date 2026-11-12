from typing import Any, Protocol

import anthropic
from cip_contracts import DraftRequest
from pydantic import BaseModel, ValidationError

from cip_agents.prompts import planner_prompt, repair_prompt, verifier_prompt, writer_prompt
from cip_agents.routing import ModelRouter, Route, Task
from cip_agents.schemas import (
    ClaimToCheck,
    EvidenceItem,
    PlanOutput,
    RepairOutput,
    SectionDraftOutput,
    SectionPlan,
    VerificationOutput,
)

FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_CAPABLE = frozenset({"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-2"})


class ModelError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class LanguageModel(Protocol):
    provider: str

    def assignments(self) -> dict[str, str]: ...

    async def plan(self, request: DraftRequest) -> PlanOutput: ...

    async def write(
        self, request: DraftRequest, plan: SectionPlan, evidence: list[EvidenceItem]
    ) -> SectionDraftOutput: ...

    async def verify(self, language: str, claims: list[ClaimToCheck]) -> VerificationOutput: ...

    async def repair(
        self, language: str, claims: list[tuple[ClaimToCheck, str]], evidence: list[EvidenceItem]
    ) -> RepairOutput: ...


def translate_api_error(error: anthropic.APIError) -> ModelError:
    match error:
        case anthropic.RateLimitError():
            return ModelError(
                "Hay mucha demanda en el servicio de IA. Intenta de nuevo en unos minutos.", "rate_limited"
            )
        case anthropic.AuthenticationError() | anthropic.PermissionDeniedError():
            return ModelError("Las credenciales del servicio de IA no son válidas. Avisa a soporte.", "llm_auth")
        case anthropic.APIStatusError(status_code=status) if status >= 500:
            return ModelError("El servicio de IA no está disponible en este momento.", "llm_unavailable")
        case anthropic.APIConnectionError():
            return ModelError("No hay conexión con el servicio de IA. Revisa tu internet.", "llm_unreachable")
        case _:
            return ModelError("El servicio de IA rechazó la solicitud.", "llm_bad_request")


class AnthropicModel:
    provider = "anthropic"

    def __init__(self, router: ModelRouter, client: anthropic.AsyncAnthropic | None = None) -> None:
        self._router = router
        self._client = client or anthropic.AsyncAnthropic(max_retries=3)

    def assignments(self) -> dict[str, str]:
        return self._router.assignments()

    async def _call(self, route: Route, system: str, user: str, schema: type[BaseModel]) -> Any:
        options: dict[str, Any] = {}
        if route.model in FALLBACK_CAPABLE:
            options = {"betas": [FALLBACK_BETA], "fallbacks": "default"}
        return await self._client.beta.messages.parse(
            model=route.model,
            max_tokens=route.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
            output_config={"effort": route.effort},
            **options,
        )

    async def _structured[T: BaseModel](self, task: Task, prompt: tuple[str, str], schema: type[T]) -> T:
        system, user = prompt
        for attempt in range(2):
            try:
                response = await self._call(self._router.route(task, attempt), system, user, schema)
            except anthropic.APIError as error:
                raise translate_api_error(error) from error
            except ValidationError:
                continue
            if response.stop_reason not in {"refusal", "max_tokens"} and response.parsed_output is not None:
                return response.parsed_output
        raise ModelError("El modelo no pudo completar esta parte del borrador.", "llm_incomplete")

    async def plan(self, request: DraftRequest) -> PlanOutput:
        return await self._structured(Task.PLAN, planner_prompt(request), PlanOutput)

    async def write(self, request: DraftRequest, plan: SectionPlan, evidence: list[EvidenceItem]) -> SectionDraftOutput:
        return await self._structured(Task.WRITE, writer_prompt(request, plan, evidence), SectionDraftOutput)

    async def verify(self, language: str, claims: list[ClaimToCheck]) -> VerificationOutput:
        return await self._structured(Task.VERIFY, verifier_prompt(language, claims), VerificationOutput)

    async def repair(
        self, language: str, claims: list[tuple[ClaimToCheck, str]], evidence: list[EvidenceItem]
    ) -> RepairOutput:
        return await self._structured(Task.REPAIR, repair_prompt(language, claims, evidence), RepairOutput)
