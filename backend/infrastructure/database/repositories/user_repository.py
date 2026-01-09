"""Репозиторий для работы с пользователями в PostgreSQL."""

from typing import List, Optional

from domain.channel import Channel, ChannelStatus
from infrastructure.database.models import ChannelModel, UserModel
from infrastructure.database.repositories.base import (
    AsyncBaseRepository,
    BaseRepository,
)
from services.interfaces.database import IUserRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, session: Session):
        super().__init__(UserModel, session)

    def get_by_telegram_id(self, telegram_id: int) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        return self._session.scalars(stmt).first()

    def get_or_create(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> UserModel:
        user = self.get_by_telegram_id(telegram_id)
        if user:
            return user

        user = UserModel(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        return self.create(user)

    def get_active_users(self) -> List[UserModel]:
        stmt = select(UserModel).where(UserModel.is_active == True)
        return list(self._session.scalars(stmt).all())

    def add_channel_to_user(self, user: UserModel, channel: ChannelModel) -> None:
        if channel not in user.channels:
            user.channels.append(channel)
            self._session.commit()

    def remove_channel_from_user(self, user: UserModel, channel: ChannelModel) -> None:
        if channel in user.channels:
            user.channels.remove(channel)
            self._session.commit()


class AsyncUserRepository(AsyncBaseRepository[UserModel], IUserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(UserModel, session)

    def _to_dict(self, model: UserModel) -> dict:
        return {
            "id": model.id,
            "telegram_id": model.telegram_id,
            "username": model.username,
            "first_name": model.first_name,
            "last_name": model.last_name,
            "is_active": model.is_active,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    def _channel_to_domain(self, model: ChannelModel) -> Channel:
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

    async def get_by_id(self, user_id: int) -> Optional[dict]:
        model = await super().get_by_id(user_id)
        return self._to_dict(model) if model else None

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self._session.scalars(stmt)
        model = result.first()
        return self._to_dict(model) if model else None

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> dict:
        user_dict = await self.get_by_telegram_id(telegram_id)
        if user_dict:
            return user_dict

        user = UserModel(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return self._to_dict(user)

    async def get_active_users(self) -> List[dict]:
        stmt = select(UserModel).where(UserModel.is_active == True)
        result = await self._session.scalars(stmt)
        return [self._to_dict(m) for m in result.all()]

    async def add_channel_to_user(self, user_id: int, channel_id: int) -> None:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.channels))
            .where(UserModel.id == user_id)
        )
        result = await self._session.scalars(stmt)
        user = result.first()

        if user:
            channel = await self._session.get(ChannelModel, channel_id)
            if channel and channel not in user.channels:
                user.channels.append(channel)
                await self._session.commit()

    async def remove_channel_from_user(self, user_id: int, channel_id: int) -> None:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.channels))
            .where(UserModel.id == user_id)
        )
        result = await self._session.scalars(stmt)
        user = result.first()

        if user:
            channel = await self._session.get(ChannelModel, channel_id)
            if channel and channel in user.channels:
                user.channels.remove(channel)
                await self._session.commit()

    async def get_user_channels(self, user_id: int) -> List[Channel]:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.channels))
            .where(UserModel.id == user_id)
        )
        result = await self._session.scalars(stmt)
        user = result.first()

        if user:
            return [self._channel_to_domain(ch) for ch in user.channels]
        return []
