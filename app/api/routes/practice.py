from typing import Annotated

from fastapi import APIRouter, Query, status

from app.ai import prompts
from app.ai.schemas import FollowUpResult, SampleAnswerResult
from app.api.deps import LLM, CurrentUser, DbSession
from app.schemas.practice import (
    AnswerCreate,
    AnswerRead,
    FollowUpRequest,
    SampleAnswerRequest,
    SessionCreate,
    SessionDetail,
    SessionRead,
)
from app.services import practice as practice_service
from app.services.evaluation import evaluate_and_store

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: DbSession, user: CurrentUser):
    session = practice_service.create_session(db, user, part=payload.part, topic=payload.topic)
    return SessionRead.model_validate(session)


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(
    db: DbSession,
    user: CurrentUser,
    part: Annotated[int | None, Query(ge=1, le=3)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    sessions = practice_service.list_sessions(db, user, limit=limit, offset=offset, part=part)
    return [SessionRead.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: DbSession, user: CurrentUser):
    return SessionDetail.model_validate(practice_service.get_owned_session(db, session_id, user))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: DbSession, user: CurrentUser) -> None:
    practice_service.delete_session(db, session_id, user)


@router.post(
    "/sessions/{session_id}/answers",
    response_model=AnswerRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_answer(
    session_id: int, payload: AnswerCreate, db: DbSession, llm: LLM, user: CurrentUser
):
    """Submit the transcript of a spoken answer. It is evaluated by the AI and saved."""
    session = practice_service.get_owned_session(db, session_id, user)
    answer = evaluate_and_store(db, llm, user, session, payload)
    return AnswerRead.model_validate(answer)


@router.post("/sample-answer", response_model=SampleAnswerResult)
def sample_answer(payload: SampleAnswerRequest, db: DbSession, llm: LLM, user: CurrentUser):
    """Generate a model answer calibrated to a target band score."""
    system, prompt = prompts.sample_answer_prompt(
        part=payload.part, question=payload.question_text, target_band=payload.target_band
    )
    db.commit()  # free the DB connection while the model works
    return llm.generate(system=system, user=prompt, schema=SampleAnswerResult)


@router.post("/follow-up", response_model=FollowUpResult)
def follow_up(payload: FollowUpRequest, db: DbSession, llm: LLM, user: CurrentUser):
    """Examiner-style follow-up questions to extend an answer."""
    system, prompt = prompts.follow_up_prompt(
        question=payload.question_text, answer=payload.answer_text
    )
    db.commit()  # free the DB connection while the model works
    return llm.generate(system=system, user=prompt, schema=FollowUpResult)
