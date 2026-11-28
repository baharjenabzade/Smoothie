import logging
import time
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.gemini_schema import to_gemini_schema
from app.ai.parsing import extract_json
from app.core.errors import LLMError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
Message = dict[str, str]


class LLMClient(Protocol):
    """What the services need from an LLM backend. Tests swap in a fake."""

    model_name: str

    def generate(self, *, system: str, user: str, schema: type[T]) -> T: ...

    def health(self) -> dict[str, Any]: ...


class _StructuredClient:
    """Shared logic: ask for JSON, validate it against a Pydantic schema, and if the reply is
    malformed, tell the model what was wrong and ask once more."""

    provider = "llm"
    model_name: str
    _max_retries: int = 1

    def _complete(self, messages: list[Message], schema: type[BaseModel]) -> str:
        raise NotImplementedError

    def generate(self, *, system: str, user: str, schema: type[T]) -> T:
        messages: list[Message] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error = "unknown error"
        for attempt in range(self._max_retries + 1):
            started = time.monotonic()
            raw = self._complete(messages, schema)
            logger.info(
                "%s call (%s, attempt %d) finished in %.1fs",
                self.provider,
                self.model_name,
                attempt + 1,
                time.monotonic() - started,
            )
            try:
                return schema.model_validate_json(extract_json(raw))
            except (ValidationError, ValueError) as exc:
                last_error = str(exc)[:500]
                logger.warning("LLM output failed validation (attempt %d): %s", attempt + 1, last_error)
                messages = [
                    *messages,
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": (
                            "Your previous reply did not match the required JSON schema "
                            f"({last_error}). Reply again with ONLY valid JSON that matches the schema."
                        ),
                    },
                ]
        raise LLMError("The AI model returned an invalid response. Please try again.", 502)


# =============================================================================== Ollama


def _ollama_error_detail(response: httpx.Response) -> str:
    """Ollama's own explanation, e.g. 'model requires more system memory'. Empty if not JSON."""
    try:
        error = response.json().get("error")
    except (ValueError, AttributeError):
        return ""
    return str(error)[:300] if error else ""


class OllamaClient(_StructuredClient):
    """Calls a local Ollama server and returns output validated against a Pydantic schema."""

    provider = "ollama"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float = 180.0,
        temperature: float = 0.3,
        num_ctx: int = 8192,
        think: bool = False,
        max_retries: int = 1,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.model_name = model
        self._temperature = temperature
        self._num_ctx = num_ctx
        self._think = think
        self._max_retries = max_retries
        self._base_url = base_url.rstrip("/")
        # trust_env=False: never route calls to the model server through HTTP_PROXY/HTTPS_PROXY
        # (a VPN or system proxy would otherwise answer requests to localhost with 502).
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout, connect=5.0),
            transport=transport,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def health(self) -> dict[str, Any]:
        try:
            response = self._client.get("/api/tags", timeout=5.0)
            response.raise_for_status()
            models = response.json().get("models", [])
        except (httpx.HTTPError, ValueError):
            return {"provider": "ollama", "reachable": False, "model": self.model_name, "model_available": False}
        names = {m.get("name") for m in models} | {m.get("model") for m in models}
        available = self.model_name in names or f"{self.model_name}:latest" in names
        return {"provider": "ollama", "reachable": True, "model": self.model_name, "model_available": available}

    def _complete(self, messages: list[Message], schema: type[BaseModel]) -> str:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "think": self._think,
            "format": schema.model_json_schema(),
            "options": {"temperature": self._temperature, "num_ctx": self._num_ctx},
        }
        try:
            response = self._client.post("/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise LLMError("The AI model took too long to respond. Please try again.", 504) from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Cannot reach the AI model server at {self._base_url}.", 503) from exc

        if response.status_code == 404:
            raise LLMError(
                f"Model '{self.model_name}' is not available in Ollama. "
                f"Run: ollama pull {self.model_name}",
                503,
            )
        if response.status_code >= 400:
            logger.error("Ollama error %s: %s", response.status_code, response.text[:300])
            detail = _ollama_error_detail(response)
            suffix = f": {detail}" if detail else ""
            raise LLMError(
                f"The AI model server returned an error ({response.status_code}){suffix}", 502
            )

        try:
            return response.json()["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise LLMError("The AI model server sent an unexpected response.", 502) from exc


# =============================================================================== Gemini

GEMINI_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
# Thinking models spend part of this budget on reasoning, so keep it generous.
GEMINI_MAX_OUTPUT_TOKENS = 12000


def _gemini_error(response: httpx.Response, model: str) -> LLMError:
    """Turn a failed Gemini response into a message a learner can act on."""
    detail = ""
    try:
        detail = str((response.json().get("error") or {}).get("message") or "")
    except (ValueError, AttributeError):
        pass
    lowered = detail.lower()
    status = response.status_code
    logger.error("Gemini error %s: %s", status, (detail or response.text)[:300])

    if "location is not supported" in lowered:
        return LLMError(
            "Google's Gemini API is not available from this computer's location or network. "
            "Set LLM_PROVIDER=ollama to use the local model instead.",
            503,
        )
    if "api key" in lowered or status in (401, 403):
        return LLMError(f"Gemini rejected the request. Check GEMINI_API_KEY. ({detail[:200] or status})", 503)
    if status == 404:
        return LLMError(
            f"Gemini model '{model}' was not found. Run `python -m app.gemini_models` to list "
            "the models your key can use, then set GEMINI_MODEL.",
            503,
        )
    if status == 429:
        return LLMError("Gemini's rate limit was reached. Wait a minute and try again.", 429)
    suffix = f": {detail[:300]}" if detail else ""
    return LLMError(f"Gemini returned an error ({status}){suffix}", 502)


class GeminiClient(_StructuredClient):
    """Calls the Google Gemini API (generateContent) with a JSON schema for structured output."""

    provider = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = GEMINI_DEFAULT_BASE_URL,
        timeout: float = 120.0,
        temperature: float = 0.3,
        max_retries: int = 1,
        rate_limit_retries: int = 2,
        sleep: Callable[[float], None] = time.sleep,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.model_name = model
        self._temperature = temperature
        self._max_retries = max_retries
        self._rate_limit_retries = rate_limit_retries
        self._sleep = sleep
        # The key travels in a header, never in the URL, so it does not end up in logs.
        # trust_env stays on so a system proxy (HTTPS_PROXY) is honoured for this remote API.
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={"x-goog-api-key": api_key},
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def health(self) -> dict[str, Any]:
        info: dict[str, Any] = {"provider": "gemini", "model": self.model_name}
        try:
            response = self._client.get(f"/models/{self.model_name}", timeout=10.0)
        except httpx.HTTPError:
            return {**info, "reachable": False, "model_available": False}
        if response.status_code == 200:
            return {**info, "reachable": True, "model_available": True}
        return {**info, "reachable": True, "model_available": False, "detail": _gemini_error(response, self.model_name).message}

    def _complete(self, messages: list[Message], schema: type[BaseModel]) -> str:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        payload: dict[str, Any] = {
            "contents": [
                {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in messages
                if m["role"] != "system"
            ],
            "generationConfig": {
                "temperature": self._temperature,
                "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS,
                "responseMimeType": "application/json",
                "responseSchema": to_gemini_schema(schema),
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        return self._extract_text(self._post(f"/models/{self.model_name}:generateContent", payload))

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response: httpx.Response | None = None
        for attempt in range(self._rate_limit_retries + 1):
            try:
                response = self._client.post(path, json=payload)
            except httpx.TimeoutException as exc:
                raise LLMError("Gemini took too long to respond. Please try again.", 504) from exc
            except httpx.HTTPError as exc:
                raise LLMError(
                    "Cannot reach the Gemini API. Check your internet connection and proxy settings.", 503
                ) from exc

            out_of_daily_quota = "perday" in response.text.lower().replace(" ", "")
            if response.status_code in (429, 503) and attempt < self._rate_limit_retries and not out_of_daily_quota:
                wait = min(30.0, 8.0 * (attempt + 1))
                logger.warning("Gemini busy or rate limited (%s); retrying in %.0fs", response.status_code, wait)
                self._sleep(wait)
                continue
            break

        assert response is not None
        if response.status_code >= 400:
            raise _gemini_error(response, self.model_name)
        try:
            return response.json()
        except ValueError as exc:
            raise LLMError("Gemini sent an unexpected response.", 502) from exc

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        block = (data.get("promptFeedback") or {}).get("blockReason")
        if block:
            raise LLMError(f"Gemini declined to process this request ({block}).", 422)
        candidates = data.get("candidates") or []
        if not candidates:
            raise LLMError("Gemini returned no answer. Please try again.", 502)
        candidate = candidates[0]
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text.strip():
            reason = candidate.get("finishReason", "unknown")
            raise LLMError(f"Gemini returned an empty answer (finish reason: {reason}).", 502)
        return text
