import re

_THINK_CLOSED = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_THINK_OPEN = re.compile(r"<think>.*$", re.DOTALL | re.IGNORECASE)  # truncated reasoning
_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


def extract_json(raw: str) -> str:
    """Pull a JSON object out of an LLM reply.

    Qwen3 may emit <think>...</think> blocks (when thinking is on) and some models wrap JSON in
    Markdown fences or add a sentence before it. Strip all of that and return the JSON text.
    """
    text = _THINK_CLOSED.sub("", raw)
    text = _THINK_OPEN.sub("", text).strip()
    text = _FENCE.sub("", text).strip()
    if text and text[0] not in "{[":
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start : end + 1]
    return text
