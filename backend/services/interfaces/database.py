"""
Интерфейсы для репозиториев базы данных.

Принцип SOLID:
- Interface Segregation: отдельные интерфейсы для каждой сущности
- Dependency Inversion: сервисы зависят от этих абстракций
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from domain.channel import Channel
from domain.document import Document


class IChannelRepository(ABC):
    """Абстрактный интерфейс для репозитория каналов."""

    @abstractmethod
    async def get_by_id(self, channel_id: int) -> Optional[Channel]:
        """
        Получить канал по ID.

        Args:
            channel_id: ID канала в БД

        Returns:
            канал или None
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[Channel]:
        """
        Получить канал по username.

        Args:
            username: username канала (без @)

        Returns:
            канал или None
        """
        pass

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Channel]:
        """
        Получить канал по Telegram ID.

        Args:
            telegram_id: ID канала в Telegram

        Returns:
            канал или None
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Channel]:
        """
        Получить все каналы с пагинацией.

        Args:
            skip: количество пропускаемых записей
            limit: максимальное количество записей

        Returns:
            список каналов
        """
        pass

    @abstractmethod
    async def get_active_channels(self) -> List[Channel]:
        """
        Получить все активные каналы.

        Returns:
            список активных каналов
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Channel]:
        """
        Получить каналы по статусу.

        Args:
            status: статус канала

        Returns:
            список каналов
        """
        pass

    @abstractmethod
    async def create(self, channel: Channel) -> Channel:
        """
        Создать новый канал.

        Args:
            channel: данные канала

        Returns:
            созданный канал с ID
        """
        pass

    @abstractmethod
    async def update(self, channel: Channel) -> Channel:
        """
        Обновить канал.

        Args:
            channel: обновлённые данные канала

        Returns:
            обновлённый канал
        """
        pass

    @abstractmethod
    async def delete(self, channel_id: int) -> bool:
        """
        Удалить канал.

        Args:
            channel_id: ID канала

        Returns:
            True если удалён
        """
        pass

    @abstractmethod
    async def update_status(self, channel_id: int, status: str) -> bool:
        """
        Обновить статус канала.

        Args:
            channel_id: ID канала
            status: новый статус

        Returns:
            True если обновлён
        """
        pass

    @abstractmethod
    async def increment_posts_count(self, channel_id: int, count: int = 1) -> None:
        """
        Увеличить счётчик постов.

        Args:
            channel_id: ID канала
            count: количество для добавления
        """
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """
        Проверить существование канала по username.

        Args:
            username: username канала

        Returns:
            True если существует
        """
        pass


class IPostRepository(ABC):
    """Абстрактный интерфейс для репозитория постов."""

    @abstractmethod
    async def get_by_id(self, post_id: int) -> Optional[Document]:
        """
        Получить пост по ID.

        Args:
            post_id: ID поста в БД

        Returns:
            документ или None
        """
        pass

    @abstractmethod
    async def get_by_channel_and_message(
        self, channel_id: int, message_id: int
    ) -> Optional[Document]:
        """
        Получить пост по channel_id и message_id.

        Args:
            channel_id: ID канала в БД
            message_id: ID сообщения в Telegram

        Returns:
            документ или None
        """
        pass

    @abstractmethod
    async def get_by_channel(
        self, channel_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Получить посты канала.

        Args:
            channel_id: ID канала
            skip: пропустить записей
            limit: максимум записей

        Returns:
            список документов
        """
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        channel_ids: Optional[List[int]] = None,
    ) -> List[Document]:
        """
        Получить посты за период.

        Args:
            start_date: начало периода
            end_date: конец периода
            channel_ids: фильтр по каналам

        Returns:
            список документов
        """
        pass

    @abstractmethod
    async def exists(self, channel_id: int, message_id: int) -> bool:
        """
        Проверить существование поста.

        Args:
            channel_id: ID канала
            message_id: ID сообщения

        Returns:
            True если существует
        """
        pass

    @abstractmethod
    async def create(self, document: Document, channel_id: int) -> Document:
        """
        Создать пост.

        Args:
            document: данные документа
            channel_id: ID канала

        Returns:
            созданный документ
        """
        pass

    @abstractmethod
    async def bulk_create(
        self, documents: List[Document], channel_id: int
    ) -> List[Document]:
        """
        Массовое создание постов.

        Args:
            documents: список документов
            channel_id: ID канала

        Returns:
            созданные документы
        """
        pass

    @abstractmethod
    async def delete_by_channel(self, channel_id: int) -> int:
        """
        Удалить все посты канала.

        Args:
            channel_id: ID канала

        Returns:
            количество удалённых постов
        """
        pass


class IUserRepository(ABC):
    """Абстрактный интерфейс для репозитория пользователей."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[dict]:
        """
        Получить пользователя по ID.

        Args:
            user_id: ID пользователя в БД

        Returns:
            данные пользователя или None
        """
        pass

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """
        Получить пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            данные пользователя или None
        """
        pass

    @abstractmethod
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> dict:
        """
        Получить или создать пользователя.

        Args:
            telegram_id: Telegram ID
            username: username
            first_name: имя
            last_name: фамилия

        Returns:
            данные пользователя
        """
        pass

    @abstractmethod
    async def get_active_users(self) -> List[dict]:
        """
        Получить активных пользователей.

        Returns:
            список пользователей
        """
        pass

    @abstractmethod
    async def add_channel_to_user(self, user_id: int, channel_id: int) -> None:
        """
        Добавить канал пользователю.

        Args:
            user_id: ID пользователя
            channel_id: ID канала
        """
        pass

    @abstractmethod
    async def remove_channel_from_user(self, user_id: int, channel_id: int) -> None:
        """
        Удалить канал у пользователя.

        Args:
            user_id: ID пользователя
            channel_id: ID канала
        """
        pass

    @abstractmethod
    async def get_user_channels(self, user_id: int) -> List[Channel]:
        """
        Получить каналы пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            список каналов
        """
        pass
