"""Turn a Pydantic model into the schema dialect Gemini accepts for structured output.

Pydantic emits JSON Schema with $defs/$ref, titles, defaults and anyOf. Gemini's `responseSchema`
accepts only a small OpenAPI-style subset, so references are inlined and everything else is dropped.
Pure Python, no HTTP, so it is easy to test.
"""

from typing import Any

from pydantic import BaseModel

_ALLOWED = {"type", "required", "items", "enum", "description", "format", "minItems", "maxItems", "nullable"}


def to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    raw = model.model_json_schema()
    return _clean(raw, raw.get("$defs", {}))


def _clean(node: Any, defs: dict[str, Any]) -> Any:
    if not isinstance(node, dict):
        return node

    if "$ref" in node:  # inline the referenced definition
        target = defs[node["$ref"].rsplit("/", 1)[-1]]
        extra = {k: v for k, v in node.items() if k != "$ref"}
        return _clean({**target, **extra}, defs)

    if "anyOf" in node:  # Optional[X] -> X with nullable
        options = [o for o in node["anyOf"] if o.get("type") != "null"]
        rest = {k: v for k, v in node.items() if k != "anyOf"}
        if len(options) == 1:
            return _clean({**rest, **options[0], "nullable": True}, defs)
        return _clean(rest, defs)

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key == "properties":
            # property *names* are user data, so they are never filtered against _ALLOWED
            out["properties"] = {name: _clean(sub, defs) for name, sub in value.items()}
        elif key == "items":
            out["items"] = _clean(value, defs)
        elif key in _ALLOWED:
            out[key] = value
    return out
