"""Базовый репозиторий для работы с PostgreSQL."""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.infrastructure.database.connection import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: Session):
        self._model = model
        self._session = session

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self._session.get(self._model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self._model).offset(skip).limit(limit)
        return list(self._session.scalars(stmt).all())

    def create(self, obj: ModelType) -> ModelType:
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self._session.delete(obj)
        self._session.commit()

    def delete_by_id(self, id: int) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.delete(obj)
            return True
        return False


class AsyncBaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        return await self._session.get(self._model, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self._model).offset(skip).limit(limit)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(self, obj: ModelType) -> ModelType:
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        await self._session.commit()
        await self._session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self._session.delete(obj)
        await self._session.commit()

    async def delete_by_id(self, id: int) -> bool:
        obj = await self.get_by_id(id)
        if obj:
            await self.delete(obj)
            return True
        return False
