from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Answer, Evaluation, GrammarIssue, PracticeSession, VocabularyItem
from app.schemas.practice import SessionRead
from app.schemas.progress import (
    CriterionAverages,
    DashboardRead,
    GrammarCategoryStat,
    GrammarExample,
    TrendPoint,
    WeaknessReport,
)


def _round(value: float | None) -> float | None:
    return round(float(value), 2) if value is not None else None


def compute_weaknesses(db: Session, user_id: int, *, top_n: int = 5) -> WeaknessReport:
    """Recurring weaknesses: weakest scoring criterion and the most frequent grammar categories."""
    count, fluency, lexical, grammar = db.execute(
        select(
            func.count(Evaluation.id),
            func.avg(Evaluation.fluency_score),
            func.avg(Evaluation.lexical_score),
            func.avg(Evaluation.grammar_score),
        ).where(Evaluation.user_id == user_id)
    ).one()

    averages = CriterionAverages(
        fluency_coherence=_round(fluency),
        lexical_resource=_round(lexical),
        grammatical_range_accuracy=_round(grammar),
    )
    scored = {k: v for k, v in averages.model_dump().items() if v is not None}
    weakest = min(scored, key=scored.get) if scored else None

    occurrences = func.count(GrammarIssue.id)
    category_rows = db.execute(
        select(GrammarIssue.category, occurrences.label("n"))
        .where(GrammarIssue.user_id == user_id, GrammarIssue.category != "other")
        .group_by(GrammarIssue.category)
        .order_by(occurrences.desc(), GrammarIssue.category)
        .limit(top_n)
    ).all()

    categories: list[GrammarCategoryStat] = []
    for category, n in category_rows:
        examples = db.scalars(
            select(GrammarIssue)
            .where(GrammarIssue.user_id == user_id, GrammarIssue.category == category)
            .order_by(GrammarIssue.id.desc())
            .limit(2)
        ).all()
        categories.append(
            GrammarCategoryStat(
                category=category,
                count=n,
                examples=[GrammarExample(original=e.original, corrected=e.corrected) for e in examples],
            )
        )

    return WeaknessReport(
        evaluations_analyzed=count or 0,
        criterion_averages=averages,
        weakest_criterion=weakest,
        top_grammar_categories=categories,
    )


def build_dashboard(db: Session, user_id: int, *, trend_points: int = 20) -> DashboardRead:
    total_sessions = db.scalar(
        select(func.count(PracticeSession.id)).where(PracticeSession.user_id == user_id)
    ) or 0
    total_answers = db.scalar(select(func.count(Answer.id)).where(Answer.user_id == user_id)) or 0
    vocabulary_count = db.scalar(
        select(func.count(VocabularyItem.id)).where(VocabularyItem.user_id == user_id)
    ) or 0

    average_band, best_band = db.execute(
        select(func.avg(Evaluation.overall_band), func.max(Evaluation.overall_band)).where(
            Evaluation.user_id == user_id
        )
    ).one()
    latest_band = db.scalar(
        select(Evaluation.overall_band)
        .where(Evaluation.user_id == user_id)
        .order_by(Evaluation.id.desc())
        .limit(1)
    )

    trend_rows = db.execute(
        select(Evaluation.id, Evaluation.created_at, Evaluation.overall_band, PracticeSession.part)
        .join(Answer, Answer.id == Evaluation.answer_id)
        .join(PracticeSession, PracticeSession.id == Answer.session_id)
        .where(Evaluation.user_id == user_id)
        .order_by(Evaluation.id.desc())
        .limit(trend_points)
    ).all()
    trend = [
        TrendPoint(evaluation_id=i, created_at=created, overall_band=band, part=part)
        for i, created, band, part in reversed(trend_rows)  # oldest first, ready to plot
    ]

    recent_sessions = db.scalars(
        select(PracticeSession)
        .where(PracticeSession.user_id == user_id)
        .order_by(PracticeSession.id.desc())
        .limit(5)
        .options(selectinload(PracticeSession.answers).selectinload(Answer.evaluation))
    ).all()

    weaknesses = compute_weaknesses(db, user_id)
    return DashboardRead(
        total_sessions=total_sessions,
        total_answers=total_answers,
        average_band=_round(average_band),
        best_band=best_band,
        latest_band=latest_band,
        criterion_averages=weaknesses.criterion_averages,
        weakest_criterion=weaknesses.weakest_criterion,
        top_grammar_categories=weaknesses.top_grammar_categories,
        vocabulary_count=vocabulary_count,
        trend=trend,
        recent_sessions=[SessionRead.model_validate(s) for s in recent_sessions],
    )
