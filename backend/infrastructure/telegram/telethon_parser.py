"""Telethon парсер Telegram-каналов."""

import re
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, List, Optional

from telethon import TelegramClient
from telethon.tl.types import Channel as TelegramChannel

from backend.core.config import settings
from backend.core.exceptions import (
    InvalidChannelLinkException,
    TelegramAuthException,
    TelegramParserException,
)
from backend.domain.channel import Channel, ChannelStatus
from backend.domain.document import Document, DocumentMetadata
from backend.services.interfaces.channel_parser import IChannelParser


class TelethonChannelParser(IChannelParser):
    def __init__(
        self,
        api_id: Optional[str] = None,
        api_hash: Optional[str] = None,
        session_name: str = "newshound_session",
    ):
        self._api_id = api_id or settings.telegram_api_id
        self._api_hash = api_hash or settings.telegram_api_hash

        if Path("/app").exists() and Path("/app").is_dir():
            sessions_dir = Path("/app/.telethon_sessions")
        else:
            project_root = Path(__file__).parent.parent.parent.parent
            sessions_dir = project_root / ".telethon_sessions"

        sessions_dir.mkdir(parents=True, exist_ok=True)
        self._session_name = str(sessions_dir / session_name)

        self._client = TelegramClient(
            self._session_name,
            self._api_id,
            self._api_hash,
        )
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Статус подключения."""
        return self._is_connected and self._client.is_connected()

    async def connect(self) -> None:
        """Подключение к Telegram API. Боты не могут читать историю каналов - нужен пользовательский аккаунт."""
        if not self.is_connected:
            if not settings.telegram_phone:
                raise TelegramAuthException(
                    "TELEGRAM_PHONE не указан в .env. "
                    "Для парсинга каналов нужна авторизация через пользовательский аккаунт. "
                    "Укажите номер телефона с кодом страны (например, +79991234567). "
                    "Интерактивный ввод отключен."
                )

            code_callback = None
            if settings.telegram_code:

                def get_code():
                    return settings.telegram_code

                code_callback = get_code

            await self._client.start(
                phone=settings.telegram_phone,
                code_callback=code_callback,
            )
            self._is_connected = True

    async def disconnect(self) -> None:
        """Отключение от Telegram API."""
        if self.is_connected:
            await self._client.disconnect()
            self._is_connected = False

    def _extract_username(self, link: str) -> str:
        """Извлечение username из ссылки."""
        if link.startswith("@"):
            return link[1:]

        pattern = r"(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)"
        match = re.match(pattern, link)
        if match:
            return match.group(1)

        return link.strip()

    async def get_channel_info(self, channel_link: str) -> Channel:
        await self.connect()

        username = self._extract_username(channel_link)

        try:
            entity = await self._client.get_entity(username)

            if not isinstance(entity, TelegramChannel):
                raise InvalidChannelLinkException(channel_link)

            return Channel(
                telegram_id=entity.id,
                username=entity.username or username,
                title=entity.title,
                description=getattr(entity, "about", None),
                link=f"https://t.me/{entity.username or username}",
                status=ChannelStatus.ACTIVE,
            )

        except Exception as e:
            if "Could not find" in str(e) or "No user has" in str(e):
                raise InvalidChannelLinkException(channel_link)
            raise TelegramParserException(f"Ошибка получения информации о канале: {e}")

    async def parse_channel_posts(
        self,
        channel: Channel,
        limit: int = 100,
        offset_date: Optional[datetime] = None,
    ) -> List[Document]:
        documents = []

        async for doc in self.parse_channel_posts_stream(channel, limit, offset_date):
            documents.append(doc)

        return documents

    async def parse_channel_posts_stream(
        self,
        channel: Channel,
        limit: int = 100,
        offset_date: Optional[datetime] = None,
    ) -> AsyncIterator[Document]:
        await self.connect()

        try:
            entity = await self._client.get_entity(channel.username)
        except Exception as e:
            raise TelegramParserException(
                f"Не удалось получить канал {channel.username}: {e}"
            )

        count = 0
        async for message in self._client.iter_messages(
            entity,
            limit=limit,
            offset_date=offset_date,
        ):
            if not message.text:
                continue

            metadata = DocumentMetadata(
                source="telegram",
                channel=channel.username,
                channel_id=channel.telegram_id,
                message_id=message.id,
                date=message.date,
                url=f"https://t.me/{channel.username}/{message.id}",
                views=message.views,
            )

            document = Document(
                id=f"{channel.username}_{message.id}",
                content=message.text,
                metadata=metadata,
            )

            yield document
            count += 1

            if count >= limit:
                break

    async def validate_channel(self, channel_link: str) -> bool:
        try:
            await self.get_channel_info(channel_link)
            return True
        except (InvalidChannelLinkException, TelegramParserException):
            return False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
