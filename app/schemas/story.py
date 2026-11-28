from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.clusters import CLUSTER_SLUGS
from app.core.scoring import count_words
from app.schemas.question import QuestionRead


def _clean_clusters(values: list[str]) -> list[str]:
    cleaned = list(dict.fromkeys(v.strip().lower() for v in values))
    unknown = [v for v in cleaned if v not in CLUSTER_SLUGS]
    if unknown:
        raise ValueError(f"unknown cluster(s): {', '.join(unknown)}")
    if len(cleaned) > 5:
        raise ValueError("choose at most 5 clusters")
    return cleaned


class StoryBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=1, max_length=6000)
    clusters: list[str] = Field(default_factory=list)

    @field_validator("title", "body")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("body")
    @classmethod
    def _min_words(cls, v: str) -> str:
        if count_words(v) < 15:
            raise ValueError("write at least 15 words so the story can be matched to cue cards")
        return v

    @field_validator("clusters")
    @classmethod
    def _clusters(cls, v: list[str]) -> list[str]:
        return _clean_clusters(v)


class StoryCreate(StoryBase):
    pass


class StoryUpdate(StoryBase):
    pass


class StoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    clusters: list[str]
    created_at: datetime
    updated_at: datetime
    word_count: int = 0


class StoryMatch(BaseModel):
    question: QuestionRead
    score: float
    shared_clusters: list[str]
    practised: bool


class StoryMatches(BaseModel):
    story_id: int
    matches: list[StoryMatch]
    practised_count: int


class StorySuggestion(BaseModel):
    story_id: int
    title: str
    score: float
    shared_clusters: list[str]


class AdaptRequest(BaseModel):
    question_id: int
