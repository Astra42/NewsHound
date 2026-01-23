"""Конфигурация приложения."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    mistral_api_key: str = Field(default="", alias="MISTRAL_API_KEY")
    telegram_api_id: str = Field(default="", alias="APP_ID_TG")
    telegram_api_hash: str = Field(default="", alias="API_HASH_TG")
    telegram_phone: str = Field(default="", alias="TELEGRAM_PHONE")
    telegram_code: str = Field(default="", alias="TELEGRAM_CODE")

    llm_model: str = Field(default="mistral-small-latest", alias="LLM_MODEL")
    embedding_model: str = Field(default="ai-forever/FRIDA", alias="EMBEDDING_MODEL")
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")

    database_url: str = Field(
        default="postgresql://newshound:newshound_secret@postgres:5432/newshound",
        alias="DATABASE_URL",
    )
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="newshound", alias="POSTGRES_USER")
    postgres_password: str = Field(
        default="newshound_secret", alias="POSTGRES_PASSWORD"
    )
    postgres_db: str = Field(default="newshound", alias="POSTGRES_DB")

    qdrant_host: str = Field(default="qdrant", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection: str = Field(default="news", alias="QDRANT_COLLECTION")

    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    retrieval_k: int = Field(default=5, alias="RETRIEVAL_K")

    default_channels: List[str] = Field(
        default=[
            "@tass_agency",
            "@rian_ru",
            "@kommersant",
            "@gazeta_ru",
            "@meduzalive",
            "@rbc_news",
        ]
    )
    telegram_message_limit: int = Field(default=100, alias="TELEGRAM_MESSAGE_LIMIT")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_debug: bool = Field(default=False, alias="API_DEBUG")

    llm_timeout: float = Field(default=60.0, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
