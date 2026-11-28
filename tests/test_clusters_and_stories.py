import pytest

for _module in ("fastapi", "sqlalchemy", "httpx", "bcrypt", "jwt", "pydantic_settings", "email_validator"):
    pytest.importorskip(_module)

from app.ai.schemas import CuePointPlan, StoryAdaptation, VocabularyEntry
from tests.test_api_flow import API, register_and_login

BODY = "I started learning graphic design online because I wanted a practical skill and I did not want to spend much money on courses."


@pytest.fixture()
def auth(client):
    return register_and_login(client)


def make_story(client, auth, **kw):
    payload = {"title": "Learning design online", "body": BODY, "clusters": ["education", "technology"], **kw}
    return client.post(f"{API}/stories", json=payload, headers=auth)


def test_clusters_endpoint(client, auth, seeded):
    r = client.get(f"{API}/clusters", headers=auth)
    assert r.status_code == 200
    tech = next(c for c in r.json() if c["slug"] == "technology")
    gadget = next(t for t in tech["topics"] if t["topic"] == "Gadget you own")
    assert gadget["counts"]["2"] == 1 and "money" in gadget["also_in"]


def test_story_crud_validation_and_ownership(client, auth):
    created = make_story(client, auth)
    assert created.status_code == 201, created.text
    sid = created.json()["id"]
    assert created.json()["word_count"] > 15

    assert make_story(client, auth, clusters=["bogus"]).status_code == 422
    assert make_story(client, auth, body="too short").status_code == 422

    updated = client.put(f"{API}/stories/{sid}", json={"title": "New", "body": BODY, "clusters": ["work"]}, headers=auth)
    assert updated.json()["clusters"] == ["work"]

    other = register_and_login(client, "other@example.com")
    assert client.get(f"{API}/stories/{sid}", headers=other).status_code == 404
    assert client.get(f"{API}/stories", headers=other).json() == []

    assert client.delete(f"{API}/stories/{sid}", headers=auth).status_code == 204
    assert client.get(f"{API}/stories/{sid}", headers=auth).status_code == 404


def test_matches_and_suggestions(client, auth, seeded):
    sid = make_story(client, auth).json()["id"]
    matches = client.get(f"{API}/stories/{sid}/matches", headers=auth).json()
    topics = [m["question"]["topic"] for m in matches["matches"]]
    assert "Skill you learned" in topics and "Online learning" in topics
    assert all(m["question"]["part"] == 2 for m in matches["matches"])

    skill = next(m["question"]["id"] for m in matches["matches"] if m["question"]["topic"] == "Skill you learned")
    sug = client.get(f"{API}/stories/suggest", params={"question_id": skill}, headers=auth).json()
    assert sug and sug[0]["story_id"] == sid


def test_adapt_story(client, auth, seeded, fake_llm):
    fake_llm.responses[StoryAdaptation] = StoryAdaptation(
        fit="strong", angle="Focus on the skill", opening_line="One skill I'm proud of is graphic design.",
        emphasise=["practice"], details_to_change=["name the course"],
        cue_point_plan=[CuePointPlan(cue_point="what the skill is", what_to_say="graphic design")],
        useful_collocations=[VocabularyEntry(term="pick up", type="phrasal verb", definition="learn casually", example="I picked up Spanish.")],
        watch_out=[],
    )
    sid = make_story(client, auth).json()["id"]
    qid = client.get(f"{API}/questions", params={"part": 2, "topic": "Skill you learned"}, headers=auth).json()[0]["id"]
    r = client.post(f"{API}/stories/{sid}/adapt", json={"question_id": qid}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["fit"] == "strong"
    assert "graphic design" in fake_llm.calls[-1][2]
    assert client.post(f"{API}/stories/{sid}/adapt", json={"question_id": 99999}, headers=auth).status_code == 404


def test_import_questions_dedupes_and_auto_topics(client, auth, seeded):
    items = [
        {"part": 1, "text": "Do you enjoy playing board games with friends?"},
        {"part": 1, "text": "How often do you play board games at home?"},
        {"part": 1, "text": "Where is your hometown, and what is it like?"},  # already seeded
        {"part": 2, "text": "Describe a game you played as a child.", "cue_points": ["what it was", "who played", "why you liked it"]},
        {"part": 9, "text": "bad part"},
        "not an object",
    ]
    r = client.post(f"{API}/questions/import", json={"items": items, "auto_topic": True}, headers=auth)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["created"] == 3 and data["skipped_duplicates"] == 1 and data["skipped_invalid"] == 2
    assert any("Board" in t or "Game" in t for t in data["topics"])
    again = client.post(f"{API}/questions/import", json={"items": items}, headers=auth).json()
    assert again["created"] == 0 and again["skipped_duplicates"] == 4


def test_similar_questions_and_auto_groups(client, auth, seeded):
    qid = client.get(f"{API}/questions", params={"part": 1, "topic": "Food and Cooking"}, headers=auth).json()[0]["id"]
    sims = client.get(f"{API}/questions/{qid}/similar", headers=auth)
    assert sims.status_code == 200 and isinstance(sims.json(), list)
    groups = client.get(f"{API}/questions/groups", params={"part": 1}, headers=auth).json()
    assert groups and all(g["size"] >= 2 and len(g["questions"]) == g["size"] for g in groups)


def test_custom_groups_crud_and_resolution(client, auth, seeded):
    q3 = client.get(f"{API}/questions", params={"part": 3, "topic": "Travel"}, headers=auth).json()[0]["id"]
    created = client.post(f"{API}/groups", json={"name": "My trip topics", "topics": ["Hobbies", "Useful website"], "question_ids": [q3]}, headers=auth)
    assert created.status_code == 201, created.text
    gid = created.json()["id"]
    assert created.json()["question_count"] >= 8

    detail = client.get(f"{API}/groups/{gid}", headers=auth).json()
    assert {q["topic"] for q in detail["questions"]} == {"Hobbies", "Useful website", "Travel"}
    only2 = client.get(f"{API}/groups/{gid}", params={"part": 2}, headers=auth).json()
    assert all(q["part"] == 2 for q in only2["questions"])

    other = register_and_login(client, "other2@example.com")
    assert client.get(f"{API}/groups/{gid}", headers=other).status_code == 404
    assert client.post(f"{API}/groups", json={"name": " ", "topics": []}, headers=auth).status_code == 422

    upd = client.put(f"{API}/groups/{gid}", json={"name": "Renamed", "topics": ["Hobbies"], "question_ids": []}, headers=auth)
    assert upd.json()["name"] == "Renamed"
    assert client.delete(f"{API}/groups/{gid}", headers=auth).status_code == 204
    assert client.get(f"{API}/groups", headers=auth).json() == []
