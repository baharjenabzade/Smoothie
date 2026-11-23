from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class VocabularyItem(Base):
    """A word, collocation, idiom, phrasal verb or expression in a learner's notebook."""

    __tablename__ = "vocabulary_items"
    __table_args__ = (
        UniqueConstraint("user_id", "term_key", name="uq_vocabulary_items_user_id_term_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    evaluation_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluations.id", ondelete="SET NULL")
    )
    term: Mapped[str] = mapped_column(String(200))
    term_key: Mapped[str] = mapped_column(String(200))  # lower-cased, whitespace-normalised
    item_type: Mapped[str] = mapped_column(String(30))
    definition: Mapped[str] = mapped_column(Text)
    example: Mapped[str | None] = mapped_column(Text)
    topic: Mapped[str | None] = mapped_column(String(100), index=True)
    # answer = used by the learner, suggestion = recommended upgrade, topic = topic word list
    source: Mapped[str] = mapped_column(String(20), default="answer", server_default="answer")
    times_seen: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
