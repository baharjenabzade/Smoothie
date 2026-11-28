import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import LLMClient
from app.ai.schemas import StoryAdaptation
from app.clusters import clusters_for_topic
from app.core.errors import NotFoundError
from app.core.scoring import count_words
from app.models import Answer, Question, Story, User
from app.schemas.question import QuestionRead
from app.schemas.story import StoryMatch, StoryMatches, StoryRead, StorySuggestion

MAX_STORIES_PER_USER = 50
MAX_MATCHES = 12

_TOKEN = re.compile(r"[a-z]{4,}")
_STOP = frozenset(["that", "this", "with", "from", "have", "they", "their", "there", "what", "when", "which", "about", "would", "could", "were", "been", "your", "you", "and", "the", "for", "but", "not", "are", "was"])


def _words(text: str) -> set[str]:
    return {w for w in _TOKEN.findall(text.lower()) if w not in _STOP}


def to_read(story: Story) -> StoryRead:
    data = StoryRead.model_validate(story)
    data.word_count = count_words(story.body)
    return data


def get_story(db: Session, user: User, story_id: int) -> Story:
    story = db.get(Story, story_id)
    if story is None or story.user_id != user.id:
        raise NotFoundError("Story not found")
    return story


def score_pair(story: Story, question: Question) -> tuple[float, list[str]]:
    """Cluster overlap counts most; shared content words add a little. Transparent, no AI call."""
    shared = [c for c in clusters_for_topic(question.topic) if c in (story.clusters or [])]
    cue_text = f"{question.text} {question.topic} {' '.join(question.cue_points or [])}"
    overlap = len(_words(f"{story.title} {story.body}") & _words(cue_text))
    return 3.0 * len(shared) + min(3.0, 0.5 * overlap), shared


def _practised_ids(db: Session, user: User) -> set[int]:
    rows = db.scalars(select(Answer.question_id).where(Answer.user_id == user.id, Answer.question_id.is_not(None)))
    return set(rows)


def matches_for_story(db: Session, user: User, story: Story) -> StoryMatches:
    practised = _practised_ids(db, user)
    scored: list[StoryMatch] = []
    for q in db.scalars(select(Question).where(Question.part == 2)):
        score, shared = score_pair(story, q)
        if shared or score >= 1.5:
            scored.append(StoryMatch(question=QuestionRead.model_validate(q), score=round(score, 1), shared_clusters=shared, practised=q.id in practised))
    scored.sort(key=lambda m: (-m.score, m.question.id))
    top = scored[:MAX_MATCHES]
    return StoryMatches(story_id=story.id, matches=top, practised_count=sum(m.practised for m in scored))


def suggest_for_question(db: Session, user: User, question: Question) -> list[StorySuggestion]:
    out: list[StorySuggestion] = []
    for story in db.scalars(select(Story).where(Story.user_id == user.id)):
        score, shared = score_pair(story, question)
        if shared or score >= 1.5:
            out.append(StorySuggestion(story_id=story.id, title=story.title, score=round(score, 1), shared_clusters=shared))
    return sorted(out, key=lambda s: -s.score)[:5]


def adapt(db: Session, llm: LLMClient, user: User, story: Story, question: Question) -> StoryAdaptation:
    system, prompt = prompts.story_adaptation_prompt(
        story_title=story.title, story_body=story.body, question=question.text,
        cue_points=question.cue_points, target_band=user.target_band,
    )
    db.commit()  # free the connection while the model works
    return llm.generate(system=system, user=prompt, schema=StoryAdaptation)
