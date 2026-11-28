from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRET = "dev-only-change-me-please-use-a-long-random-string"


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smoothies"
    environment: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+psycopg://ielts:ielts@localhost:5432/ielts"
    db_pool_size: int = 5

    # Auth
    secret_key: str = _PLACEHOLDER_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # CORS (JSON list in the environment)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Which AI backend does the evaluating: a local Ollama model or the Google Gemini API.
    llm_provider: Literal["ollama", "gemini"] = "ollama"

    # Gemini (used when llm_provider=gemini). Get a key at https://aistudio.google.com/apikey
    gemini_api_key: str = ""
    # Model names change over time. `python -m app.gemini_models` lists the ones your key can use.
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: float = 120.0
    gemini_max_retries: int = 1
    gemini_rate_limit_retries: int = 4

    # Scoring: "strict" applies length/error-density caps and rounds the overall band down.
    scoring_strictness: Literal["strict", "standard"] = "strict"

    # RAG: graded reference answers (JSON files) shown to the model to calibrate its scoring.
    rag_enabled: bool = True
    rag_samples_dir: str = "knowledge/samples"
    rag_top_k: int = 3

    # Ollama (used when llm_provider=ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_timeout_seconds: float = 180.0
    ollama_temperature: float = 0.3
    ollama_num_ctx: int = 8192
    ollama_think: bool = False
    ollama_max_retries: int = 1

    @model_validator(mode="after")
    def _reject_weak_secret_in_production(self) -> "Settings":
        weak = (
            self.secret_key == _PLACEHOLDER_SECRET
            or self.secret_key.startswith("change-me")
            or len(self.secret_key) < 32
        )
        if self.environment == "production" and weak:
            raise ValueError(
                "SECRET_KEY must be a random string of at least 32 characters in production "
                "(generate one with: openssl rand -hex 32)"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
