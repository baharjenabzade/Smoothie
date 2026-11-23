from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import LLMClient
from app.ai.schemas import Recommendations, TopicVocabulary, VocabularyEntry
from app.core.errors import ConflictError
from app.models import User
from app.services.progress import compute_weaknesses
from app.services.vocabulary import upsert_vocabulary


def topic_vocabulary(
    db: Session,
    llm: LLMClient,
    user: User,
    *,
    topic: str,
    count: int,
    target_band: float,
    save: bool,
) -> tuple[list[VocabularyEntry], int]:
    system, prompt = prompts.topic_vocabulary_prompt(topic=topic, count=count, target_band=target_band)
    db.commit()  # free the connection while the model works
    result = llm.generate(system=system, user=prompt, schema=TopicVocabulary)
    items = result.items[:count]

    saved = 0
    if save:
        rows = upsert_vocabulary(
            db,
            user_id=user.id,
            items=[(item, "topic") for item in items],
            topic=topic.strip(),
            evaluation_id=None,
        )
        db.commit()
        saved = len(rows)
    return items, saved


def build_recommendations(db: Session, llm: LLMClient, user: User) -> Recommendations:
    report = compute_weaknesses(db, user.id)
    if report.evaluations_analyzed == 0:
        raise ConflictError(
            "Complete at least one evaluated answer first, so recommendations can be based on your results."
        )
    system, prompt = prompts.recommendations_prompt(
        report_json=report.model_dump_json(indent=2), target_band=user.target_band
    )
    db.commit()  # free the connection while the model works
    return llm.generate(system=system, user=prompt, schema=Recommendations)
