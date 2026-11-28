from app.ai.gemini_schema import to_gemini_schema
from app.ai.schemas import EvaluationResult


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_schema_is_inlined_and_has_no_unsupported_keys():
    schema = to_gemini_schema(EvaluationResult)
    text = repr(schema)
    assert "$ref" not in text and "$defs" not in text and "anyOf" not in text
    assert "additionalProperties" not in text and "title" not in [k for n in _walk(schema) for k in n if k == "title" and not isinstance(n[k], dict)]
    assert schema["type"] == "object" and "properties" in schema
