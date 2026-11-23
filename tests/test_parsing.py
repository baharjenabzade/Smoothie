import json

from app.ai.parsing import extract_json

PAYLOAD = '{"follow_up_questions": ["Why?"]}'


def test_plain_json_is_unchanged():
    assert extract_json(PAYLOAD) == PAYLOAD


def test_strips_markdown_fences():
    assert extract_json(f"```json\n{PAYLOAD}\n```") == PAYLOAD


def test_strips_qwen_think_block():
    assert extract_json(f"<think>let me reason about this...</think>\n{PAYLOAD}") == PAYLOAD


def test_unterminated_think_block_leaves_nothing():
    assert extract_json('<think>I am still thinking {"a": 1}') == ""


def test_ignores_chatter_around_the_object():
    text = f"Sure! Here is the result:\n{PAYLOAD}\nHope that helps."
    assert json.loads(extract_json(text)) == {"follow_up_questions": ["Why?"]}
