"""Deterministic guard rails on the model's band scores.

LLMs tend to be generous. These rules only ever LOWER a score, using facts we can measure
(answer length, density of verified grammar errors) plus a halo-effect limit. They are heuristics
based on the public band descriptors, not an official IELTS algorithm.
"""

import math
from dataclasses import dataclass, field

from app.ai.schemas import EvaluationResult
from app.core.scoring import round_band

# (minimum words, highest fluency band allowed below that length), checked in order
_LENGTH_CAPS: dict[int, list[tuple[int, float]]] = {
    1: [(12, 4.5), (20, 5.5), (30, 6.5)],
    2: [(60, 4.5), (100, 5.5), (150, 6.5)],
    3: [(20, 4.5), (40, 5.5), (60, 6.5)],
}
# (errors per 100 words at or above, highest grammar band allowed)
_ERROR_CAPS = [(8.0, 4.5), (5.0, 5.0), (3.5, 5.5), (2.5, 6.0), (1.5, 6.5), (0.8, 7.0)]
MIN_WORDS_FOR_DENSITY = 20
MAX_GAP = 1.5  # highest criterion may exceed the lowest by at most this
TEXT_ONLY_CEILING = 8.5  # a transcript alone cannot show band 9 delivery


@dataclass
class Calibrated:
    fluency: float
    lexical: float
    grammar: float
    notes: list[str] = field(default_factory=list)


def strict_round(value: float) -> float:
    """Round DOWN to the nearest half band."""
    return math.floor(min(9.0, max(0.0, value)) * 2 + 1e-9) / 2


def calibrate(result: EvaluationResult, *, part: int, word_count: int, strict: bool = True) -> Calibrated:
    f = result.fluency_coherence.score
    lex = result.lexical_resource.score
    g = result.grammatical_range_accuracy.score
    out = Calibrated(f, lex, g)
    if not strict:
        return out

    def cap(name: str, value: float, limit: float, why: str) -> float:
        if value > limit:
            out.notes.append(f"{name} limited to {limit:g}: {why}")
            return limit
        return value

    for min_words, limit in _LENGTH_CAPS[part]:
        if word_count < min_words:
            out.fluency = cap("Fluency and coherence", out.fluency, limit, f"the answer is short for Part {part} ({word_count} words).")
            break

    if word_count >= MIN_WORDS_FOR_DENSITY:
        density = len(result.grammar_issues) * 100 / word_count
        for threshold, limit in _ERROR_CAPS:
            if density >= threshold:
                out.grammar = cap("Grammar", out.grammar, limit, f"{len(result.grammar_issues)} confirmed error(s) in {word_count} words.")
                break

    low = min(out.fluency, out.lexical, out.grammar)
    ceiling = round_band(low + MAX_GAP)
    for name in ("fluency", "lexical", "grammar"):
        value = getattr(out, name)
        if value > ceiling:
            out.notes.append(f"{name.capitalize()} limited to {ceiling:g}: criteria rarely differ by more than {MAX_GAP:g} bands.")
            setattr(out, name, ceiling)
        if getattr(out, name) > TEXT_ONLY_CEILING:
            setattr(out, name, TEXT_ONLY_CEILING)
    return out
