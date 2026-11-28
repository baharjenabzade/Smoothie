from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.db.types import JSONType


class Question(Base):
    """A speaking question. Part 2 questions are cue cards: `text` plus `cue_points`."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    part: Mapped[int] = mapped_column(SmallInteger, index=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    text: Mapped[str] = mapped_column(Text)
    cue_points: Mapped[list[str] | None] = mapped_column(JSONType)
    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
