from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.question import QuestionRead


class GroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    topics: list[str] = Field(default_factory=list, max_length=40)
    question_ids: list[int] = Field(default_factory=list, max_length=300)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("topics")
    @classmethod
    def _topics(cls, v: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(t.strip() for t in v if t and t.strip()))
        if any(len(t) > 100 for t in cleaned):
            raise ValueError("topic names are at most 100 characters")
        return cleaned

    @field_validator("question_ids")
    @classmethod
    def _ids(cls, v: list[int]) -> list[int]:
        return list(dict.fromkeys(i for i in v if i > 0))


class GroupCreate(GroupBase):
    pass


class GroupUpdate(GroupBase):
    pass


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    topics: list[str]
    question_ids: list[int]
    created_at: datetime
    question_count: int = 0


class GroupDetail(GroupRead):
    questions: list[QuestionRead] = []


class ImportRequest(BaseModel):
    items: list[dict] = Field(max_length=1000)
    default_topic: str = Field(default="Imported", min_length=1, max_length=100)
    auto_topic: bool = False


class ImportResult(BaseModel):
    created: int
    skipped_duplicates: int
    skipped_invalid: int
    topics: dict[str, int]


class QuestionGroupRead(BaseModel):
    label: str
    size: int
    topics: list[str]
    questions: list[QuestionRead]


class SimilarQuestion(BaseModel):
    question: QuestionRead
    score: float
