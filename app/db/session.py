from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def _make_engine(url: str, pool_size: int) -> Engine:
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///") or ":memory:" in url:
            kwargs["poolclass"] = StaticPool  # one shared in-memory database
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True, pool_size=pool_size, max_overflow=pool_size)


_settings = get_settings()
engine = _make_engine(_settings.database_url, _settings.db_pool_size)

# expire_on_commit=False keeps objects readable after commit. The evaluation service commits
# before slow LLM calls so the DB connection goes back to the pool while the model is thinking.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
