from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Question, User
from app.schemas.group import ImportResult
from app.services.similarity import Item, group_similar, label_for

MAX_TEXT = 600


def _clean(raw: Any, index: int) -> dict | None:
    if not isinstance(raw, dict):
        return None
    try:
        part = int(raw.get("part"))
    except (TypeError, ValueError):
        return None
    text = str(raw.get("text") or "").strip()
    if part not in (1, 2, 3) or not (5 <= len(text) <= MAX_TEXT):
        return None
    topic = str(raw.get("topic") or "").strip()[:100] or None
    cues = raw.get("cue_points") or []
    cues = [str(c).strip()[:200] for c in cues if str(c).strip()][:6] if isinstance(cues, list) else []
    return {"index": index, "part": part, "text": text, "topic": topic, "cue_points": cues if part == 2 and cues else None}


def import_questions(db: Session, user: User, items: list[Any], *, default_topic: str, auto_topic: bool) -> ImportResult:
    existing = {(part, text.lower()) for part, text in db.execute(select(Question.part, Question.text))}
    clean: list[dict] = []
    invalid = duplicates = 0
    for i, raw in enumerate(items):
        row = _clean(raw, i)
        if row is None:
            invalid += 1
            continue
        key = (row["part"], row["text"].lower())
        if key in existing:
            duplicates += 1
            continue
        existing.add(key)
        clean.append(row)

    if auto_topic:
        for part in (1, 2, 3):
            untopiced = [r for r in clean if r["part"] == part and not r["topic"]]
            for group in group_similar([Item.of(r["index"], r["text"]) for r in untopiced]):
                if len(group) < 2:
                    continue
                label = label_for([g.text for g in group])[:100]
                members = {g.key for g in group}
                for r in untopiced:
                    if r["index"] in members:
                        r["topic"] = label

    topics: dict[str, int] = {}
    for row in clean:
        topic = row["topic"] or default_topic.strip()[:100] or "Imported"
        topics[topic] = topics.get(topic, 0) + 1
        db.add(Question(part=row["part"], topic=topic, text=row["text"], cue_points=row["cue_points"], is_ai_generated=False, created_by=user.id))
    db.commit()
    return ImportResult(created=len(clean), skipped_duplicates=duplicates, skipped_invalid=invalid, topics=topics)
