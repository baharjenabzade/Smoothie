import pytest
from pydantic import ValidationError

from app.ai import schemas
from app.ai.schemas import CriterionFeedback, GrammarFinding, VocabularyEntry


def _criterion(score):
    return CriterionFeedback(score=score, summary="s", strengths=[], improvements=[])


@pytest.mark.parametrize(
    "raw, expected",
    [(6.2, 6.0), (6.3, 6.5), ("7", 7.0), (11, 9.0), (-2, 0.0), (6.75, 7.0)],
)
def test_band_scores_are_snapped_to_half_bands(raw, expected):
    assert _criterion(raw).score == expected


@pytest.mark.parametrize("bad", ["abc", None, float("nan")])
def test_non_numeric_band_is_rejected(bad):
    with pytest.raises(ValidationError):
        _criterion(bad)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("tense", "tense"),
        ("Verb Tense", "tense"),
        ("Subject_Verb Agreement", "subject-verb agreement"),
        ("article", "articles"),
        ("Prepositions", "prepositions"),
        ("something unexpected", "other"),
        (None, "other"),
    ],
)
def test_grammar_category_is_normalised(raw, expected):
    finding = GrammarFinding(original="a", corrected="b", explanation="c", category=raw)
    assert finding.category == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("word", "word"),
        ("Phrasal_Verb", "phrasal verb"),
        ("phrasal verbs", "phrasal verb"),
        ("Idioms", "idiom"),
        ("collocations", "collocation"),
        ("whatever", "expression"),
    ],
)
def test_vocabulary_type_is_normalised(raw, expected):
    entry = VocabularyEntry(term="t", type=raw, definition="d", example="e")
    assert entry.type == expected


@pytest.mark.parametrize(
    "model",
    [
        schemas.EvaluationResult,
        schemas.GeneratedQuestions,
        schemas.SampleAnswerResult,
        schemas.FollowUpResult,
        schemas.TopicVocabulary,
        schemas.Recommendations,
    ],
)
def test_models_produce_a_json_schema_for_ollama(model):
    schema = model.model_json_schema()
    assert schema["type"] == "object"
    assert schema["required"]  # every field is required so the model fills them all


def test_evaluation_schema_requires_all_three_criteria():
    required = set(schemas.EvaluationResult.model_json_schema()["required"])
    assert {"fluency_coherence", "lexical_resource", "grammatical_range_accuracy"} <= required
