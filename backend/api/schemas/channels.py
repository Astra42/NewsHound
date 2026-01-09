"""
Схемы для API управления каналами.
"""

from datetime import datetime
from typing import List, Optional

from domain.channel import ChannelStatus
from pydantic import BaseModel, Field


class AddChannelRequestSchema(BaseModel):
    """Схема запроса на добавление канала."""

    channel_link: str = Field(
        ..., description="Ссылка на канал (@channel или https://t.me/channel)"
    )
    index_posts: bool = Field(
        default=True, description="Индексировать посты при добавлении"
    )
    posts_limit: Optional[int] = Field(
        default=None, ge=1, le=1000, description="Лимит постов для индексации"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "channel_link": "https://t.me/rbc_news",
                "index_posts": True,
                "posts_limit": 100,
            }
        }


class RemoveChannelRequestSchema(BaseModel):
    """Схема запроса на удаление канала."""

    channel_link: str = Field(..., description="Ссылка на канал или username")


class ChannelResponseSchema(BaseModel):
    """Схема ответа с информацией о канале."""

    username: str = Field(..., description="Username канала")
    title: Optional[str] = Field(default=None, description="Название канала")
    link: str = Field(..., description="Ссылка на канал")
    status: ChannelStatus = Field(..., description="Статус канала")
    posts_count: int = Field(default=0, description="Количество постов")
    last_post_date: Optional[datetime] = Field(
        default=None, description="Дата последнего поста"
    )
    created_at: datetime = Field(..., description="Дата добавления")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "rbc_news",
                "title": "РБК",
                "link": "https://t.me/rbc_news",
                "status": "active",
                "posts_count": 100,
                "last_post_date": "2025-01-08T15:30:00",
                "created_at": "2025-01-01T10:00:00",
            }
        }


class ChannelListResponseSchema(BaseModel):
    """Схема списка каналов."""

    channels: List[ChannelResponseSchema] = Field(
        default_factory=list, description="Список каналов"
    )
    total: int = Field(default=0, description="Общее количество каналов")
