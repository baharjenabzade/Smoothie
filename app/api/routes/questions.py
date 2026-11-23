from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.deps import LLM, CurrentUser, DbSession
from app.core.errors import NotFoundError
from app.models import Question
from app.schemas.question import QuestionGenerateRequest, QuestionRead, TopicSummary
from app.services import questions as question_service

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
