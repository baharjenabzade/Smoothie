import os

# Must be set before the app is imported: never let tests touch a real database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-for-the-test-suite-only-0123456789"
os.environ["ENVIRONMENT"] = "test"
# API-flow tests assert the model's raw scores; strict calibration is unit-tested separately.
os.environ["SCORING_STRICTNESS"] = "standard"

import pytest

# NOTE: heavy imports (fastapi, sqlalchemy, app.*) happen inside fixtures so the pure unit tests
# (scoring, schemas, parsing, grounding, seed data) run even without the web stack installed.


@pytest.fixture()
def engine():
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    import app.models  # noqa: F401
    from app.db.base import Base

    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def fake_llm():
    from tests.fakes import FakeLLM

    return FakeLLM()


@pytest.fixture()
def client(session_factory, fake_llm):
    from fastapi.testclient import TestClient

    from app.api.deps import get_llm
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm] = lambda: fake_llm
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(session_factory):
    from app.seed import seed_questions

    with session_factory() as db:
        return seed_questions(db)
