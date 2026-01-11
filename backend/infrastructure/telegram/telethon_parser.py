"""Pyrogram парсер Telegram-каналов.

Реализация парсера на основе библиотеки Pyrogram вместо Telethon.
Обеспечивает совместимость с интерфейсом IChannelParser.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, List, Optional

from core.config import settings
from core.exceptions import (
    InvalidChannelLinkException,
    TelegramParserException,
)
from domain.channel import Channel, ChannelStatus
from domain.document import Document, DocumentMetadata
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import (
    UsernameInvalid,
    UsernameNotOccupied,
)
from pyrogram.types import Chat
from services.interfaces.channel_parser import IChannelParser


class TelethonChannelParser(IChannelParser):
    """Парсер Telegram-каналов на основе Pyrogram.

    Класс сохраняет название TelethonChannelParser для обратной совместимости,
    но использует библиотеку Pyrogram для работы с Telegram API.
    """

    def __init__(
        self,
        api_id: Optional[str] = None,
        api_hash: Optional[str] = None,
        session_name: str = "session",
    ):
        self._api_id = api_id or settings.telegram_api_id
        self._api_hash = api_hash or settings.telegram_api_hash

        if Path("/app").exists() and Path("/app").is_dir():
            # В Docker контейнере используем /app/sessions (volume из docker-compose.yml)
            sessions_dir = Path("/app/sessions")
        else:
            project_root = Path(__file__).parent.parent.parent
            sessions_dir = project_root / "sessions"

        sessions_dir.mkdir(parents=True, exist_ok=True)
        # Pyrogram автоматически добавляет расширение .session
        # Передаем путь без расширения, например: /app/sessions/session
        self._session_path = sessions_dir / session_name

        # Pyrogram Client создается лениво в connect(), чтобы избежать проблем с event loop
        # при инициализации в worker thread (FastAPI dependencies)
        self._client: Optional[Client] = None
        self._is_connected = False

    def _get_client(self) -> Client:
        """Получить или создать Pyrogram Client.

        Создается лениво, чтобы избежать проблем с event loop при инициализации
        в worker thread (когда FastAPI вызывает __init__ через run_in_threadpool).
        """
        if self._client is None:
            # В Pyrogram клиент создается без параметров авторизации
            # Авторизация происходит при вызове start()
            self._client = Client(
                name=str(self._session_path),
                api_id=int(self._api_id)
                if self._api_id and self._api_id.isdigit()
                else None,
                api_hash=self._api_hash,
            )
        return self._client

    @property
    def is_connected(self) -> bool:
        """Статус подключения."""
        if self._client is None:
            return False
        return self._is_connected and self._client.is_connected

    async def connect(self) -> None:
        """Подключение к Telegram API.

        Проверяет наличие авторизованной сессии. Если сессии нет или она не авторизована,
        просто выводит сообщение. Клиент все равно запускается для возможности работы.
        Исключения не выбрасываются.
        """
        if self.is_connected:
            return

        # Получаем или создаем клиент (ленивая инициализация)
        client = self._get_client()
        session_file = Path(str(self._session_path) + ".session")

        # Запускаем клиент, если он еще не запущен
        if not client.is_connected:
            try:
                await client.start()
            except Exception as e:
                print(f"Не удалось запустить клиент Telegram: {e}")
                return

        # Проверяем, существует ли файл сессии
        if not session_file.exists():
            print(f"Файл сессии не найден: {session_file}")
            print("Для работы необходимо создать и авторизовать сессию Telegram.")
            return

        # Проверяем, авторизована ли сессия
        try:
            me = await client.get_me()
            if me:
                # Сессия существует и авторизована - устанавливаем флаг подключения
                self._is_connected = True
                return
        except Exception:
            # Сессия не авторизована или повреждена
            print(f"Сессия не авторизована или повреждена: {session_file}")
            print("Необходимо заново создать и авторизовать сессию Telegram.")
            return

        # Если дошли сюда - сессия не авторизована
        print(f"Сессия существует, но не авторизована: {session_file}")
        print("Необходимо авторизовать сессию Telegram.")

    async def disconnect(self) -> None:
        """Отключение от Telegram API."""
        if self._client is not None and self.is_connected:
            if self._client.is_connected:
                await self._client.stop()
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

    def _extract_text_from_message(self, message) -> Optional[str]:
        """Извлечь текст из сообщения разных типов.

        Поддерживает:
        - message.text - обычный текст
        - message.caption - подпись к медиа
        - message.poll.question - вопрос опроса
        - message.game.title - название игры

        Args:
            message: объект Message из Pyrogram

        Returns:
            текст сообщения или None, если текста нет
        """
        if message.text:
            return message.text
        if message.caption:
            return message.caption
        if message.poll and message.poll.question:
            return message.poll.question
        if message.game and message.game.title:
            return message.game.title
        return None

    async def get_channel_info(self, channel_link: str) -> Channel:
        await self.connect()

        username = self._extract_username(channel_link)
        client = self._get_client()

        # Убеждаемся, что клиент запущен
        if not client.is_connected:
            try:
                await client.start()
            except Exception as e:
                raise TelegramParserException(
                    f"Не удалось запустить клиент Telegram: {e}"
                ) from e

        try:
            chat: Chat = await client.get_chat(username)

            # Проверяем, что это канал (channel) или супергруппа (supergroup)
            # В Pyrogram каналы могут быть типа "channel" или "supergroup"
            if chat.type not in (ChatType.CHANNEL, ChatType.SUPERGROUP):
                raise InvalidChannelLinkException(
                    f"{channel_link} не является каналом (это {chat.type})"
                )

            return Channel(
                telegram_id=chat.id,
                username=chat.username or username,
                title=chat.title,
                description=chat.description,
                link=f"https://t.me/{chat.username or username}",
                status=ChannelStatus.ACTIVE,
            )

        except UsernameInvalid:
            raise InvalidChannelLinkException(
                f"Неверный username канала: {channel_link}"
            )
        except UsernameNotOccupied:
            raise InvalidChannelLinkException(f"Канал не найден: {channel_link}")
        except Exception as e:
            if "not found" in str(e).lower() or "could not find" in str(e).lower():
                raise InvalidChannelLinkException(channel_link)
            raise TelegramParserException(
                f"Ошибка получения информации о канале: {e}"
            ) from e

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
        client = self._get_client()

        # Убеждаемся, что клиент запущен
        if not client.is_connected:
            try:
                await client.start()
            except Exception as e:
                raise TelegramParserException(
                    f"Не удалось запустить клиент Telegram: {e}"
                ) from e

        try:
            chat = await client.get_chat(channel.username)
        except Exception as e:
            raise TelegramParserException(
                f"Не удалось получить канал {channel.username}: {e}"
            ) from e

        yielded = 0
        seen_media_groups: set[int] = set()

        def _describe_media(msg) -> str:
            """Более надежно определяем тип медиа для fallback."""
            # 1) если есть enum media (Pyrogram), используем его
            media_enum = getattr(msg, "media", None)
            if media_enum:
                try:
                    return str(media_enum).split(".")[-1].lower()
                except Exception:
                    pass

            # 2) иначе — по полям
            parts = []
            for attr in (
                "photo",
                "video",
                "animation",
                "document",
                "audio",
                "voice",
                "sticker",
                "poll",
                "web_page",
            ):
                if getattr(msg, attr, None):
                    parts.append(attr)

            return ", ".join(parts) if parts else "unknown"

        def _fallback_single(msg) -> str:
            descr = _describe_media(msg)

            fwd = ""
            if getattr(msg, "forward_from_chat", None):
                try:
                    src = (
                        msg.forward_from_chat.title
                        or msg.forward_from_chat.username
                        or "unknown"
                    )
                    fwd = f" | forward_from={src}"
                except Exception:
                    fwd = " | forward_from=unknown"

            return f"[media_post: {descr}{fwd}]"

        def _fallback_album(group_msgs) -> str:
            type_counts: dict[str, int] = {}
            for m in group_msgs:
                t = _describe_media(m)
                type_counts[t] = type_counts.get(t, 0) + 1
            counts_str = "; ".join([f"{k} x{v}" for k, v in type_counts.items()])
            return f"[album: {len(group_msgs)} items | {counts_str}]"

        try:
            async for message in client.get_chat_history(
                chat.id,
                limit=limit,
                # offset_date=offset_date,
            ):
                # service/empty пропускаем
                if message.empty or message.service:
                    continue

                content: Optional[str] = None

                # --------- ALBUM (media_group_id) ----------
                if message.media_group_id:
                    gid = message.media_group_id
                    if gid in seen_media_groups:
                        continue
                    seen_media_groups.add(gid)

                    # ВАЖНО: используем Client.get_media_group(), он надежнее message.get_media_group()
                    # и корректно поднимает группу по chat_id/message_id.
                    try:
                        group_messages = await client.get_media_group(
                            chat.id, message.id
                        )
                    except Exception:
                        group_messages = [message]

                    # Канонический "пост" для t.me/<channel>/<id>:
                    # в UI ссылка обычно соответствует минимальному message.id в группе
                    # (а в истории вы можете встретить не первый элемент).
                    root_message = min(group_messages, key=lambda m: m.id)

                    # Ищем текст в ЛЮБОМ элементе группы (caption/text/poll/game)
                    for m in group_messages:
                        extracted = self._extract_text_from_message(m)
                        if extracted:
                            content = extracted
                            break

                    # Если текста нет — всё равно создаём документ (чтобы "парсить любой пост")
                    if not content:
                        content = _fallback_album(group_messages)

                    message_id_for_doc = root_message.id
                    date_for_doc = root_message.date
                    views_for_doc = root_message.views or 0

                # --------- SINGLE MESSAGE ----------
                else:
                    extracted = self._extract_text_from_message(message)
                    if extracted:
                        content = extracted
                    else:
                        # текста нет — не пропускаем, а делаем fallback
                        content = _fallback_single(message)

                    message_id_for_doc = message.id
                    date_for_doc = message.date
                    views_for_doc = message.views or 0

                # --------- BUILD DOCUMENT ----------
                metadata = DocumentMetadata(
                    source="telegram",
                    channel=channel.username,
                    channel_id=channel.telegram_id,
                    message_id=message_id_for_doc,
                    date=date_for_doc,
                    url=f"https://t.me/{channel.username}/{message_id_for_doc}",
                    views=views_for_doc,
                )

                document = Document(
                    id=f"{channel.username}_{message_id_for_doc}",
                    content=content,
                    metadata=metadata,
                )

                yield document
                yielded += 1
                if yielded >= limit:
                    break

        except Exception as e:
            raise TelegramParserException(
                f"Ошибка при парсинге постов канала {channel.username}: {e}"
            ) from e

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
