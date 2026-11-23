from datetime import datetime

from pydantic import BaseModel

from app.schemas.practice import SessionRead


class GrammarExample(BaseModel):
    original: str
    corrected: str


class GrammarCategoryStat(BaseModel):
    category: str
    count: int
    examples: list[GrammarExample]


class CriterionAverages(BaseModel):
    fluency_coherence: float | None
    lexical_resource: float | None
    grammatical_range_accuracy: float | None


class WeaknessReport(BaseModel):
    evaluations_analyzed: int
    criterion_averages: CriterionAverages
    weakest_criterion: str | None
    top_grammar_categories: list[GrammarCategoryStat]


class TrendPoint(BaseModel):
    evaluation_id: int
    created_at: datetime
    part: int
    overall_band: float


class DashboardRead(BaseModel):
    total_sessions: int
    total_answers: int
    average_band: float | None
    best_band: float | None
    latest_band: float | None
    criterion_averages: CriterionAverages
    weakest_criterion: str | None
    top_grammar_categories: list[GrammarCategoryStat]
    vocabulary_count: int
    trend: list[TrendPoint]
    recent_sessions: list[SessionRead]
