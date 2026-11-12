import json

import anthropic
import httpx2
from cip_agents import check
from cip_agents.config import Settings
from cip_agents.models import AnthropicModel
from cip_agents.routing import ModelRouter

RESPONSES = {
    "title": {"title": "Estado del arte", "sections": [{"heading": "H", "goal": "G", "queries": ["q"]}]},
    "paragraphs": {"paragraphs": [{"sentences": [{"text": "La conductancia cayó 58 %.", "evidence": ["E1"]}]}]},
    "judgments": {"judgments": [{"claim_id": "c0", "verdict": "supported", "rationale": ""}]},
}


def fake_api(request: httpx2.Request) -> httpx2.Response:
    body = json.loads(request.content)
    properties = body["output_config"]["format"]["schema"]["properties"]
    payload = next(value for key, value in RESPONSES.items() if key in properties)
    return httpx2.Response(
        200,
        json={
            "id": "msg",
            "type": "message",
            "role": "assistant",
            "model": body["model"],
            "content": [{"type": "text", "text": json.dumps(payload)}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    )


async def test_check_runs_planner_writer_and_verifier(capsys):
    client = anthropic.AsyncAnthropic(
        api_key="test", http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(fake_api))
    )
    router = ModelRouter(Settings())

    await check.run(AnthropicModel(router, client), router)

    output = capsys.readouterr().out
    assert "✓ Planificador (claude-haiku-5-5)" in output
    assert "✓ Redactor (claude-opus-5-5)" in output
    assert "✓ Verificador (claude-haiku-5-5)" in output


def test_check_explains_how_to_add_credentials(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    assert check.main() == 2
    assert "console.anthropic.com" in capsys.readouterr().out
