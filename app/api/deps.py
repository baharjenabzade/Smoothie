from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.ai.client import LLMClient, OllamaClient
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_prefix}/auth/login")


@lru_cache
def _ollama() -> OllamaClient:
    s = get_settings()
    return OllamaClient(
        base_url=s.ollama_base_url,
        model=s.ollama_model,
        timeout=s.ollama_timeout_seconds,
        temperature=s.ollama_temperature,
        num_ctx=s.ollama_num_ctx,
        think=s.ollama_think,
        max_retries=s.ollama_max_retries,
    )


def get_llm() -> LLMClient:
    return _ollama()


def close_llm() -> None:
    if _ollama.cache_info().currsize:
        _ollama().close()
        _ollama.cache_clear()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
LLM = Annotated[LLMClient, Depends(get_llm)]
