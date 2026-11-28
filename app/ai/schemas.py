"""Structured outputs the LLM must produce.

Every model here is also sent to Ollama as a JSON schema (``format``), so the model's output is
constrained to this shape. Fields are deliberately required (no defaults) so the model fills them.
Validators normalise small deviations instead of failing the whole request.
"""

import math
from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, BeforeValidator, Field

from app.core.scoring import round_band

# --------------------------------------------------------------------------- helpers


def _snap_band(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("band score must be a number") from exc
    if math.isnan(number):
        raise ValueError("band score must be a number")
    return round_band(number)


BandScore = Annotated[float, BeforeValidator(_snap_band)]

GrammarCategory = Literal[
    "tense",
    "subject-verb agreement",
    "articles",
    "prepositions",
    "word order",
    "plurals and countability",
    "word form",
    "conditionals",
    "modal verbs",
    "relative clauses",
    "passive voice",
    "comparatives and superlatives",
    "sentence structure",
    "other",
]
GRAMMAR_CATEGORIES: tuple[str, ...] = get_args(GrammarCategory)

_CATEGORY_ALIASES = {
    "subject verb agreement": "subject-verb agreement",
    "agreement": "subject-verb agreement",
    "article": "articles",
    "preposition": "prepositions",
    "verb tense": "tense",
    "tenses": "tense",
    "plural": "plurals and countability",
    "plurals": "plurals and countability",
    "countability": "plurals and countability",
    "modal": "modal verbs",
    "modals": "modal verbs",
    "comparatives": "comparatives and superlatives",
    "comparative": "comparatives and superlatives",
    "passive": "passive voice",
    "relative clause": "relative clauses",
    "conditional": "conditionals",
    "syntax": "sentence structure",
    "run-on sentence": "sentence structure",
    "fragment": "sentence structure",
}


def _normalise_category(value: Any) -> str:
    if not isinstance(value, str):
        return "other"
    key = value.strip().lower().replace("_", " ")
    if key in GRAMMAR_CATEGORIES:
        return key
    return _CATEGORY_ALIASES.get(key, "other")


VocabularyType = Literal["word", "collocation", "idiom", "phrasal verb", "expression"]
VOCABULARY_TYPES: tuple[str, ...] = get_args(VocabularyType)

_VOCAB_ALIASES = {
    "phrasal verbs": "phrasal verb",
    "phrasal": "phrasal verb",
    "collocations": "collocation",
    "idioms": "idiom",
    "idiomatic expression": "idiom",
    "phrase": "expression",
    "words": "word",
}


def _normalise_vocab_type(value: Any) -> str:
    if not isinstance(value, str):
        return "expression"
    key = value.strip().lower().replace("_", " ").replace("-", " ")
    if key in VOCABULARY_TYPES:
        return key
    return _VOCAB_ALIASES.get(key, "expression")


# --------------------------------------------------------------------------- shared pieces


class VocabularyEntry(BaseModel):
    term: str
    type: Annotated[VocabularyType, BeforeValidator(_normalise_vocab_type)]
    definition: str
    example: str


class GrammarFinding(BaseModel):
    original: str
    corrected: str
    explanation: str
    category: Annotated[GrammarCategory, BeforeValidator(_normalise_category)]


class StructureUsed(BaseModel):
    structure: str
    example: str


class CriterionFeedback(BaseModel):
    # Listed first so the model gathers quotes/observations before it commits to a score.
    evidence: list[str] = Field(default_factory=list)
    score: BandScore
    summary: str
    strengths: list[str]
    improvements: list[str]


# --------------------------------------------------------------------------- evaluation


class EvaluationResult(BaseModel):
    fluency_coherence: CriterionFeedback
    lexical_resource: CriterionFeedback
    grammatical_range_accuracy: CriterionFeedback
    strengths: list[str]
    areas_for_improvement: list[str]
    grammar_issues: list[GrammarFinding]
    correct_structures: list[StructureUsed]
    useful_vocabulary: list[VocabularyEntry]
    suggested_vocabulary: list[VocabularyEntry]
    improved_answer: str


# --------------------------------------------------------------------------- other tasks


class GeneratedQuestion(BaseModel):
    text: str
    cue_points: list[str]


class GeneratedQuestions(BaseModel):
    questions: list[GeneratedQuestion]


class SampleAnswerResult(BaseModel):
    sample_answer: str
    key_features: list[str]
    useful_vocabulary: list[VocabularyEntry]


class FollowUpResult(BaseModel):
    follow_up_questions: list[str]


class TopicVocabulary(BaseModel):
    items: list[VocabularyEntry]


class Exercise(BaseModel):
    title: str
    instructions: str
    practice_items: list[str]


class FocusArea(BaseModel):
    area: str
    why_it_matters: str
    exercises: list[Exercise]


class Recommendations(BaseModel):
    summary: str
    focus_areas: list[FocusArea]
    weekly_routine: list[str]


# --------------------------------------------------------------------------- story adaptation


class CuePointPlan(BaseModel):
    cue_point: str
    what_to_say: str


class StoryAdaptation(BaseModel):
    fit: Literal["strong", "partial", "weak"]
    angle: str
    opening_line: str
    emphasise: list[str]
    details_to_change: list[str]
    cue_point_plan: list[CuePointPlan]
    useful_collocations: list[VocabularyEntry]
    watch_out: list[str]
