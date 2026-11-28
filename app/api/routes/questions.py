from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.deps import LLM, CurrentUser, DbSession
from app.core.errors import NotFoundError
from app.models import Question
from app.schemas.group import (
    ImportRequest,
    ImportResult,
    QuestionGroupRead,
    SimilarQuestion,
)
from app.schemas.question import QuestionGenerateRequest, QuestionRead, TopicSummary
from app.services import question_import
from app.services import questions as question_service
from app.services import similarity as sim

router = APIRouter(prefix="/questions", tags=["questions"])


def _filtered(part: int | None, topic: str | None, q: str | None):
    stmt = select(Question)
    if part is not None:
        stmt = stmt.where(Question.part == part)
    if topic:
        stmt = stmt.where(func.lower(Question.topic) == topic.strip().lower())
    if q:
        stmt = stmt.where(func.lower(Question.text).contains(q.strip().lower(), autoescape=True))
    return stmt


@router.get("", response_model=list[QuestionRead])
def list_questions(
    db: DbSession,
    user: CurrentUser,
    part: Annotated[int | None, Query(ge=1, le=3)] = None,
    topic: Annotated[str | None, Query(max_length=100)] = None,
    q: Annotated[str | None, Query(max_length=100, description="Search in question text")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = _filtered(part, topic, q).order_by(Question.id).limit(limit).offset(offset)
    return [QuestionRead.model_validate(row) for row in db.scalars(stmt)]


@router.get("/topics", response_model=list[TopicSummary])
def list_topics(db: DbSession, user: CurrentUser):
    return question_service.topic_summaries(db)


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
def import_questions(payload: ImportRequest, db: DbSession, user: CurrentUser):
    """Add many questions at once (from your own notes or files). Duplicates are skipped."""
    return question_import.import_questions(db, user, payload.items, default_topic=payload.default_topic, auto_topic=payload.auto_topic)


@router.get("/groups", response_model=list[QuestionGroupRead])
def similar_groups(
    db: DbSession,
    user: CurrentUser,
    part: Annotated[int, Query(ge=1, le=3)],
    min_size: Annotated[int, Query(ge=2, le=20)] = 2,
    threshold: Annotated[float, Query(ge=0.2, le=0.9)] = 0.4,
):
    """Automatically group questions of one part that ask about the same thing."""
    rows = list(db.scalars(select(Question).where(Question.part == part).order_by(Question.id).limit(3000)))
    by_id = {q.id: q for q in rows}
    groups = [g for g in sim.group_similar([sim.Item.of(q.id, q.text) for q in rows], threshold) if len(g) >= min_size]
    out = []
    for g in sorted(groups, key=lambda g: (-len(g), g[0].key))[:80]:
        qs = [by_id[i.key] for i in g]
        out.append(
            QuestionGroupRead(
                label=sim.label_for([i.text for i in g]),
                size=len(g),
                topics=sorted({q.topic for q in qs}),
                questions=[QuestionRead.model_validate(q) for q in qs],
            )
        )
    return out


@router.get("/{question_id}/similar", response_model=list[SimilarQuestion])
def similar_questions(question_id: int, db: DbSession, user: CurrentUser, limit: Annotated[int, Query(ge=1, le=20)] = 8):
    question = db.get(Question, question_id)
    if question is None:
        raise NotFoundError("Question not found")
    pool = list(db.scalars(select(Question).where(Question.part == question.part).limit(3000)))
    by_id = {q.id: q for q in pool}
    ranked = sim.most_similar(sim.Item.of(question.id, question.text), [sim.Item.of(q.id, q.text) for q in pool], limit)
    return [SimilarQuestion(question=QuestionRead.model_validate(by_id[i.key]), score=round(score, 2)) for i, score in ranked]


@router.get("/random", response_model=QuestionRead)
def random_question(
    db: DbSession,
    user: CurrentUser,
    part: Annotated[int | None, Query(ge=1, le=3)] = None,
    topic: Annotated[str | None, Query(max_length=100)] = None,
):
    question = db.scalar(_filtered(part, topic, None).order_by(func.random()).limit(1))
    if question is None:
        raise NotFoundError("No questions match those filters")
    return QuestionRead.model_validate(question)


@router.post("/generate", response_model=list[QuestionRead], status_code=status.HTTP_201_CREATED)
def generate_questions(payload: QuestionGenerateRequest, db: DbSession, llm: LLM, user: CurrentUser):
    """Ask the AI for new practice questions on a topic and save them to the question bank."""
    created = question_service.generate_questions(
        db, llm, user, part=payload.part, topic=payload.topic, count=payload.count
    )
    return [QuestionRead.model_validate(q) for q in created]


@router.get("/{question_id}", response_model=QuestionRead)
def get_question(question_id: int, db: DbSession, user: CurrentUser):
    question = db.get(Question, question_id)
    if question is None:
        raise NotFoundError("Question not found")
    return QuestionRead.model_validate(question)
