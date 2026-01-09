"""Сервис для управления Telegram-каналами."""

from datetime import datetime
from typing import List, Optional

from backend.core.config import settings
from backend.core.exceptions import (
    ChannelAlreadyExistsException,
    ChannelNotFoundException,
    TelegramParserException,
)
from backend.domain.channel import Channel, ChannelStatus
from backend.domain.document import Document
from backend.services.interfaces.channel_parser import IChannelParser
from backend.services.interfaces.database import IChannelRepository, IPostRepository
from backend.services.interfaces.vectorstore import IVectorStoreRepository


class ChannelService:
    def __init__(
        self,
        channel_parser: IChannelParser,
        vectorstore_repository: IVectorStoreRepository,
        channel_repository: IChannelRepository,
        post_repository: IPostRepository,
    ):
        self._parser = channel_parser
        self._vectorstore = vectorstore_repository
        self._channel_repo = channel_repository
        self._post_repo = post_repository

    async def add_channel(
        self,
        channel_link: str,
        index_posts: bool = True,
        posts_limit: int = None,
    ) -> Channel:
        posts_limit = posts_limit or settings.telegram_message_limit

        channel_info = await self._parser.get_channel_info(channel_link)

        existing = await self._channel_repo.get_by_username(channel_info.username)
        if existing:
            raise ChannelAlreadyExistsException(channel_info.username)

        channel = Channel(
            telegram_id=channel_info.telegram_id,
            username=channel_info.username,
            title=channel_info.title,
            description=channel_info.description,
            link=channel_info.link,
            status=ChannelStatus.INDEXING,
        )

        channel = await self._channel_repo.create(channel)

        if index_posts:
            try:
                posts_count = await self._index_channel_posts(channel, posts_limit)
                channel.posts_count = posts_count
                channel.status = ChannelStatus.ACTIVE
                channel = await self._channel_repo.update(channel)
            except Exception as e:
                channel.status = ChannelStatus.ERROR
                await self._channel_repo.update(channel)
                raise TelegramParserException(f"Ошибка индексации: {e}")
        else:
            channel.status = ChannelStatus.ACTIVE
            channel = await self._channel_repo.update(channel)

        return channel

    async def remove_channel(self, channel_link: str) -> bool:
        username = self._extract_username(channel_link)

        channel = await self._channel_repo.get_by_username(username)
        if not channel:
            raise ChannelNotFoundException(username)

        self._vectorstore.delete_documents(filter_dict={"channel": username})
        await self._post_repo.delete_by_channel(channel.id)
        await self._channel_repo.delete(channel.id)

        return True

    async def get_channels(self) -> List[Channel]:
        return await self._channel_repo.get_all(limit=1000)

    async def get_channel(self, channel_link: str) -> Optional[Channel]:
        username = self._extract_username(channel_link)
        return await self._channel_repo.get_by_username(username)

    async def refresh_channel(
        self,
        channel_link: str,
        posts_limit: int = None,
    ) -> int:
        username = self._extract_username(channel_link)

        channel = await self._channel_repo.get_by_username(username)
        if not channel:
            raise ChannelNotFoundException(username)

        posts_limit = posts_limit or settings.telegram_message_limit

        new_posts_count = await self._index_channel_posts(
            channel,
            posts_limit,
            offset_date=channel.last_post_date,
        )

        channel.posts_count += new_posts_count
        await self._channel_repo.update(channel)

        return new_posts_count

    async def _index_channel_posts(
        self,
        channel: Channel,
        limit: int,
        offset_date: datetime = None,
    ) -> int:
        documents: List[Document] = []
        last_post_date: Optional[datetime] = None

        async for doc in self._parser.parse_channel_posts_stream(
            channel,
            limit=limit,
            offset_date=offset_date,
        ):
            if doc.metadata.message_id:
                exists = await self._post_repo.exists(
                    channel.id, doc.metadata.message_id
                )
                if exists:
                    continue

            documents.append(doc)

            if doc.metadata.date:
                if last_post_date is None or doc.metadata.date > last_post_date:
                    last_post_date = doc.metadata.date

        if documents:
            await self._vectorstore.aadd_documents(documents)
            await self._post_repo.bulk_create(documents, channel.id)

        if last_post_date:
            channel.last_post_date = last_post_date
            await self._channel_repo.update(channel)

        return len(documents)

    def _extract_username(self, link: str) -> str:
        """Извлечение username из ссылки."""
        if link.startswith("@"):
            return link[1:]
        if "t.me/" in link:
            return link.split("t.me/")[-1].split("/")[0].split("?")[0]
        return link.strip()
