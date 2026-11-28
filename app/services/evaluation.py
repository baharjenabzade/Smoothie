import logging

from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import LLMClient
from app.ai.schemas import EvaluationResult
from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.core.scoring import count_words, overall_band
from app.models import Answer, Evaluation, GrammarIssue, PracticeSession, Question, User
from app.rag.retrieval import reference_samples_for
from app.schemas.practice import AnswerCreate
from app.services.calibration import calibrate, strict_round
from app.services.grounding import ground_result
from app.services.vocabulary import upsert_vocabulary

logger = logging.getLogger(__name__)

MIN_WORDS = 3


def _resolve_question(
    db: Session, session: PracticeSession, payload: AnswerCreate
) -> tuple[Question | None, str]:
    if payload.question_id is None:
        return None, (payload.question_text or "").strip()

    question = db.get(Question, payload.question_id)
    if question is None:
        raise NotFoundError("Question not found")
    if question.part != session.part:
        raise AppError(
            f"This question belongs to Part {question.part}, but the session is Part {session.part}.",
            422,
        )
    text = question.text
    if question.cue_points:
        text += "\nYou should say: " + "; ".join(question.cue_points)
    return question, text


def evaluate_and_store(
    db: Session, llm: LLMClient, user: User, session: PracticeSession, payload: AnswerCreate
) -> Answer:
    """Evaluate a learner's answer with the LLM and save the answer, scores, grammar issues and
    vocabulary. Nothing is saved if the model call fails."""
    question, question_text = _resolve_question(db, session, payload)

    answer_text = payload.answer_text
    words = count_words(answer_text)
    if words < MIN_WORDS:
        raise AppError(f"The answer is too short to evaluate (minimum {MIN_WORDS} words).", 422)

    system, prompt = prompts.evaluation_prompt(
        part=session.part,
        question=question_text,
        answer=answer_text,
        word_count=words,
        target_band=user.target_band,
        references=reference_samples_for(part=session.part, question=question_text, answer=answer_text),
    )

    # Release the DB connection back to the pool while the (slow) model is working.
    db.commit()
    result = ground_result(
        llm.generate(system=system, user=prompt, schema=EvaluationResult), answer_text
    )

    strict = get_settings().scoring_strictness == "strict"
    cal = calibrate(result, part=session.part, word_count=words, strict=strict)
    fluency, lexical, grammar = cal.fluency, cal.lexical, cal.grammar
    average = (fluency + lexical + grammar) / 3
    band = strict_round(average) if strict else overall_band(fluency, lexical, grammar)
    result = result.model_copy(
        update={
            "fluency_coherence": result.fluency_coherence.model_copy(update={"score": fluency}),
            "lexical_resource": result.lexical_resource.model_copy(update={"score": lexical}),
            "grammatical_range_accuracy": result.grammatical_range_accuracy.model_copy(update={"score": grammar}),
        }
    )
    topic = session.topic or (question.topic if question else None)

    evaluation = Evaluation(
        user_id=user.id,
        fluency_score=fluency,
        lexical_score=lexical,
        grammar_score=grammar,
        overall_band=band,
        feedback={**result.model_dump(mode="json"), "calibration_notes": cal.notes},
        model_name=llm.model_name,
    )
    evaluation.grammar_issues = [
        GrammarIssue(
            user_id=user.id,
            category=issue.category,
            original=issue.original.strip(),
            corrected=issue.corrected.strip(),
            explanation=issue.explanation.strip(),
        )
        for issue in result.grammar_issues
    ]

    answer = Answer(
        session_id=session.id,
        user_id=user.id,
        question_id=question.id if question else None,
        question_text=question_text,
        answer_text=answer_text,
        word_count=words,
    )
    answer.evaluation = evaluation
    db.add(answer)
    db.flush()  # assigns evaluation.id for the vocabulary rows

    upsert_vocabulary(
        db,
        user_id=user.id,
        items=[(v, "answer") for v in result.useful_vocabulary]
        + [(v, "suggestion") for v in result.suggested_vocabulary],
        topic=topic,
        evaluation_id=evaluation.id,
    )
    db.commit()
    logger.info("Evaluated answer %s for user %s: band %.1f", answer.id, user.id, band)
    return answer
