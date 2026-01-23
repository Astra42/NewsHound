"""Репозиторий для работы с постами в PostgreSQL."""

from datetime import datetime, timezone
from typing import List, Optional

from domain.document import Document, DocumentMetadata
from infrastructure.database.models import PostModel
from infrastructure.database.repositories.base import (
    AsyncBaseRepository,
    BaseRepository,
)
from services.interfaces.database import IPostRepository
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class PostRepository(BaseRepository[PostModel]):
    def __init__(self, session: Session):
        super().__init__(PostModel, session)

    def get_by_channel_and_message(
        self, channel_id: int, message_id: int
    ) -> Optional[PostModel]:
        stmt = select(PostModel).where(
            and_(PostModel.channel_id == channel_id, PostModel.message_id == message_id)
        )
        return self._session.scalars(stmt).first()

    def get_by_channel(
        self, channel_id: int, skip: int = 0, limit: int = 100
    ) -> List[PostModel]:
        stmt = (
            select(PostModel)
            .where(PostModel.channel_id == channel_id)
            .order_by(PostModel.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        channel_ids: List[int] = None,
    ) -> List[PostModel]:
        conditions = [
            PostModel.published_at >= start_date,
            PostModel.published_at <= end_date,
        ]

        if channel_ids:
            conditions.append(PostModel.channel_id.in_(channel_ids))

        stmt = (
            select(PostModel)
            .where(and_(*conditions))
            .order_by(PostModel.published_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def exists(self, channel_id: int, message_id: int) -> bool:
        return self.get_by_channel_and_message(channel_id, message_id) is not None

    def bulk_create(self, posts: List[PostModel]) -> List[PostModel]:
        self._session.add_all(posts)
        self._session.commit()
        return posts

    def delete_by_channel(self, channel_id: int) -> int:
        posts = self.get_by_channel(channel_id, limit=10000)
        count = len(posts)
        for post in posts:
            self._session.delete(post)
        self._session.commit()
        return count


class AsyncPostRepository(AsyncBaseRepository[PostModel], IPostRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(PostModel, session)

    def _to_domain(self, model: PostModel, channel_username: str = "") -> Document:
        return Document(
            id=str(model.id),
            content=model.content,
            metadata=DocumentMetadata(
                source="telegram",
                channel=channel_username,
                channel_id=model.channel_id,
                message_id=model.message_id,
                date=model.published_at,
                url=model.url,
                views=model.views,
            ),
        )

    def _to_model(self, document: Document, channel_id: int) -> PostModel:
        # Преобразуем datetime в naive datetime (PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
        published_at = document.metadata.date
        if published_at:
            if published_at.tzinfo is not None:
                # Если datetime aware (с timezone), преобразуем в UTC и убираем timezone
                published_at = published_at.astimezone(timezone.utc).replace(tzinfo=None)
            # Если уже naive - оставляем как есть
        
        return PostModel(
            channel_id=channel_id,
            message_id=document.metadata.message_id or 0,
            content=document.content,
            url=document.metadata.url,
            views=document.metadata.views,
            published_at=published_at,
        )

    async def get_by_id(self, post_id: int) -> Optional[Document]:
        model = await super().get_by_id(post_id)
        return self._to_domain(model) if model else None

    async def get_by_channel_and_message(
        self, channel_id: int, message_id: int
    ) -> Optional[Document]:
        stmt = select(PostModel).where(
            and_(PostModel.channel_id == channel_id, PostModel.message_id == message_id)
        )
        result = await self._session.scalars(stmt)
        model = result.first()
        return self._to_domain(model) if model else None

    async def get_by_channel(
        self, channel_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        stmt = (
            select(PostModel)
            .where(PostModel.channel_id == channel_id)
            .order_by(PostModel.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result.all()]

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        channel_ids: Optional[List[int]] = None,
    ) -> List[Document]:
        conditions = [
            PostModel.published_at >= start_date,
            PostModel.published_at <= end_date,
        ]

        if channel_ids:
            conditions.append(PostModel.channel_id.in_(channel_ids))

        stmt = (
            select(PostModel)
            .where(and_(*conditions))
            .order_by(PostModel.published_at.desc())
        )
        result = await self._session.scalars(stmt)
        return [self._to_domain(m) for m in result.all()]

    async def exists(self, channel_id: int, message_id: int) -> bool:
        stmt = (
            select(PostModel.id)
            .where(
                and_(
                    PostModel.channel_id == channel_id,
                    PostModel.message_id == message_id,
                )
            )
            .limit(1)
        )
        result = await self._session.scalars(stmt)
        return result.first() is not None

    async def create(self, document: Document, channel_id: int) -> Document:
        model = self._to_model(document, channel_id)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def bulk_create(
        self, documents: List[Document], channel_id: int
    ) -> List[Document]:
        models = [self._to_model(doc, channel_id) for doc in documents]
        self._session.add_all(models)
        await self._session.commit()
        return [self._to_domain(m) for m in models]

    async def delete_by_channel(self, channel_id: int) -> int:
        stmt = select(PostModel).where(PostModel.channel_id == channel_id)
        result = await self._session.scalars(stmt)
        models = list(result.all())
        count = len(models)
        for model in models:
            await self._session.delete(model)
        await self._session.commit()
        return count
