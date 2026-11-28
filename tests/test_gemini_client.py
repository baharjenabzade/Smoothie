import json

import pytest

httpx = pytest.importorskip("httpx")

from app.ai.client import GeminiClient
from app.ai.schemas import FollowUpResult
from app.core.errors import LLMError

VALID = '{"follow_up_questions": ["Why do you think so?"]}'


def make_client(handler, sleeps=None, **kwargs) -> GeminiClient:
    return GeminiClient(
        api_key="k-123",
        model="gemini-2.5-flash",
        base_url="https://gemini.test/v1beta",
        sleep=(sleeps.append if sleeps is not None else (lambda s: None)),
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def ok(text: str) -> httpx.Response:
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]})


def generate(client):
    return client.generate(system="sys", user="usr", schema=FollowUpResult)


def test_request_shape_and_parsing():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("x-goog-api-key")
        seen["body"] = json.loads(request.content)
        return ok(VALID)

    result = generate(make_client(handler))
    assert result.follow_up_questions == ["Why do you think so?"]
    assert seen["url"].endswith("/models/gemini-2.5-flash:generateContent")
    assert "k-123" not in seen["url"] and seen["key"] == "k-123"
    body = seen["body"]
    assert body["systemInstruction"]["parts"][0]["text"] == "sys"
    assert body["contents"][0] == {"role": "user", "parts": [{"text": "usr"}]}
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseSchema" in body["generationConfig"]


def test_retries_once_on_invalid_json():
    calls = []

    def handler(request):
        calls.append(1)
        return ok("not json") if len(calls) == 1 else ok(VALID)

    assert generate(make_client(handler)).follow_up_questions
    assert len(calls) == 2


def test_rate_limit_is_retried_with_backoff():
    calls, sleeps = [], []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, json={"error": {"message": "slow down"}})
        return ok(VALID)

    assert generate(make_client(handler, sleeps)).follow_up_questions
    assert len(calls) == 2 and len(sleeps) == 1


def test_daily_quota_is_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429, json={"error": {"message": "Quota exceeded for GenerateRequestsPerDay"}})

    with pytest.raises(LLMError):
        generate(make_client(handler))
    assert len(calls) == 1


@pytest.mark.parametrize("status", [400, 403, 404, 500])
def test_http_errors_become_llm_errors(status):
    def handler(request):
        return httpx.Response(status, json={"error": {"message": "nope"}})

    with pytest.raises(LLMError):
        generate(make_client(handler))


def test_unreachable_and_empty_answers():
    def down(request):
        raise httpx.ConnectError("down")

    with pytest.raises(LLMError) as exc:
        generate(make_client(down))
    assert exc.value.status_code == 503

    with pytest.raises(LLMError):
        generate(make_client(lambda r: httpx.Response(200, json={"candidates": []})))


def test_health():
    good = make_client(lambda r: httpx.Response(200, json={"name": "models/gemini-2.5-flash"})).health()
    assert good["provider"] == "gemini" and good["model_available"] is True
    bad = make_client(lambda r: httpx.Response(404, json={"error": {"message": "x"}})).health()
    assert bad["reachable"] is True and bad["model_available"] is False
