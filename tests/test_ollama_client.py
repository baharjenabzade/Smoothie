import json

import pytest

httpx = pytest.importorskip("httpx")

from app.ai.client import OllamaClient
from app.ai.schemas import FollowUpResult
from app.core.errors import LLMError

VALID = '{"follow_up_questions": ["Why do you think so?"]}'


def make_client(handler, **kwargs) -> OllamaClient:
    return OllamaClient(
        base_url="http://ollama.test",
        model="qwen3:8b",
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def reply(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


def generate(client: OllamaClient):
    return client.generate(system="sys", user="usr", schema=FollowUpResult)


def test_sends_schema_and_parses_reply():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return reply(VALID)

    result = generate(make_client(handler))
    assert result.follow_up_questions == ["Why do you think so?"]
    assert seen["model"] == "qwen3:8b"
    assert seen["stream"] is False
    assert seen["think"] is False
    assert "follow_up_questions" in seen["format"]["properties"]
    assert [m["role"] for m in seen["messages"]] == ["system", "user"]


def test_strips_think_block_and_fences():
    client = make_client(lambda r: reply(f"<think>hmm</think>```json\n{VALID}\n```"))
    assert generate(client).follow_up_questions == ["Why do you think so?"]


def test_retries_once_with_the_error_when_output_is_invalid():
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return reply("definitely not json" if len(bodies) == 1 else VALID)

    result = generate(make_client(handler))
    assert result.follow_up_questions == ["Why do you think so?"]
    assert len(bodies) == 2
    assert [m["role"] for m in bodies[1]["messages"]] == ["system", "user", "assistant", "user"]


def test_gives_up_with_502_after_retries_are_used():
    calls = []

    def handler(request):
        calls.append(1)
        return reply("still not json")

    with pytest.raises(LLMError) as exc:
        generate(make_client(handler, max_retries=1))
    assert exc.value.status_code == 502
    assert len(calls) == 2


def test_missing_model_gives_pull_hint():
    client = make_client(lambda r: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(LLMError) as exc:
        generate(client)
    assert exc.value.status_code == 503
    assert "ollama pull qwen3:8b" in exc.value.message


def test_server_error_includes_ollamas_explanation():
    body = {"error": "model requires more system memory (5.6 GiB) than is available (3.1 GiB)"}
    client = make_client(lambda r: httpx.Response(500, json=body))
    with pytest.raises(LLMError) as exc:
        generate(client)
    assert exc.value.status_code == 502
    assert "(500)" in exc.value.message and "more system memory" in exc.value.message


def test_non_json_error_body_is_not_echoed():
    client = make_client(lambda r: httpx.Response(502, text="<html>Bad Gateway from proxy</html>"))
    with pytest.raises(LLMError) as exc:
        generate(client)
    assert exc.value.message == "The AI model server returned an error (502)"


def test_unreachable_server_gives_503():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    with pytest.raises(LLMError) as exc:
        generate(make_client(handler))
    assert exc.value.status_code == 503


def test_timeout_gives_504():
    def handler(request):
        raise httpx.ReadTimeout("too slow")

    with pytest.raises(LLMError) as exc:
        generate(make_client(handler))
    assert exc.value.status_code == 504


def test_health_reports_model_availability():
    models = {"models": [{"name": "qwen3:8b", "model": "qwen3:8b"}]}
    ok = make_client(lambda r: httpx.Response(200, json=models)).health()
    assert ok == {"provider": "ollama", "reachable": True, "model": "qwen3:8b", "model_available": True}

    missing = make_client(lambda r: httpx.Response(200, json={"models": []})).health()
    assert missing["reachable"] is True and missing["model_available"] is False


def test_health_when_server_is_down():
    def handler(request):
        raise httpx.ConnectError("down")

    assert make_client(handler).health()["reachable"] is False
