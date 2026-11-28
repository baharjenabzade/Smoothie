from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.ai.schemas import StoryAdaptation
from app.api.deps import LLM, CurrentUser, DbSession
from app.core.errors import AppError, NotFoundError
from app.models import Question, Story
from app.schemas.story import (
    AdaptRequest,
    StoryCreate,
    StoryMatches,
    StoryRead,
    StorySuggestion,
    StoryUpdate,
)
from app.services import stories as svc

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("", response_model=list[StoryRead])
def list_stories(db: DbSession, user: CurrentUser):
    rows = db.scalars(select(Story).where(Story.user_id == user.id).order_by(Story.updated_at.desc(), Story.id.desc()))
    return [svc.to_read(s) for s in rows]


@router.post("", response_model=StoryRead, status_code=status.HTTP_201_CREATED)
def create_story(payload: StoryCreate, db: DbSession, user: CurrentUser):
    count = db.scalar(select(func.count()).select_from(Story).where(Story.user_id == user.id)) or 0
    if count >= svc.MAX_STORIES_PER_USER:
        raise AppError(f"You can keep up to {svc.MAX_STORIES_PER_USER} stories. Delete one to add another.", 422)
    story = Story(user_id=user.id, title=payload.title, body=payload.body, clusters=payload.clusters)
    db.add(story)
    db.commit()
    db.refresh(story)
    return svc.to_read(story)


@router.get("/suggest", response_model=list[StorySuggestion])
def suggest_stories(db: DbSession, user: CurrentUser, question_id: Annotated[int, Query(ge=1)]):
    """Which of my stories could answer this cue card?"""
    question = db.get(Question, question_id)
    if question is None:
        raise NotFoundError("Question not found")
    return svc.suggest_for_question(db, user, question)


@router.get("/{story_id}", response_model=StoryRead)
def get_story(story_id: int, db: DbSession, user: CurrentUser):
    return svc.to_read(svc.get_story(db, user, story_id))


@router.put("/{story_id}", response_model=StoryRead)
def update_story(story_id: int, payload: StoryUpdate, db: DbSession, user: CurrentUser):
    story = svc.get_story(db, user, story_id)
    story.title, story.body, story.clusters = payload.title, payload.body, payload.clusters
    db.commit()
    db.refresh(story)
    return svc.to_read(story)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(story_id: int, db: DbSession, user: CurrentUser):
    db.delete(svc.get_story(db, user, story_id))
    db.commit()


@router.get("/{story_id}/matches", response_model=StoryMatches)
def story_matches(story_id: int, db: DbSession, user: CurrentUser):
    """Part 2 cue cards this story can answer, and how many the learner has practised."""
    return svc.matches_for_story(db, user, svc.get_story(db, user, story_id))


@router.post("/{story_id}/adapt", response_model=StoryAdaptation)
def adapt_story(story_id: int, payload: AdaptRequest, db: DbSession, llm: LLM, user: CurrentUser):
    story = svc.get_story(db, user, story_id)
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return svc.adapt(db, llm, user, story, question)
