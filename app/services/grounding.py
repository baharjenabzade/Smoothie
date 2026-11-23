"""Guards against LLM hallucinations in evaluation output.

A small local model sometimes "corrects" sentences the learner never said. Grammar issues and
quoted structures must be verbatim excerpts of the transcript, otherwise they are dropped.
"""

from collections.abc import Iterable

from app.ai.schemas import EvaluationResult, GrammarFinding

MAX_ISSUES = 8
MAX_STRUCTURES = 4

_QUOTES = {"’": "'", "‘": "'", "“": '"', "”": '"'}


def _norm(text: str) -> str:
    for fancy, plain in _QUOTES.items():
        text = text.replace(fancy, plain)
    return " ".join(text.lower().split()).strip(" .,;:!?\"'-…")


def _contains(haystack_norm: str, needle: str) -> bool:
    needle_norm = _norm(needle)
    return bool(needle_norm) and needle_norm in haystack_norm


def ground_issues(issues: Iterable[GrammarFinding], transcript: str) -> list[GrammarFinding]:
    haystack = _norm(transcript)
    seen: set[str] = set()
    kept: list[GrammarFinding] = []
    for issue in issues:
        original = _norm(issue.original)
        if not original or original == _norm(issue.corrected):
            continue
        if original not in haystack or original in seen:
            continue
        seen.add(original)
        kept.append(issue)
    return kept


def ground_result(result: EvaluationResult, transcript: str) -> EvaluationResult:
    haystack = _norm(transcript)
    structures = [s for s in result.correct_structures if _contains(haystack, s.example)]
    return result.model_copy(
        update={
            "grammar_issues": ground_issues(result.grammar_issues, transcript)[:MAX_ISSUES],
            "correct_structures": structures[:MAX_STRUCTURES],
        }
    )
