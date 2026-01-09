"""
Интерфейс для парсера Telegram-каналов.

Принцип SOLID:
- Interface Segregation: только методы для работы с Telegram
- Single Responsibility: парсинг каналов
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator, List, Optional

from domain.channel import Channel
from domain.document import Document


class IChannelParser(ABC):
    """Абстрактный интерфейс для парсера Telegram-каналов."""

    @abstractmethod
    async def get_channel_info(self, channel_link: str) -> Channel:
        """
        Получение информации о канале.

        Args:
            channel_link: ссылка на канал (@channel или https://t.me/channel)

        Returns:
            объект Channel с информацией
        """
        pass

    @abstractmethod
    async def parse_channel_posts(
        self,
        channel: Channel,
        limit: int = 100,
        offset_date: Optional[datetime] = None,
    ) -> List[Document]:
        """
        Парсинг постов канала.

        Args:
            channel: канал для парсинга
            limit: максимальное количество постов
            offset_date: дата, с которой начинать парсинг (None = с начала)

        Returns:
            список документов (постов)
        """
        pass

    @abstractmethod
    async def parse_channel_posts_stream(
        self,
        channel: Channel,
        limit: int = 100,
        offset_date: Optional[datetime] = None,
    ) -> AsyncIterator[Document]:
        """
        Стриминг постов канала (для больших объёмов).

        Args:
            channel: канал для парсинга
            limit: максимальное количество постов
            offset_date: дата, с которой начинать

        Yields:
            документы по одному
        """
        pass

    @abstractmethod
    async def validate_channel(self, channel_link: str) -> bool:
        """
        Проверка доступности канала.

        Args:
            channel_link: ссылка на канал

        Returns:
            True если канал доступен и публичный
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Подключение к Telegram API."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Отключение от Telegram API."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Статус подключения."""
        pass
