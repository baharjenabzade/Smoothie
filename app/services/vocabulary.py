from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.schemas import VocabularyEntry
from app.models import VocabularyItem


def term_key(term: str) -> str:
    return " ".join(term.lower().split())[:200]


def upsert_vocabulary(
    db: Session,
    *,
    user_id: int,
    items: list[tuple[VocabularyEntry, str]],
    topic: str | None,
    evaluation_id: int | None,
) -> list[VocabularyItem]:
    """Add vocabulary to a learner's notebook. Terms they already have are not duplicated;
    their ``times_seen`` counter goes up instead. Does not commit."""
    prepared: dict[str, tuple[VocabularyEntry, str]] = {}
    for entry, source in items:
        key = term_key(entry.term)
        if key and key not in prepared:
            prepared[key] = (entry, source)
    if not prepared:
        return []

    existing = {
        row.term_key: row
        for row in db.scalars(
            select(VocabularyItem).where(
                VocabularyItem.user_id == user_id,
                VocabularyItem.term_key.in_(list(prepared)),
            )
        )
    }

    result: list[VocabularyItem] = []
    for key, (entry, source) in prepared.items():
        row = existing.get(key)
        if row is not None:
            row.times_seen += 1
            if source == "answer":  # the learner actually used it
                row.source = "answer"
        else:
            row = VocabularyItem(
                user_id=user_id,
                evaluation_id=evaluation_id,
                term=entry.term.strip()[:200],
                term_key=key,
                item_type=entry.type,
                definition=entry.definition.strip(),
                example=entry.example.strip() or None,
                topic=topic[:100] if topic else None,
                source=source,
            )
            db.add(row)
        result.append(row)
    return result
