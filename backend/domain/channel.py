"""
Доменные модели для Telegram-каналов.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChannelStatus(str, Enum):
    """Статус канала."""

    ACTIVE = "active"  # Активный мониторинг
    PAUSED = "paused"  # Мониторинг приостановлен
    INDEXING = "indexing"  # Идёт индексация
    ERROR = "error"  # Ошибка


class Channel(BaseModel):
    """Модель Telegram-канала."""

    id: Optional[int] = Field(default=None, description="ID канала в БД")
    telegram_id: Optional[int] = Field(default=None, description="Telegram ID канала")
    username: str = Field(..., description="Username канала (без @)")
    title: Optional[str] = Field(default=None, description="Название канала")
    description: Optional[str] = Field(default=None, description="Описание канала")
    link: str = Field(..., description="Полная ссылка на канал")
    status: ChannelStatus = Field(
        default=ChannelStatus.ACTIVE, description="Статус канала"
    )
    posts_count: int = Field(
        default=0, description="Количество проиндексированных постов"
    )
    last_post_date: Optional[datetime] = Field(
        default=None, description="Дата последнего поста"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Дата добавления"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Дата последнего обновления"
    )

    @classmethod
    def from_link(cls, link: str) -> "Channel":
        """
        Создание канала из ссылки.

        Args:
            link: ссылка вида https://t.me/channel или @channel
        """
        # Извлекаем username
        if link.startswith("@"):
            username = link[1:]
        elif "t.me/" in link:
            username = link.split("t.me/")[-1].split("/")[0].split("?")[0]
        else:
            username = link

        # Формируем полную ссылку
        full_link = f"https://t.me/{username}"

        return cls(
            username=username,
            link=full_link,
        )

    @property
    def telegram_link(self) -> str:
        """Получить ссылку для Telegram."""
        return f"https://t.me/{self.username}"

    @property
    def mention(self) -> str:
        """Получить @mention."""
        return f"@{self.username}"
