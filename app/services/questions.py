from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import LLMClient
from app.ai.schemas import GeneratedQuestions
from app.core.errors import AppError
from app.models import Question, User
from app.schemas.question import TopicSummary


def generate_questions(
    db: Session, llm: LLMClient, user: User, *, part: int, topic: str, count: int
) -> list[Question]:
    topic = topic.strip()
    system, prompt = prompts.question_generation_prompt(part=part, topic=topic, count=count)

    db.commit()  # free the connection while the model works
    result = llm.generate(system=system, user=prompt, schema=GeneratedQuestions)

    existing = {
        text.lower()
        for text in db.scalars(
            select(Question.text).where(Question.part == part, func.lower(Question.topic) == topic.lower())
        )
    }
    created: list[Question] = []
    for item in result.questions[:count]:
        text = item.text.strip()
        if not text or text.lower() in existing:
            continue
        existing.add(text.lower())
        cues = [c.strip() for c in item.cue_points if c.strip()] if part == 2 else []
        question = Question(
            part=part,
            topic=topic,
            text=text,
            cue_points=cues or None,
            is_ai_generated=True,
            created_by=user.id,
        )
        db.add(question)
        created.append(question)

    if not created:
        raise AppError("The model did not produce any new questions. Please try again.", 502)
    db.commit()
    return created


def topic_summaries(db: Session) -> list[TopicSummary]:
    rows = db.execute(
        select(Question.topic, Question.part, func.count(Question.id))
        .group_by(Question.topic, Question.part)
        .order_by(Question.topic, Question.part)
    ).all()
    topics: dict[str, TopicSummary] = {}
    for topic, part, count in rows:
        summary = topics.setdefault(topic, TopicSummary(topic=topic, parts=[], question_count=0))
        summary.parts.append(part)
        summary.question_count += count
    return list(topics.values())
