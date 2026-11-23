import logging
import time
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.parsing import extract_json
from app.core.errors import LLMError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _error_detail(response: httpx.Response) -> str:
    """Ollama's own explanation, e.g. 'model requires more system memory'. Empty if not JSON."""
    try:
        error = response.json().get("error")
    except (ValueError, AttributeError):
        return ""
    return str(error)[:300] if error else ""


class LLMClient(Protocol):
    """What the services need from an LLM backend. Tests swap in a fake."""

    model_name: str

    def generate(self, *, system: str, user: str, schema: type[T]) -> T: ...

    def health(self) -> dict[str, Any]: ...


class OllamaClient:
    """Calls a local Ollama server and returns output validated against a Pydantic schema."""

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

    # ------------------------------------------------------------------ public API

    def generate(self, *, system: str, user: str, schema: type[T]) -> T:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error = "unknown error"
        for attempt in range(self._max_retries + 1):
            started = time.monotonic()
            raw = self._chat(messages, schema)
            logger.info(
                "LLM call (%s, attempt %d) finished in %.1fs",
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

    def health(self) -> dict[str, Any]:
        try:
            response = self._client.get("/api/tags", timeout=5.0)
            response.raise_for_status()
            models = response.json().get("models", [])
        except (httpx.HTTPError, ValueError):
            return {"reachable": False, "model": self.model_name, "model_available": False}
        names = {m.get("name") for m in models} | {m.get("model") for m in models}
        available = self.model_name in names or f"{self.model_name}:latest" in names
        return {"reachable": True, "model": self.model_name, "model_available": available}

    # ------------------------------------------------------------------ internals

    def _chat(self, messages: list[dict[str, str]], schema: type[BaseModel]) -> str:
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
            detail = _error_detail(response)
            suffix = f": {detail}" if detail else ""
            raise LLMError(
                f"The AI model server returned an error ({response.status_code}){suffix}", 502
            )

        try:
            return response.json()["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise LLMError("The AI model server sent an unexpected response.", 502) from exc
