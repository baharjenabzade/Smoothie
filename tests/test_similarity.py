from app.seed_data import iter_seed_questions
from app.services.similarity import (
    Item,
    group_similar,
    keywords,
    label_for,
    most_similar,
    similarity,
)


def items(texts):
    return [Item.of(i, t) for i, t in enumerate(texts, 1)]


def test_keywords_drop_question_words_and_stem():
    assert set(keywords("How often do you go cooking at home?")) == {"cook", "home"}
    assert "hobby" in keywords("What hobbies do you have?")


def test_similar_questions_are_grouped_and_unrelated_are_not():
    its = items([
        "Do you like cooking at home?",
        "How often do you cook for yourself?",
        "What is your favourite sport?",
        "Where do you cook most of your meals?",
        "Which sports are popular in your country?",
    ])
    groups = [[i.key for i in g] for g in group_similar(its)]
    assert [1, 2, 4] in groups
    assert [3, 5] in groups


def test_label_and_most_similar():
    texts = ["Do you like cooking?", "How often do you cook?"]
    assert "Cook" in label_for(texts)
    its = items(texts + ["Describe a sport you enjoy."])
    ranked = most_similar(its[0], its)
    assert ranked and ranked[0][0].key == 2
    assert similarity(set(), {"a"}) == 0.0


def test_seed_questions_form_reasonable_groups():
    qs = [q for q in iter_seed_questions() if q["part"] == 1]
    groups = group_similar([Item.of(i, q["text"]) for i, q in enumerate(qs)])
    assert 1 < len(groups) < len(qs)  # some grouping happens, but not everything merges
    assert max(len(g) for g in groups) <= 8
