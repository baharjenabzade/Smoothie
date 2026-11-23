"""Test doubles and sample data shared by the test modules."""

from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.schemas import (
    CriterionFeedback,
    EvaluationResult,
    GrammarFinding,
    StructureUsed,
    VocabularyEntry,
)

T = TypeVar("T", bound=BaseModel)

TRANSCRIPT = (
    "I am agree that cities are very crowded, but I like living in a big city "
    "because there are many opportunities."
)


class FakeLLM:
    """Returns canned responses keyed by the requested schema class."""

    model_name = "fake-model"

    def __init__(self) -> None:
        self.responses: dict[type, BaseModel] = {}
        self.calls: list[tuple[type, str, str]] = []
        self.error: Exception | None = None

    def generate(self, *, system: str, user: str, schema: type[T]) -> T:
        self.calls.append((schema, system, user))
        if self.error is not None:
            raise self.error
        try:
            return self.responses[schema]  # type: ignore[return-value]
        except KeyError:
            raise AssertionError(f"No fake response registered for {schema.__name__}") from None

    def health(self) -> dict[str, Any]:
        return {"reachable": True, "model": self.model_name, "model_available": True}


def _criterion(score: float) -> CriterionFeedback:
    return CriterionFeedback(
        score=score,
        summary="Reasonable control with some slips.",
        strengths=["Clear main idea"],
        improvements=["Develop ideas further"],
    )


def make_evaluation(
    *, fluency: float = 6.0, lexical: float = 6.5, grammar: float = 6.5
) -> EvaluationResult:
    """An evaluation of TRANSCRIPT. It deliberately contains hallucinated items
    (quotes that are not in the transcript) that the grounding step must drop."""
    return EvaluationResult(
        fluency_coherence=_criterion(fluency),
        lexical_resource=_criterion(lexical),
        grammatical_range_accuracy=_criterion(grammar),
        strengths=["You gave a clear opinion with a reason."],
        areas_for_improvement=["Add an example to support your reason."],
        grammar_issues=[
            GrammarFinding(
                original="I am agree",
                corrected="I agree",
                explanation="'Agree' is a verb, so it does not need 'am'.",
                category="word form",
            ),
            GrammarFinding(  # hallucinated: never said by the learner
                original="He don't like it",
                corrected="He doesn't like it",
                explanation="Third person singular needs 'doesn't'.",
                category="subject-verb agreement",
            ),
        ],
        correct_structures=[
            StructureUsed(
                structure="because-clause giving a reason",
                example="because there are many opportunities",
            ),
            StructureUsed(  # hallucinated
                structure="second conditional",
                example="If I had more money, I would move",
            ),
        ],
        useful_vocabulary=[
            VocabularyEntry(
                term="crowded", type="word", definition="too full of people",
                example="The train was really crowded this morning.",
            ),
            VocabularyEntry(
                term="a wide range of opportunities", type="collocation",
                definition="many different chances to do or achieve things",
                example="Big cities offer a wide range of opportunities.",
            ),
        ],
        suggested_vocabulary=[
            VocabularyEntry(
                term="hustle and bustle", type="idiom",
                definition="busy, noisy activity",
                example="I enjoy the hustle and bustle of the city centre.",
            ),
        ],
        improved_answer=(
            "I'd say I agree that cities can feel crowded, but I still enjoy living in one "
            "because there's such a wide range of opportunities."
        ),
    )
