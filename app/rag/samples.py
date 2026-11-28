"""Reference answers written/graded by the platform owner, loaded from JSON files.

Put files in ``knowledge/samples/`` (``*.json`` holding a list, ``{"samples": [...]}``, or ``*.jsonl``
with one sample per line). Files whose name starts with ``_`` are ignored. Format:

    {"part": 2, "question": "Describe a book you enjoyed", "topic": "Books",
     "band": 6.0, "fluency": 6.0, "lexical": 6.0, "grammar": 5.5,
     "answer": "...", "notes": "why this band: ..."}

``band`` is required; the three criterion bands and ``topic`` and ``notes`` are optional.
"""

import json
import logging
import math
from pathlib import Path

from pydantic import BaseModel, ValidationError, field_validator

from app.core.scoring import count_words

logger = logging.getLogger(__name__)

MIN_SAMPLE_WORDS = 5


class ReferenceSample(BaseModel):
    part: int
    question: str
    answer: str
    band: float
    topic: str | None = None
    fluency: float | None = None
    lexical: float | None = None
    grammar: float | None = None
    notes: str | None = None
    source: str = ""

    @field_validator("part")
    @classmethod
    def _part(cls, v: int) -> int:
        if v not in (1, 2, 3):
            raise ValueError("part must be 1, 2 or 3")
        return v

    @field_validator("band", "fluency", "lexical", "grammar")
    @classmethod
    def _band(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if math.isnan(v) or not 0 <= v <= 9:
            raise ValueError("bands must be between 0 and 9")
        return round(v * 2) / 2

    @field_validator("answer")
    @classmethod
    def _answer(cls, v: str) -> str:
        v = v.strip()
        if count_words(v) < MIN_SAMPLE_WORDS:
            raise ValueError(f"answer must have at least {MIN_SAMPLE_WORDS} words")
        return v

    @field_validator("question", "topic", "notes")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) and v.strip() else (None if v is not None else v)


def _records(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("samples", [])
    if not isinstance(data, list):
        raise ValueError("expected a list of samples")
    return data


def load_samples(directory: Path) -> tuple[list[ReferenceSample], list[str]]:
    """Return (valid samples, problems). Bad entries are skipped and reported, never fatal."""
    samples: list[ReferenceSample] = []
    problems: list[str] = []
    if not directory.is_dir():
        return samples, [f"Samples folder not found: {directory}"]
    for path in sorted([*directory.glob("*.json"), *directory.glob("*.jsonl")]):
        if path.name.startswith("_"):
            continue
        try:
            records = _records(path)
        except (OSError, ValueError) as exc:  # JSONDecodeError is a ValueError
            problems.append(f"{path.name}: cannot read ({exc})")
            continue
        for i, record in enumerate(records, 1):
            try:
                if not isinstance(record, dict):
                    raise ValueError("entry is not an object")
                record = dict(record)
                if "overall_band" in record and "band" not in record:
                    record["band"] = record.pop("overall_band")
                samples.append(ReferenceSample(**record, source=f"{path.name}#{i}"))
            except (ValidationError, ValueError, TypeError) as exc:
                reason = exc.errors()[0]["msg"] if isinstance(exc, ValidationError) else str(exc)
                problems.append(f"{path.name} entry {i}: {reason}")
    return samples, problems
