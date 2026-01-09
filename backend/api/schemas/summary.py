"""
Схемы для API summary.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SummaryRequestSchema(BaseModel):
    """Схема запроса на генерацию саммари."""

    user_id: int = Field(..., description="ID пользователя Telegram")
    start_date: datetime = Field(..., description="Начало периода")
    end_date: datetime = Field(..., description="Конец периода")
    channels: Optional[List[str]] = Field(
        default=None, description="Фильтр по каналам (None = все)"
    )
    max_topics: int = Field(
        default=5, ge=1, le=10, description="Максимум тем в саммари"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "start_date": "2025-01-01T00:00:00",
                "end_date": "2025-01-08T23:59:59",
                "channels": ["rbc_news", "tass_agency"],
                "max_topics": 5,
            }
        }


class SummaryResponseSchema(BaseModel):
    """Схема ответа с саммари."""

    summary: str = Field(..., description="Текст саммари")
    posts_processed: int = Field(default=0, description="Обработано постов")
    period: str = Field(..., description="Период в текстовом виде")
    topics: List[str] = Field(default_factory=list, description="Выделенные темы")
    channels_included: List[str] = Field(
        default_factory=list, description="Каналы, вошедшие в саммари"
    )
    processing_time: float = Field(
        default=0.0, description="Время обработки в секундах"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "📰 САММАРИ НОВОСТЕЙ ЗА 01.01.2025 — 08.01.2025\n\n📌 Политика:\n...",
                "posts_processed": 47,
                "period": "01.01.2025 — 08.01.2025",
                "topics": ["Политика", "Экономика", "Технологии"],
                "channels_included": ["rbc_news", "tass_agency"],
                "processing_time": 5.2,
            }
        }
