"""
Схемы для API completion (RAG).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceSchema(BaseModel):
    """Схема источника ответа."""

    channel: str = Field(..., description="Название канала")
    date: Optional[datetime] = Field(default=None, description="Дата публикации")
    post_id: Optional[int] = Field(default=None, description="ID поста")
    url: Optional[str] = Field(default=None, description="Ссылка на пост")
    relevance_score: float = Field(default=0.0, description="Оценка релевантности")


class CompletionRequestSchema(BaseModel):
    """Схема запроса на генерацию ответа."""

    user_id: int = Field(..., description="ID пользователя Telegram")
    question: str = Field(
        ..., min_length=1, max_length=2000, description="Вопрос пользователя"
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Количество документов для контекста"
    )
    channels: Optional[List[str]] = Field(
        default=None, description="Фильтр по каналам (None = все)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "question": "Какие новости о технологиях за последнюю неделю?",
                "top_k": 5,
                "channels": None,
            }
        }


class CompletionResponseSchema(BaseModel):
    """Схема ответа на вопрос."""

    answer: str = Field(..., description="Сгенерированный ответ")
    sources: List[SourceSchema] = Field(
        default_factory=list, description="Источники информации"
    )
    processing_time: float = Field(
        default=0.0, description="Время обработки в секундах"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "На основе мониторинга новостей...",
                "sources": [
                    {
                        "channel": "rbc_news",
                        "date": "2025-01-08T10:00:00",
                        "post_id": 12345,
                        "url": "https://t.me/rbc_news/12345",
                        "relevance_score": 0.95,
                    }
                ],
                "processing_time": 1.5,
            }
        }
