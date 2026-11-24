"""End-to-end API tests: real FastAPI app + in-memory SQLite + a fake LLM."""

import pytest

for _module in ("fastapi", "sqlalchemy", "httpx", "bcrypt", "jwt", "pydantic_settings", "email_validator"):
    pytest.importorskip(_module)

from app.ai.schemas import (  # noqa: E402
    EvaluationResult,
    Exercise,
    FocusArea,
    FollowUpResult,
    GeneratedQuestion,
    GeneratedQuestions,
    Recommendations,
    SampleAnswerResult,
    TopicVocabulary,
    VocabularyEntry,
)
from app.core.errors import LLMError  # noqa: E402
from tests.fakes import TRANSCRIPT, make_evaluation  # noqa: E402

API = "/api/v1"
QUESTION = "Do you like living in a big city?"


def register_and_login(client, email="learner@example.com"):
    r = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": "Test Learner"},
    )
    assert r.status_code == 201, r.text
    r = client.post(f"{API}/auth/login", data={"username": email, "password": "supersecret1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return register_and_login(client)


@pytest.fixture()
def llm(fake_llm):
    fake_llm.responses[EvaluationResult] = make_evaluation()
    return fake_llm


def create_session(client, auth, part=1, topic="Hometown"):
    r = client.post(f"{API}/practice/sessions", json={"part": part, "topic": topic}, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def submit(client, auth, session_id, **body):
    body.setdefault("question_text", QUESTION)
    body.setdefault("answer_text", TRANSCRIPT)
    return client.post(f"{API}/practice/sessions/{session_id}/answers", json=body, headers=auth)


# ------------------------------------------------------------------ auth


def test_register_login_and_profile(client):
    r = client.post(
        f"{API}/auth/register", json={"email": "Learner@Example.com", "password": "supersecret1"}
    )
    assert r.status_code == 201
    assert r.json()["email"] == "learner@example.com"
    assert "password" not in r.text

    dup = client.post(
        f"{API}/auth/register", json={"email": "learner@example.com", "password": "supersecret1"}
    )
    assert dup.status_code == 409

    bad = client.post(
        f"{API}/auth/login", data={"username": "learner@example.com", "password": "wrong-password"}
    )
    assert bad.status_code == 401

    headers = register_and_login(client, "other@example.com")
    assert client.get(f"{API}/auth/me", headers=headers).json()["email"] == "other@example.com"
    patched = client.patch(f"{API}/auth/me", json={"target_band": 7.5}, headers=headers)
    assert patched.json()["target_band"] == 7.5


def test_weak_password_is_rejected(client):
    r = client.post(f"{API}/auth/register", json={"email": "a@example.com", "password": "short"})
    assert r.status_code == 422


@pytest.mark.parametrize(
    "path", ["/dashboard", "/questions", "/practice/sessions", "/learning/vocabulary"]
)
def test_endpoints_require_a_token(client, path):
    assert client.get(f"{API}{path}").status_code == 401
    assert client.get(f"{API}{path}", headers={"Authorization": "Bearer nonsense"}).status_code == 401


# ------------------------------------------------------------------ questions


def test_browse_seeded_questions(client, auth, seeded):
    assert seeded == 48

    topics = client.get(f"{API}/questions/topics", headers=auth).json()
    travel = next(t for t in topics if t["topic"] == "Travel")
    assert travel["parts"] == [1, 2, 3]

    part2 = client.get(f"{API}/questions", params={"part": 2, "limit": 100}, headers=auth).json()
    assert len(part2) == 6 and all(q["cue_points"] for q in part2)

    hobbies = client.get(f"{API}/questions", params={"topic": "hobbies"}, headers=auth).json()
    assert hobbies and all(q["topic"] == "Hobbies" for q in hobbies)

    random_q = client.get(f"{API}/questions/random", params={"part": 3}, headers=auth).json()
    assert random_q["part"] == 3
    one = client.get(f"{API}/questions/{random_q['id']}", headers=auth)
    assert one.json()["text"] == random_q["text"]
    assert client.get(f"{API}/questions/999999", headers=auth).status_code == 404
    assert (
        client.get(f"{API}/questions/random", params={"topic": "Nope"}, headers=auth).status_code
        == 404
    )


def test_generate_questions_saves_new_unique_ones(client, auth, llm):
    llm.responses[GeneratedQuestions] = GeneratedQuestions(
        questions=[
            GeneratedQuestion(text="What do you usually do at weekends?", cue_points=[]),
            GeneratedQuestion(text="what do you usually do at weekends?", cue_points=[]),
        ]
    )
    r = client.post(
        f"{API}/questions/generate", json={"part": 1, "topic": "Weekends", "count": 2}, headers=auth
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert len(created) == 1 and created[0]["is_ai_generated"] is True

    # Asking again produces only duplicates, which is reported as an error rather than silence.
    again = client.post(
        f"{API}/questions/generate", json={"part": 1, "topic": "Weekends", "count": 2}, headers=auth
    )
    assert again.status_code == 502


# ------------------------------------------------------------------ practice + evaluation


def test_submit_answer_evaluates_and_stores(client, auth, llm):
    session_id = create_session(client, auth)
    r = submit(client, auth, session_id)
    assert r.status_code == 201, r.text
    answer = r.json()

    assert answer["word_count"] == 20
    ev = answer["evaluation"]
    # (6.0 + 6.5 + 6.5) / 3 = 6.33 -> rounds to 6.5
    assert (ev["fluency_score"], ev["lexical_score"], ev["grammar_score"]) == (6.0, 6.5, 6.5)
    assert ev["overall_band"] == 6.5
    assert "Pronunciation is not assessed" in ev["disclaimer"]
    assert ev["model_name"] == "fake-model"

    feedback = ev["feedback"]
    assert [i["original"] for i in feedback["grammar_issues"]] == ["I am agree"]  # hallucination dropped
    assert len(feedback["correct_structures"]) == 1

    # The learner's text is passed to the model inside the transcript delimiters.
    schema, system, user = llm.calls[0]
    assert schema is EvaluationResult and "<transcript>" in user and TRANSCRIPT in user

    detail = client.get(f"{API}/practice/sessions/{session_id}", headers=auth).json()
    assert detail["answer_count"] == 1 and detail["average_band"] == 6.5
    assert detail["answers"][0]["evaluation"]["overall_band"] == 6.5


def test_answer_can_reference_a_question_from_the_bank(client, auth, llm, seeded):
    question = client.get(f"{API}/questions/random", params={"part": 1}, headers=auth).json()
    session_id = create_session(client, auth, part=1, topic=None)
    r = client.post(
        f"{API}/practice/sessions/{session_id}/answers",
        json={"question_id": question["id"], "answer_text": TRANSCRIPT},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["question_text"] == question["text"]

    # A Part 3 question cannot be answered inside a Part 1 session.
    part3 = client.get(f"{API}/questions/random", params={"part": 3}, headers=auth).json()
    mismatch = client.post(
        f"{API}/practice/sessions/{session_id}/answers",
        json={"question_id": part3["id"], "answer_text": TRANSCRIPT},
        headers=auth,
    )
    assert mismatch.status_code == 422


def test_invalid_answer_requests(client, auth, llm):
    session_id = create_session(client, auth)
    url = f"{API}/practice/sessions/{session_id}/answers"

    no_question = client.post(url, json={"answer_text": TRANSCRIPT}, headers=auth)
    assert no_question.status_code == 422
    blank = client.post(url, json={"question_text": QUESTION, "answer_text": "   "}, headers=auth)
    assert blank.status_code == 422
    too_short = submit(client, auth, session_id, answer_text="Yes.")
    assert too_short.status_code == 422
    assert llm.calls == []  # the model is never called for invalid input


def test_model_failure_returns_error_and_saves_nothing(client, auth, llm):
    session_id = create_session(client, auth)
    llm.error = LLMError("The AI model server is not reachable.", 503)
    r = submit(client, auth, session_id)
    assert r.status_code == 503
    assert "not reachable" in r.json()["detail"]

    detail = client.get(f"{API}/practice/sessions/{session_id}", headers=auth).json()
    assert detail["answer_count"] == 0
    assert client.get(f"{API}/dashboard", headers=auth).json()["total_answers"] == 0


def test_sessions_are_private_to_their_owner(client, auth, llm):
    session_id = create_session(client, auth)
    other = register_and_login(client, "intruder@example.com")
    assert client.get(f"{API}/practice/sessions/{session_id}", headers=other).status_code == 404
    assert submit(client, other, session_id).status_code == 404
    assert client.delete(f"{API}/practice/sessions/{session_id}", headers=other).status_code == 404
    assert client.get(f"{API}/practice/sessions", headers=other).json() == []


def test_delete_session(client, auth, llm):
    session_id = create_session(client, auth)
    assert submit(client, auth, session_id).status_code == 201
    assert client.delete(f"{API}/practice/sessions/{session_id}", headers=auth).status_code == 204
    assert client.get(f"{API}/practice/sessions/{session_id}", headers=auth).status_code == 404
    assert client.get(f"{API}/dashboard", headers=auth).json()["total_sessions"] == 0


def test_sample_answer_and_follow_up(client, auth, fake_llm):
    fake_llm.responses[SampleAnswerResult] = SampleAnswerResult(
        sample_answer="Well, I'd say I really enjoy it...",
        key_features=["Uses a linking phrase"],
        useful_vocabulary=[],
    )
    fake_llm.responses[FollowUpResult] = FollowUpResult(
        follow_up_questions=["What do you dislike about it?", "Would you ever move?"]
    )
    sample = client.post(
        f"{API}/practice/sample-answer",
        json={"part": 1, "question_text": QUESTION, "target_band": 6.5},
        headers=auth,
    )
    assert sample.status_code == 200 and sample.json()["sample_answer"].startswith("Well")
    assert "Band 6-6.5" in fake_llm.calls[0][1]  # the system prompt was calibrated to the band

    follow = client.post(
        f"{API}/practice/follow-up",
        json={"question_text": QUESTION, "answer_text": TRANSCRIPT},
        headers=auth,
    )
    assert len(follow.json()["follow_up_questions"]) == 2


# ------------------------------------------------------------------ learning + progress


def test_vocabulary_is_saved_filtered_and_not_duplicated(client, auth, llm):
    session_id = create_session(client, auth, topic="Hometown")
    assert submit(client, auth, session_id).status_code == 201

    items = client.get(f"{API}/learning/vocabulary", params={"limit": 100}, headers=auth).json()
    assert {i["term"] for i in items} == {"crowded", "a wide range of opportunities", "hustle and bustle"}
    assert all(i["topic"] == "Hometown" and i["times_seen"] == 1 for i in items)

    suggestions = client.get(
        f"{API}/learning/vocabulary", params={"source": "suggestion"}, headers=auth
    ).json()
    assert [i["term"] for i in suggestions] == ["hustle and bustle"]
    idioms = client.get(f"{API}/learning/vocabulary", params={"item_type": "idiom"}, headers=auth)
    assert len(idioms.json()) == 1
    assert len(client.get(f"{API}/learning/vocabulary", params={"q": "CROWD"}, headers=auth).json()) == 1

    # The same answer again does not duplicate terms; it counts how often they came up.
    assert submit(client, auth, session_id).status_code == 201
    items = client.get(f"{API}/learning/vocabulary", params={"limit": 100}, headers=auth).json()
    assert len(items) == 3 and all(i["times_seen"] == 2 for i in items)

    gone = client.delete(f"{API}/learning/vocabulary/{items[0]['id']}", headers=auth)
    assert gone.status_code == 204
    assert len(client.get(f"{API}/learning/vocabulary", params={"limit": 100}, headers=auth).json()) == 2


def test_topic_vocabulary_can_be_saved(client, auth, fake_llm):
    fake_llm.responses[TopicVocabulary] = TopicVocabulary(
        items=[
            VocabularyEntry(
                term="off the beaten track", type="idiom",
                definition="away from popular tourist places",
                example="We stayed in a village off the beaten track.",
            )
        ]
    )
    preview = client.post(
        f"{API}/learning/topic-vocabulary", json={"topic": "Travel", "count": 5}, headers=auth
    )
    assert preview.status_code == 200 and preview.json()["saved"] == 0
    assert client.get(f"{API}/learning/vocabulary", headers=auth).json() == []

    saved = client.post(
        f"{API}/learning/topic-vocabulary",
        json={"topic": "Travel", "count": 5, "save": True},
        headers=auth,
    )
    assert saved.json()["saved"] == 1
    rows = client.get(f"{API}/learning/vocabulary", params={"topic": "travel"}, headers=auth).json()
    assert rows[0]["source"] == "topic"


def test_grammar_issues_weaknesses_and_recommendations(client, auth, llm):
    # No data yet: weaknesses are empty and recommendations explain why they are unavailable.
    empty = client.get(f"{API}/learning/weaknesses", headers=auth).json()
    assert empty["evaluations_analyzed"] == 0 and empty["weakest_criterion"] is None
    assert client.get(f"{API}/learning/recommendations", headers=auth).status_code == 409

    session_id = create_session(client, auth)
    assert submit(client, auth, session_id).status_code == 201

    issues = client.get(f"{API}/learning/grammar-issues", headers=auth).json()
    assert [(i["category"], i["original"], i["corrected"]) for i in issues] == [
        ("word form", "I am agree", "I agree")
    ]
    assert client.get(
        f"{API}/learning/grammar-issues", params={"category": "tense"}, headers=auth
    ).json() == []

    report = client.get(f"{API}/learning/weaknesses", headers=auth).json()
    assert report["evaluations_analyzed"] == 1
    assert report["weakest_criterion"] == "fluency_coherence"  # 6.0 vs 6.5 / 6.5
    assert report["criterion_averages"]["lexical_resource"] == 6.5
    assert report["top_grammar_categories"][0]["category"] == "word form"

    llm.responses[Recommendations] = Recommendations(
        summary="Work on developing your ideas.",
        focus_areas=[
            FocusArea(
                area="Fluency and coherence",
                why_it_matters="Longer, linked answers raise this score.",
                exercises=[
                    Exercise(title="PEEL answers", instructions="Answer aloud...", practice_items=["Q1"])
                ],
            )
        ],
        weekly_routine=["Mon: record two Part 1 answers"],
    )
    rec = client.get(f"{API}/learning/recommendations", headers=auth)
    assert rec.status_code == 200 and rec.json()["focus_areas"][0]["area"] == "Fluency and coherence"
    # The model is given the learner's real diagnostics, not generic text.
    _, _, user_prompt = llm.calls[-1]
    assert "word form" in user_prompt and "fluency_coherence" in user_prompt


def test_dashboard_summarises_progress(client, auth, llm):
    empty = client.get(f"{API}/dashboard", headers=auth).json()
    assert empty["total_sessions"] == 0 and empty["average_band"] is None and empty["trend"] == []

    session_id = create_session(client, auth)
    assert submit(client, auth, session_id).status_code == 201
    llm.responses[EvaluationResult] = make_evaluation(fluency=7.0, lexical=7.0, grammar=7.0)
    assert submit(client, auth, session_id).status_code == 201

    data = client.get(f"{API}/dashboard", headers=auth).json()
    assert data["total_sessions"] == 1 and data["total_answers"] == 2
    assert data["average_band"] == 6.75  # mean of 6.5 and 7.0
    assert data["best_band"] == 7.0 and data["latest_band"] == 7.0
    assert [p["overall_band"] for p in data["trend"]] == [6.5, 7.0]  # oldest first
    assert data["vocabulary_count"] == 3
    assert data["recent_sessions"][0]["id"] == session_id
    assert data["recent_sessions"][0]["average_band"] == 7.0  # round_band(6.75)


def test_web_ui_is_served_without_shadowing_the_api(client):
    page = client.get("/")
    assert page.status_code == 200 and "Smoothies" in page.text and 'id="smoothie"' in page.text
    app_page = client.get("/app/")
    assert app_page.status_code == 200 and "../js/main.js" in app_page.text
    assert "javascript" in client.get("/js/smoothie.js").headers["content-type"]
    script = client.get("/js/main.js")
    assert script.status_code == 200 and "javascript" in script.headers["content-type"]
    assert "text/css" in client.get("/css/styles.css").headers["content-type"]
    assert client.get("/docs").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get(f"{API}/dashboard").status_code == 401  # API routes still win


def test_health_endpoints(client, fake_llm):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/ai").json()["model_available"] is True
