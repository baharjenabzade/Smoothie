from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.scoring import round_band
from app.db.base import Base, utcnow
from app.db.types import JSONType


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    part: Mapped[int] = mapped_column(SmallInteger)
    topic: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Answer.id"
    )

    @property
    def answer_count(self) -> int:
        return len(self.answers)

    @property
    def average_band(self) -> float | None:
        bands = [a.evaluation.overall_band for a in self.answers if a.evaluation is not None]
        return round_band(sum(bands) / len(bands)) if bands else None


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL")
    )
    question_text: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    session: Mapped[PracticeSession] = relationship(back_populates="answers")
    evaluation: Mapped[Optional["Evaluation"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan", uselist=False
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    fluency_score: Mapped[float] = mapped_column(Float)
    lexical_score: Mapped[float] = mapped_column(Float)
    grammar_score: Mapped[float] = mapped_column(Float)
    overall_band: Mapped[float] = mapped_column(Float)
    feedback: Mapped[dict] = mapped_column(JSONType)
    model_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    answer: Mapped[Answer] = relationship(back_populates="evaluation")
    grammar_issues: Mapped[list["GrammarIssue"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan", order_by="GrammarIssue.id"
    )


class GrammarIssue(Base):
    __tablename__ = "grammar_issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    original: Mapped[str] = mapped_column(Text)
    corrected: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    evaluation: Mapped[Evaluation] = relationship(back_populates="grammar_issues")
