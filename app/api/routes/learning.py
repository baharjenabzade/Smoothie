from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.ai.schemas import GRAMMAR_CATEGORIES, Recommendations
from app.api.deps import LLM, CurrentUser, DbSession
from app.core.errors import NotFoundError
from app.models import GrammarIssue, VocabularyItem
from app.schemas.learning import (
    GrammarIssueRead,
    TopicVocabularyRequest,
    TopicVocabularyResponse,
    VocabularyItemRead,
)
from app.schemas.progress import WeaknessReport
from app.services import learning as learning_service
from app.services.progress import compute_weaknesses

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/vocabulary", response_model=list[VocabularyItemRead])
def list_vocabulary(
    db: DbSession,
    user: CurrentUser,
    topic: Annotated[str | None, Query(max_length=100)] = None,
    item_type: Annotated[
        Literal["word", "collocation", "idiom", "phrasal verb", "expression"] | None, Query()
    ] = None,
    source: Annotated[Literal["answer", "suggestion", "topic"] | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=100, description="Search in the term")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(VocabularyItem).where(VocabularyItem.user_id == user.id)
    if topic:
        stmt = stmt.where(func.lower(VocabularyItem.topic) == topic.strip().lower())
    if item_type:
        stmt = stmt.where(VocabularyItem.item_type == item_type)
    if source:
        stmt = stmt.where(VocabularyItem.source == source)
    if q:
        stmt = stmt.where(VocabularyItem.term_key.contains(q.strip().lower(), autoescape=True))
    stmt = stmt.order_by(VocabularyItem.id.desc()).limit(limit).offset(offset)
    return [VocabularyItemRead.model_validate(row) for row in db.scalars(stmt)]


@router.delete("/vocabulary/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocabulary_item(item_id: int, db: DbSession, user: CurrentUser) -> None:
    item = db.scalar(
        select(VocabularyItem).where(VocabularyItem.id == item_id, VocabularyItem.user_id == user.id)
    )
    if item is None:
        raise NotFoundError("Vocabulary item not found")
    db.delete(item)
    db.commit()


@router.post("/topic-vocabulary", response_model=TopicVocabularyResponse)
def topic_vocabulary(payload: TopicVocabularyRequest, db: DbSession, llm: LLM, user: CurrentUser):
    """Generate a topic word list (collocations, idioms, phrasal verbs). Optionally save it."""
    items, saved = learning_service.topic_vocabulary(
        db,
        llm,
        user,
        topic=payload.topic,
        count=payload.count,
        target_band=payload.target_band or user.target_band,
        save=payload.save,
    )
    return TopicVocabularyResponse(topic=payload.topic.strip(), items=items, saved=saved)


@router.get("/grammar-issues", response_model=list[GrammarIssueRead])
def list_grammar_issues(
    db: DbSession,
    user: CurrentUser,
    category: Annotated[
        str | None,
        Query(description="One of: " + ", ".join(GRAMMAR_CATEGORIES)),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(GrammarIssue).where(GrammarIssue.user_id == user.id)
    if category:
        stmt = stmt.where(GrammarIssue.category == category.strip().lower())
    stmt = stmt.order_by(GrammarIssue.id.desc()).limit(limit).offset(offset)
    return [GrammarIssueRead.model_validate(row) for row in db.scalars(stmt)]


@router.get("/weaknesses", response_model=WeaknessReport)
def weaknesses(db: DbSession, user: CurrentUser):
    """Recurring weaknesses computed from the learner's saved evaluations (no AI call)."""
    return compute_weaknesses(db, user.id)


@router.get("/recommendations", response_model=Recommendations)
def recommendations(db: DbSession, llm: LLM, user: CurrentUser):
    """Personalised exercises and a weekly routine, generated from the learner's weaknesses."""
    return learning_service.build_recommendations(db, llm, user)
