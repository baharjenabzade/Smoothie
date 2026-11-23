from app.ai.schemas import GrammarFinding
from app.services.grounding import MAX_ISSUES, ground_issues, ground_result
from tests.fakes import TRANSCRIPT, make_evaluation


def _finding(original, corrected="fixed"):
    return GrammarFinding(
        original=original, corrected=corrected, explanation="why", category="tense"
    )


def test_hallucinated_issues_and_structures_are_dropped():
    result = ground_result(make_evaluation(), TRANSCRIPT)
    assert [i.original for i in result.grammar_issues] == ["I am agree"]
    assert [s.example for s in result.correct_structures] == [
        "because there are many opportunities"
    ]


def test_scores_and_vocabulary_are_untouched():
    original = make_evaluation()
    result = ground_result(original, TRANSCRIPT)
    assert result.fluency_coherence.score == original.fluency_coherence.score
    assert result.useful_vocabulary == original.useful_vocabulary


def test_matching_ignores_case_whitespace_and_curly_quotes():
    transcript = "He  don’t like it, honestly."
    kept = ground_issues([_finding("he don't like it")], transcript)
    assert len(kept) == 1


def test_issue_with_identical_correction_is_dropped():
    assert ground_issues([_finding("I am agree", "I am agree")], TRANSCRIPT) == []


def test_duplicate_issues_are_collapsed():
    kept = ground_issues([_finding("I am agree"), _finding("i am agree")], TRANSCRIPT)
    assert len(kept) == 1


def test_number_of_issues_is_capped():
    transcript = " ".join(f"error{i}" for i in range(20))
    evaluation = make_evaluation().model_copy(
        update={"grammar_issues": [_finding(f"error{i}") for i in range(20)]}
    )
    assert len(ground_result(evaluation, transcript).grammar_issues) == MAX_ISSUES
