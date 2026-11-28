from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.schemas import EvaluationResult

DISCLAIMER = (
    "Provisional band estimate from the transcript only. Pronunciation is not assessed and the "
    "scores are indicative, not an official IELTS result."
)


class SessionCreate(BaseModel):
    part: Literal[1, 2, 3]
    topic: str | None = Field(default=None, max_length=100)


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part: int
    topic: str | None
    created_at: datetime
    answer_count: int
    average_band: float | None


class AnswerCreate(BaseModel):
    question_id: int | None = None
    question_text: str | None = Field(default=None, max_length=1000)
    answer_text: str = Field(max_length=6000)

    @field_validator("answer_text")
    @classmethod
    def _strip_answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("answer_text must not be empty")
        return value

    @model_validator(mode="after")
    def _need_a_question(self) -> "AnswerCreate":
        if self.question_id is None and not (self.question_text and self.question_text.strip()):
            raise ValueError("Provide either question_id or question_text")
        return self


class StoredFeedback(EvaluationResult):
    """The model's feedback plus notes on any score limits our own checks applied."""

    calibration_notes: list[str] = Field(default_factory=list)


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fluency_score: float
    lexical_score: float
    grammar_score: float
    overall_band: float
    feedback: StoredFeedback
    model_name: str
    created_at: datetime
    disclaimer: str = DISCLAIMER


class AnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    question_id: int | None
    question_text: str
    answer_text: str
    word_count: int
    created_at: datetime
    evaluation: EvaluationRead | None


class SessionDetail(SessionRead):
    answers: list[AnswerRead]


class SampleAnswerRequest(BaseModel):
    part: Literal[1, 2, 3]
    question_text: str = Field(min_length=3, max_length=1000)
    target_band: float = Field(default=7.0, ge=4.0, le=9.0)


class FollowUpRequest(BaseModel):
    question_text: str = Field(min_length=3, max_length=1000)
    answer_text: str = Field(min_length=3, max_length=6000)
