from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.ai.schemas import VocabularyEntry


class VocabularyItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term: str
    item_type: str
    definition: str
    example: str | None
    topic: str | None
    source: str
    times_seen: int
    created_at: datetime


class GrammarIssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_id: int
    category: str
    original: str
    corrected: str
    explanation: str
    created_at: datetime


class TopicVocabularyRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    count: int = Field(default=10, ge=3, le=20)
    target_band: float | None = Field(default=None, ge=4.0, le=9.0)
    save: bool = False


class TopicVocabularyResponse(BaseModel):
    topic: str
    items: list[VocabularyEntry]
    saved: int
