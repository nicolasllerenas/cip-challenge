from types import SimpleNamespace

import anthropic
import httpx
import pytest
from cip_agents.config import Settings
from cip_agents.models import FALLBACK_BETA, AnthropicModel, ModelError
from cip_agents.routing import ModelRouter, Task
from cip_agents.schemas import PlanOutput, SectionOutline
from cip_contracts import DraftRequest

PLAN = PlanOutput(title="T", sections=[SectionOutline(heading="H", goal="G", queries=["q"])])
REQUEST = DraftRequest(library_id="lib", prompt="Estado del arte sobre sequía en papa")


class FakeMessages:
    def __init__(self, responses: list) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def fake_client(*responses) -> SimpleNamespace:
    return SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(list(responses))))


def ok(parsed) -> SimpleNamespace:
    return SimpleNamespace(stop_reason="end_turn", parsed_output=parsed)


def test_router_sends_cheap_tasks_to_fast_model_and_writing_to_strong():
    router = ModelRouter(Settings())

    assert router.route(Task.PLAN).model == "claude-haiku-5-5"
    assert router.route(Task.VERIFY).effort == "low"
    assert router.route(Task.WRITE).model == "claude-opus-5-5"
    assert router.route(Task.PLAN, attempt=1).model == "claude-opus-5-5"


async def test_fast_tasks_do_not_request_fallbacks():
    client = fake_client(ok(PLAN))

    await AnthropicModel(ModelRouter(Settings()), client).plan(REQUEST)

    call = client.beta.messages.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["output_format"] is PlanOutput
    assert call["output_config"] == {"effort": "low"}
    assert "fallbacks" not in call


async def test_refusal_on_fast_model_escalates_to_strong_model_with_fallbacks():
    client = fake_client(SimpleNamespace(stop_reason="refusal", parsed_output=None), ok(PLAN))

    result = await AnthropicModel(ModelRouter(Settings()), client).plan(REQUEST)

    escalated = client.beta.messages.calls[1]
    assert result == PLAN
    assert escalated["model"] == "claude-opus-5-5"
    assert escalated["fallbacks"] == "default"
    assert escalated["betas"] == [FALLBACK_BETA]


async def test_rate_limit_becomes_friendly_model_error():
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    error = anthropic.RateLimitError("rate limited", response=response, body=None)
    client = fake_client(error)

    with pytest.raises(ModelError) as raised:
        await AnthropicModel(ModelRouter(Settings()), client).plan(REQUEST)

    assert raised.value.code == "rate_limited"


def test_auto_provider_uses_offline_without_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    assert Settings().resolved_provider == "offline"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert Settings().resolved_provider == "anthropic"
