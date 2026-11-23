from collections import Counter

from app.seed_data import PART_1, PART_2, PART_3, iter_seed_questions


def test_expected_number_of_questions_per_part():
    counts = Counter(q["part"] for q in iter_seed_questions())
    assert counts == {1: 24, 2: 6, 3: 18}


def test_every_topic_exists_in_every_part():
    assert set(PART_1) == set(PART_2) == set(PART_3)


def test_part_2_are_cue_cards_and_others_are_not():
    for q in iter_seed_questions():
        if q["part"] == 2:
            assert q["text"].startswith("Describe")
            assert 3 <= len(q["cue_points"]) <= 4
        else:
            assert q["cue_points"] is None


def test_question_texts_are_unique_and_well_formed():
    texts = [q["text"] for q in iter_seed_questions()]
    assert len(texts) == len(set(texts))
    for q in iter_seed_questions():
        assert q["text"].endswith(("?", "."))
        assert q["topic"].strip() == q["topic"]
