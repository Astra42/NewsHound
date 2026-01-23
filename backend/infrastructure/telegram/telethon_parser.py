"""
Telethon парсер Telegram-каналов.

Реализация парсера на основе библиотеки Telethon.
Обеспечивает совместимость с интерфейсом IChannelParser.
"""

import re
from pathlib import Path
from typing import AsyncIterator, List, Optional

from core.config import settings
from core.exceptions import InvalidChannelLinkException, TelegramParserException
from domain.channel import Channel, ChannelStatus
from domain.document import Document, DocumentMetadata
from services.interfaces.channel_parser import IChannelParser
from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
    TypeNotFoundError,
)
from telethon.tl.types import Channel as TelethonChannel
from telethon.tl.types import Message


class TelethonChannelParser(IChannelParser):
    """Парсер Telegram-каналов на основе Telethon."""

    def __init__(
        self,
        api_id: Optional[str] = None,
        api_hash: Optional[str] = None,
        session_name: str = "session",
    ):
        self._api_id = api_id or settings.telegram_api_id
        self._api_hash = api_hash or settings.telegram_api_hash

        if Path("/app").exists() and Path("/app").is_dir():
            sessions_dir = Path("/app/sessions")
        else:
            project_root = Path(__file__).parent.parent.parent
            sessions_dir = project_root / "sessions"

        sessions_dir.mkdir(parents=True, exist_ok=True)
        self._session_path = sessions_dir / session_name

        self._client: Optional[TelegramClient] = None
        self._is_connected = False

    def _get_client(self) -> TelegramClient:
        if self._client is None:
            api_id_int: Optional[int] = None
            if self._api_id and str(self._api_id).isdigit():
                api_id_int = int(self._api_id)

            if not api_id_int or not self._api_hash:
                raise TelegramParserException(
                    "Не задан telegram_api_id/telegram_api_hash в настройках."
                )

            self._client = TelegramClient(
                str(self._session_path),
                api_id_int,
                self._api_hash,
            )
        return self._client

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        return self._is_connected and self._client.is_connected()

    async def connect(self) -> None:
        """Подключение к Telegram API с интерактивной авторизацией."""
        if self.is_connected:
            return

        client = self._get_client()

        try:
            if not client.is_connected():
                await client.connect()

            if not await client.is_user_authorized():
                # Пытаемся авторизовать сессию
                phone = (
                    settings.telegram_phone.strip() if settings.telegram_phone else None
                )
                code = (
                    settings.telegram_code.strip() if settings.telegram_code else None
                )

                try:
                    if phone:
                        # Используем телефон из настроек
                        if code:
                            # Если код указан, передаем его
                            await client.start(phone=phone, code=code)
                        else:
                            # Если код не указан, Telethon запросит его интерактивно
                            await client.start(phone=phone)
                    else:
                        # Интерактивный ввод телефона (Telethon запросит телефон и код)
                        await client.start()
                except Exception as auth_error:
                    error_msg = str(auth_error)
                    raise TelegramParserException(
                        f"Не удалось авторизовать сессию: {error_msg}. "
                        f"Проверьте телефон ({phone or 'не указан'}) и код ({code or 'не указан'}) в настройках. "
                        f"Для интерактивной авторизации убедитесь, что код доступа может быть получен в терминале."
                    ) from auth_error

            me = await client.get_me()
            if me:
                self._is_connected = True
                return
        except TelegramParserException:
            raise
        except Exception as e:
            raise TelegramParserException(f"Ошибка подключения к Telegram: {e}") from e

    async def disconnect(self) -> None:
        if self._client is not None and self._client.is_connected():
            await self._client.disconnect()
        self._is_connected = False

    def _extract_username(self, link: str) -> str:
        if link.startswith("@"):
            return link[1:]

        pattern = r"(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)"
        match = re.match(pattern, link)
        if match:
            return match.group(1)

        return link.strip()

    def _extract_text_from_message(self, message: Message) -> Optional[str]:
        """Извлечь текст из сообщения разных типов."""
        # В Telethon текст находится в message.message
        text = message.message
        if text:
            return text.strip() if text.strip() else None

        # Для медиа-сообщений текст может быть в message.raw_text
        if hasattr(message, "raw_text") and message.raw_text:
            return message.raw_text.strip() if message.raw_text.strip() else None

        return None

    def _describe_media(self, message: Message) -> str:
        """Описание медиа-типа сообщения."""
        if not hasattr(message, "media") or not message.media:
            return "text"

        media_type = type(message.media).__name__
        # Убираем префикс MessageMedia
        if media_type.startswith("MessageMedia"):
            media_type = media_type[12:].lower()
        return media_type

    async def get_channel_info(self, channel_link: str) -> Channel:
        await self.connect()
        client = self._get_client()

        username = self._extract_username(channel_link)

        try:
            entity = await client.get_entity(username)

            # Проверяем, что это канал
            if not isinstance(entity, TelethonChannel):
                raise InvalidChannelLinkException(f"{channel_link} не является каналом")

            return Channel(
                telegram_id=entity.id,
                username=entity.username or username,
                title=entity.title,
                description=getattr(entity, "about", None),
                link=f"https://t.me/{entity.username or username}",
                status=ChannelStatus.ACTIVE,
            )

        except UsernameInvalidError:
            raise InvalidChannelLinkException(
                f"Неверный username канала: {channel_link}"
            )
        except UsernameNotOccupiedError:
            raise InvalidChannelLinkException(f"Канал не найден: {channel_link}")
        except ChannelPrivateError:
            raise InvalidChannelLinkException(
                f"Канал приватный или недоступен: {channel_link}"
            )
        except (TypeNotFoundError, ValueError) as e:
            # Ошибка "Could not find a matching Constructor ID" обычно возникает
            # из-за устаревшей сессии или проблем с версией TL схемы
            error_msg = str(e)
            if "Constructor ID" in error_msg or "TLObject" in error_msg:
                raise TelegramParserException(
                    f"Ошибка при получении информации о канале {channel_link}. "
                    f"Возможно, сессия устарела. Попробуйте удалить файл сессии и переавторизоваться. "
                    f"Детали: {error_msg}"
                ) from e
            raise TelegramParserException(
                f"Ошибка получения информации о канале: {error_msg}"
            ) from e
        except InvalidChannelLinkException:
            raise
        except Exception as e:
            error_msg = str(e)
            # Проверяем, не является ли это ошибкой Constructor ID в другом формате
            if "Constructor ID" in error_msg or "TLObject" in error_msg or "fe4478bd" in error_msg:
                raise TelegramParserException(
                    f"Ошибка при получении информации о канале {channel_link}. "
                    f"Сессия Telethon может быть устаревшей. Попробуйте удалить файл сессии "
                    f"(обычно в папке sessions/) и переавторизоваться. "
                    f"Детали: {error_msg}"
                ) from e
            raise TelegramParserException(
                f"Ошибка получения информации о канале: {error_msg}"
            ) from e

    async def validate_channel(self, channel_link: str) -> bool:
        try:
            await self.get_channel_info(channel_link)
            return True
        except (InvalidChannelLinkException, TelegramParserException):
            return False

    async def parse_channel_posts(
        self,
        channel: Channel,
        limit: int = 100,
    ) -> List[Document]:
        documents: List[Document] = []
        async for doc in self.parse_channel_posts_stream(channel, limit):
            documents.append(doc)
        return documents

    async def parse_channel_posts_stream(
        self,
        channel: Channel,
        limit: int = 100,
    ) -> AsyncIterator[Document]:
        await self.connect()
        client = self._get_client()

        try:
            entity = await client.get_entity(channel.username)
        except Exception as e:
            raise TelegramParserException(
                f"Не удалось получить канал {channel.username}: {e}"
            ) from e

        yielded = 0
        seen_grouped_ids: set[int] = set()

        try:
            async for message in client.iter_messages(
                entity,
                limit=limit
                * 3,  # Запрашиваем больше, так как некоторые сообщения будут пропущены
            ):
                # Пропускаем служебные сообщения (action сообщения)
                if message.action is not None:
                    continue

                # -------- ALBUM (grouped messages) --------
                if message.grouped_id:
                    gid = message.grouped_id
                    if gid in seen_grouped_ids:
                        continue  # Альбом уже обработан
                    seen_grouped_ids.add(gid)

                    # Используем первое сообщение группы для обработки
                    # В Telethon получить всю группу сложно, поэтому используем только первое
                    content = self._extract_text_from_message(message)

                    message_id_for_doc = message.id
                    date_for_doc = message.date
                    views_for_doc = getattr(message, "views", 0) or 0

                # -------- SINGLE --------
                else:
                    content = self._extract_text_from_message(message)

                    message_id_for_doc = message.id
                    date_for_doc = message.date
                    views_for_doc = getattr(message, "views", 0) or 0

                metadata = DocumentMetadata(
                    source="telegram",
                    channel=channel.username,
                    channel_id=channel.telegram_id,
                    message_id=message_id_for_doc,
                    date=date_for_doc,
                    url=f"https://t.me/{channel.username}/{message_id_for_doc}",
                    views=views_for_doc,
                )
                if content is None:
                    continue

                yield Document(
                    id=f"{channel.username}_{message_id_for_doc}",
                    content=content,
                    metadata=metadata,
                )

                yielded += 1
                if yielded >= limit:
                    break

        except Exception as e:
            raise TelegramParserException(
                f"Ошибка при парсинге постов канала {channel.username}: {e}"
            ) from e

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
