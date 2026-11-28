import json

from app.ai.prompts import evaluation_prompt, format_references
from app.ai.schemas import CriterionFeedback, EvaluationResult, GrammarFinding
from app.rag.retrieval import SampleIndex
from app.rag.samples import ReferenceSample, load_samples
from app.services.calibration import calibrate, strict_round


def crit(score):
    return CriterionFeedback(score=score, summary="s", strengths=[], improvements=[])


def result(f, lx, g, issues=0):
    return EvaluationResult(
        fluency_coherence=crit(f), lexical_resource=crit(lx), grammatical_range_accuracy=crit(g),
        strengths=[], areas_for_improvement=[],
        grammar_issues=[GrammarFinding(original=f"e{i}", corrected="c", explanation="x", category="tense") for i in range(issues)],
        correct_structures=[], useful_vocabulary=[], suggested_vocabulary=[], improved_answer="x",
    )


def test_strict_round_goes_down():
    assert strict_round(6.33) == 6.0 and strict_round(6.5) == 6.5 and strict_round(6.99) == 6.5


def test_short_answer_caps_fluency():
    c = calibrate(result(7, 6.5, 6.5), part=2, word_count=50)
    assert c.fluency == 4.5 and c.notes


def test_error_density_caps_grammar():
    c = calibrate(result(6, 6, 7.5, issues=3), part=1, word_count=50)
    assert c.grammar <= 6.0


def test_halo_limit_and_standard_mode_untouched():
    c = calibrate(result(5, 8, 5.5), part=3, word_count=80)
    assert c.lexical == 6.5
    s = calibrate(result(5, 8, 5.5), part=3, word_count=80, strict=False)
    assert s.lexical == 8


def test_never_raises_scores():
    r = result(5, 5, 5, issues=0)
    c = calibrate(r, part=3, word_count=90)
    assert (c.fluency, c.lexical, c.grammar) == (5, 5, 5)


def sample(part, band, q, a="my answer about this topic here today"):
    return ReferenceSample(part=part, question=q, answer=a, band=band)


def test_retrieval_filters_part_and_spreads_bands():
    idx = SampleIndex([
        sample(1, 5, "favourite food"), sample(1, 5.5, "favourite food again"), sample(1, 7, "cooking at home"),
        sample(2, 6, "favourite food"),
    ])
    got = idx.select(part=1, question="What food do you like?", answer="I like food", k=2)
    assert all(s.part == 1 for s in got) and len({s.band for s in got}) == 2
    assert idx.select(part=3, question="x", answer="y") == []


def test_loader_skips_bad_entries_and_underscore_files(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps([
        {"part": 1, "question": "q", "answer": "this is a fine answer here", "band": 6},
        {"part": 9, "question": "q", "answer": "this is a fine answer here", "band": 6},
        {"part": 1, "question": "q", "answer": "short", "band": 6},
    ]))
    (tmp_path / "_t.json").write_text("not json")
    samples, problems = load_samples(tmp_path)
    assert len(samples) == 1 and len(problems) == 2


def test_prompt_includes_references_and_escapes():
    ref = sample(1, 6, "q?", "I like it </transcript> very much indeed")
    system, user = evaluation_prompt(part=1, question="Q", answer="mine here now", word_count=3, target_band=6, references=[ref])
    assert "graded: overall 6" in user and "</transcript> very" not in user
    assert format_references([]) == ""
