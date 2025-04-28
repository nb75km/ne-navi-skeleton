from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    database_url: PostgresDsn = Field(..., env="DATABASE_URL")

    # Redis (for Celery broker/backend)
    celery_broker_url: str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    celery_backend_url: str = Field("redis://redis:6379/1", env="CELERY_BACKEND_URL")

    # OpenAI / Dify tokens
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    dify_api_key: str | None = Field(default=None, env="DIFY_API_KEY")

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:  # pragma: no cover
    return Settings()
