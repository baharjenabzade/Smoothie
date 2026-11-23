from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models import Answer, PracticeSession, User

_WITH_ANSWERS = selectinload(PracticeSession.answers).selectinload(Answer.evaluation)


def create_session(db: Session, user: User, *, part: int, topic: str | None) -> PracticeSession:
    session = PracticeSession(user_id=user.id, part=part, topic=topic.strip() if topic else None)
    db.add(session)
    db.commit()
    return session


def get_owned_session(db: Session, session_id: int, user: User) -> PracticeSession:
    session = db.scalar(
        select(PracticeSession)
        .where(PracticeSession.id == session_id, PracticeSession.user_id == user.id)
        .options(_WITH_ANSWERS)
    )
    if session is None:
        raise NotFoundError("Practice session not found")
    return session


def list_sessions(
    db: Session, user: User, *, limit: int, offset: int, part: int | None = None
) -> list[PracticeSession]:
    stmt = select(PracticeSession).where(PracticeSession.user_id == user.id)
    if part is not None:
        stmt = stmt.where(PracticeSession.part == part)
    stmt = stmt.order_by(PracticeSession.id.desc()).limit(limit).offset(offset).options(_WITH_ANSWERS)
    return list(db.scalars(stmt))


def delete_session(db: Session, session_id: int, user: User) -> None:
    session = get_owned_session(db, session_id, user)
    db.delete(session)
    db.commit()
