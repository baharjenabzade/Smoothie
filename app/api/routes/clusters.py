from collections import Counter

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.clusters import CLUSTERS, clusters_for_topic
from app.models import Question

router = APIRouter(prefix="/clusters", tags=["clusters"])


class TopicInCluster(BaseModel):
    topic: str
    counts: dict[int, int]  # part -> number of questions
    also_in: list[str]  # other cluster slugs this topic belongs to


class ClusterRead(BaseModel):
    slug: str
    name: str
    blurb: str
    topics: list[TopicInCluster]
    question_count: int


@router.get("", response_model=list[ClusterRead])
def list_clusters(db: DbSession, user: CurrentUser):
    """All topic clusters with the number of questions per part for each topic."""
    counts: dict[str, Counter] = {}
    for topic, part in db.execute(select(Question.topic, Question.part)):
        counts.setdefault(topic.lower(), Counter())[part] += 1
    out = []
    for c in CLUSTERS:
        topics = [
            TopicInCluster(
                topic=t,
                counts={p: counts.get(t.lower(), Counter()).get(p, 0) for p in (1, 2, 3)},
                also_in=[s for s in clusters_for_topic(t) if s != c.slug],
            )
            for t in c.topics
        ]
        out.append(ClusterRead(slug=c.slug, name=c.name, blurb=c.blurb, topics=topics, question_count=sum(sum(t.counts.values()) for t in topics)))
    return out
