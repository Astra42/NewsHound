"""Репозиторий для работы с каналами в PostgreSQL."""

from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.domain.channel import Channel, ChannelStatus
from backend.infrastructure.database.models import ChannelModel
from backend.infrastructure.database.repositories.base import (
    AsyncBaseRepository,
    BaseRepository,
)
from backend.services.interfaces.database import IChannelRepository


class ChannelRepository(BaseRepository[ChannelModel]):
    def __init__(self, session: Session):
        super().__init__(ChannelModel, session)

    def get_by_username(self, username: str) -> Optional[ChannelModel]:
        stmt = select(ChannelModel).where(ChannelModel.username == username)
        return self._session.scalars(stmt).first()

    def get_by_telegram_id(self, telegram_id: int) -> Optional[ChannelModel]:
        stmt = select(ChannelModel).where(ChannelModel.telegram_id == telegram_id)
        return self._session.scalars(stmt).first()

    def get_active_channels(self) -> List[ChannelModel]:
        stmt = select(ChannelModel).where(ChannelModel.status == "active")
        return list(self._session.scalars(stmt).all())

    def get_by_status(self, status: str) -> List[ChannelModel]:
        stmt = select(ChannelModel).where(ChannelModel.status == status)
        return list(self._session.scalars(stmt).all())

    def update_status(self, channel_id: int, status: str) -> bool:
        stmt = (
            update(ChannelModel)
            .where(ChannelModel.id == channel_id)
            .values(status=status)
        )
        result = self._session.execute(stmt)
        self._session.commit()
        return result.rowcount > 0

    def increment_posts_count(self, channel_id: int, count: int = 1) -> None:
        channel = self.get_by_id(channel_id)
        if channel:
            channel.posts_count += count
            self._session.commit()

    def exists_by_username(self, username: str) -> bool:
        return self.get_by_username(username) is not None


class AsyncChannelRepository(AsyncBaseRepository[ChannelModel], IChannelRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(ChannelModel, session)

    def _to_domain(self, model: ChannelModel) -> Channel:
        return Channel(
            id=model.id,
            telegram_id=model.telegram_id,
            username=model.username,
            title=model.title,
            description=model.description,
            link=model.link,
            status=ChannelStatus(model.status),
            posts_count=model.posts_count,
            last_post_date=model.last_post_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, channel: Channel) -> ChannelModel:
        return ChannelModel(
            id=channel.id,
            telegram_id=channel.telegram_id,
            username=channel.username,
            title=channel.title,
            description=channel.description,
            link=channel.link,
            status=channel.status.value
            if isinstance(channel.status, ChannelStatus)
            else channel.status,
            posts_count=channel.posts_count,
            updated_at=model.updated_at,
        )

    def _to_model(self, channel: Channel) -> ChannelModel:
        return ChannelModel(
            id=channel.id,
            telegram_id=channel.telegram_id,
            username=channel.username,
            title=channel.title,
            description=channel.description,
            link=channel.link,
            status=channel.status.value
            if isinstance(channel.status, ChannelStatus)
            else channel.status,
            posts_count=channel.posts_count,
            last_post_date=channel.last_post_date,
        )

    async def get_by_id(self, channel_id: int) -> Optional[Channel]:
        model = await super().get_by_id(channel_id)
        return self._to_domain(model) if model else None

    async def get_by_username(self, username: str) -> Optional[Channel]:
        stmt = select(ChannelModel).where(ChannelModel.username == username)
        result = await self._session.scalars(stmt)
        model = result.first()
        return self._to_domain(model) if model else None

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Channel]:
        stmt = select(ChannelModel).where(ChannelModel.telegram_id == telegram_id)
        result = await self._session.scalars(stmt)
        model = result.first()
        return self._to_domain(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Channel]:
        models = await super().get_all(skip=skip, limit=limit)
        return [self._to_domain(m) for m in models]

    async def get_active_channels(self) -> List[Channel]:
        stmt = select(ChannelModel).where(ChannelModel.status == "active")
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result.all()]

    async def get_by_status(self, status: str) -> List[Channel]:
        stmt = select(ChannelModel).where(ChannelModel.status == status)
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result.all()]

    async def create(self, channel: Channel) -> Channel:
        model = self._to_model(channel)
        model.id = None
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, channel: Channel) -> Channel:
        model = await self._session.get(ChannelModel, channel.id)
        if model:
            model.telegram_id = channel.telegram_id
            model.username = channel.username
            model.title = channel.title
            model.description = channel.description
            model.link = channel.link
            model.status = (
                channel.status.value
                if isinstance(channel.status, ChannelStatus)
                else channel.status
            )
            model.posts_count = channel.posts_count
            model.last_post_date = channel.last_post_date
            await self._session.commit()
            await self._session.refresh(model)
            return self._to_domain(model)
        return channel

    async def delete(self, channel_id: int) -> bool:
        model = await self._session.get(ChannelModel, channel_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False

    async def update_status(self, channel_id: int, status: str) -> bool:
        stmt = (
            update(ChannelModel)
            .where(ChannelModel.id == channel_id)
            .values(status=status)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    async def increment_posts_count(self, channel_id: int, count: int = 1) -> None:
        model = await self._session.get(ChannelModel, channel_id)
        if model:
            model.posts_count += count
            await self._session.commit()

    async def exists_by_username(self, username: str) -> bool:
        channel = await self.get_by_username(username)
        return channel is not None
