"""Load the starter question bank. Safe to run repeatedly: existing questions are skipped.

    python -m app.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Question
from app.seed_data import iter_seed_questions


def seed_questions(db: Session) -> int:
    existing = {(part, text) for part, text in db.execute(select(Question.part, Question.text))}
    added = 0
    for item in iter_seed_questions():
        if (item["part"], item["text"]) in existing:
            continue
        db.add(
            Question(
                part=item["part"],
                topic=item["topic"],
                text=item["text"],
                cue_points=item["cue_points"],
                is_ai_generated=False,
            )
        )
        added += 1
    db.commit()
    return added


def main() -> None:
    with SessionLocal() as db:
        added = seed_questions(db)
    print(f"Seeded {added} new question(s).")


if __name__ == "__main__":
    main()
