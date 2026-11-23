from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part: int
    topic: str
    text: str
    cue_points: list[str] | None
    is_ai_generated: bool


class QuestionGenerateRequest(BaseModel):
    part: Literal[1, 2, 3]
    topic: str = Field(min_length=1, max_length=100)
    count: int = Field(default=5, ge=1, le=10)


class TopicSummary(BaseModel):
    topic: str
    parts: list[int]
    question_count: int
