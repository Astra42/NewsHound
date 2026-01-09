"""
Доменные модели для запросов и ответов AI.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Ссылка на источник ответа."""

    channel: str = Field(..., description="Название канала")
    date: Optional[datetime] = Field(default=None, description="Дата публикации")
    post_id: Optional[int] = Field(default=None, description="ID поста")
    url: Optional[str] = Field(default=None, description="Ссылка на пост")
    relevance_score: float = Field(default=0.0, description="Оценка релевантности")


class CompletionRequest(BaseModel):
    """Запрос на генерацию ответа (RAG)."""

    user_id: int = Field(..., description="ID пользователя Telegram")
    question: str = Field(..., description="Вопрос пользователя")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Количество документов для контекста"
    )
    channels: Optional[List[str]] = Field(
        default=None, description="Фильтр по каналам (None = все)"
    )


class CompletionResponse(BaseModel):
    """Ответ на вопрос пользователя."""

    answer: str = Field(..., description="Сгенерированный ответ")
    sources: List[SourceReference] = Field(
        default_factory=list, description="Источники информации"
    )
    processing_time: float = Field(default=0.0, description="Время обработки (сек)")
    tokens_used: Optional[int] = Field(default=None, description="Использовано токенов")


class SummaryRequest(BaseModel):
    """Запрос на генерацию саммари."""

    user_id: int = Field(..., description="ID пользователя Telegram")
    start_date: datetime = Field(..., description="Начало периода")
    end_date: datetime = Field(..., description="Конец периода")
    channels: Optional[List[str]] = Field(
        default=None, description="Фильтр по каналам (None = все)"
    )
    max_topics: int = Field(
        default=5, ge=1, le=10, description="Максимум тем в саммари"
    )


class SummaryResponse(BaseModel):
    """Саммари за период."""

    summary: str = Field(..., description="Текст саммари")
    posts_processed: int = Field(default=0, description="Обработано постов")
    period: str = Field(..., description="Период в текстовом виде")
    topics: List[str] = Field(default_factory=list, description="Выделенные темы")
    channels_included: List[str] = Field(
        default_factory=list, description="Каналы, вошедшие в саммари"
    )
    processing_time: float = Field(default=0.0, description="Время обработки (сек)")
