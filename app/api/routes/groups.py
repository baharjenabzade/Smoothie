from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppError, NotFoundError
from app.models import Question, TopicGroup
from app.schemas.group import GroupCreate, GroupDetail, GroupRead, GroupUpdate
from app.schemas.question import QuestionRead

router = APIRouter(prefix="/groups", tags=["groups"])
MAX_GROUPS = 40


def _questions(db, group: TopicGroup, part: int | None = None, limit: int = 300) -> list[Question]:
    conditions = []
    if group.topics:
        conditions.append(func.lower(Question.topic).in_([t.lower() for t in group.topics]))
    if group.question_ids:
        conditions.append(Question.id.in_(group.question_ids))
    if not conditions:
        return []
    stmt = select(Question).where(or_(*conditions))
    if part:
        stmt = stmt.where(Question.part == part)
    return list(db.scalars(stmt.order_by(Question.part, Question.id).limit(limit)))


def _read(db, group: TopicGroup) -> GroupRead:
    data = GroupRead.model_validate(group)
    data.question_count = len(_questions(db, group))
    return data


def _own(db, user, group_id: int) -> TopicGroup:
    group = db.get(TopicGroup, group_id)
    if group is None or group.user_id != user.id:
        raise NotFoundError("Group not found")
    return group


@router.get("", response_model=list[GroupRead])
def list_groups(db: DbSession, user: CurrentUser):
    rows = db.scalars(select(TopicGroup).where(TopicGroup.user_id == user.id).order_by(TopicGroup.name))
    return [_read(db, g) for g in rows]


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, db: DbSession, user: CurrentUser):
    count = db.scalar(select(func.count()).select_from(TopicGroup).where(TopicGroup.user_id == user.id)) or 0
    if count >= MAX_GROUPS:
        raise AppError(f"You can keep up to {MAX_GROUPS} groups. Delete one to add another.", 422)
    group = TopicGroup(user_id=user.id, name=payload.name, topics=payload.topics, question_ids=payload.question_ids)
    db.add(group)
    db.commit()
    db.refresh(group)
    return _read(db, group)


@router.get("/{group_id}", response_model=GroupDetail)
def get_group(group_id: int, db: DbSession, user: CurrentUser, part: Annotated[int | None, Query(ge=1, le=3)] = None):
    group = _own(db, user, group_id)
    detail = GroupDetail.model_validate(group)
    questions = _questions(db, group, part)
    detail.question_count = len(_questions(db, group))
    detail.questions = [QuestionRead.model_validate(q) for q in questions]
    return detail


@router.put("/{group_id}", response_model=GroupRead)
def update_group(group_id: int, payload: GroupUpdate, db: DbSession, user: CurrentUser):
    group = _own(db, user, group_id)
    group.name, group.topics, group.question_ids = payload.name, payload.topics, payload.question_ids
    db.commit()
    db.refresh(group)
    return _read(db, group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, db: DbSession, user: CurrentUser):
    db.delete(_own(db, user, group_id))
    db.commit()
