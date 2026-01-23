"""Dependency Injection для FastAPI."""

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends
from infrastructure.database.connection import AsyncSessionLocal
from infrastructure.database.repositories.channel_repository import (
    AsyncChannelRepository,
)
from infrastructure.database.repositories.post_repository import (
    AsyncPostRepository,
)
from infrastructure.database.repositories.user_repository import (
    AsyncUserRepository,
)
from infrastructure.embeddings.huggingface_embeddings import (
    HuggingFaceEmbeddingService,
)
from infrastructure.llm.mistral_llm import MistralLLMService
from infrastructure.telegram.telethon_parser import TelethonChannelParser
from infrastructure.vectorstore.qdrant_store import QdrantVectorStoreRepository
from services.channel_service import ChannelService
from services.completion_service import CompletionService
from services.evaluation_service import EvaluationService
from services.interfaces.database import (
    IChannelRepository,
    IPostRepository,
)
from services.interfaces.embeddings import IEmbeddingService
from services.interfaces.llm import ILLMService
from services.interfaces.vectorstore import IVectorStoreRepository
from services.retrieval_service import RetrievalService
from services.summary_service import SummaryService
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@lru_cache(maxsize=1)
def get_embedding_service() -> IEmbeddingService:
    return HuggingFaceEmbeddingService()


@lru_cache(maxsize=1)
def get_llm_service() -> ILLMService:
    return MistralLLMService()


@lru_cache(maxsize=1)
def get_vectorstore_repository() -> IVectorStoreRepository:
    embedding_service = get_embedding_service()
    return QdrantVectorStoreRepository(embedding_service=embedding_service)


@lru_cache(maxsize=1)
def get_channel_parser() -> TelethonChannelParser:
    return TelethonChannelParser()


def get_channel_repository(
    db: AsyncSession = Depends(get_db),
) -> AsyncChannelRepository:
    return AsyncChannelRepository(db)


def get_post_repository(
    db: AsyncSession = Depends(get_db),
) -> AsyncPostRepository:
    return AsyncPostRepository(db)


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> AsyncUserRepository:
    return AsyncUserRepository(db)


def get_retrieval_service() -> RetrievalService:
    vectorstore = get_vectorstore_repository()
    return RetrievalService(vectorstore_repository=vectorstore)


def get_completion_service() -> CompletionService:
    llm = get_llm_service()
    retrieval = get_retrieval_service()
    return CompletionService(llm_service=llm, retrieval_service=retrieval)


def get_evaluation_service() -> EvaluationService:
    llm = get_llm_service()
    retrieval = get_retrieval_service()
    return EvaluationService(llm_service=llm, retrieval_service=retrieval)


def get_summary_service() -> SummaryService:
    llm = get_llm_service()
    vectorstore = get_vectorstore_repository()
    return SummaryService(llm_service=llm, vectorstore_repository=vectorstore)


def get_channel_service(
    channel_repository: IChannelRepository = Depends(get_channel_repository),
    post_repository: IPostRepository = Depends(get_post_repository),
) -> ChannelService:
    parser = get_channel_parser()
    vectorstore = get_vectorstore_repository()
    return ChannelService(
        channel_parser=parser,
        vectorstore_repository=vectorstore,
        channel_repository=channel_repository,
        post_repository=post_repository,
    )


async def startup_services():
    _ = get_embedding_service()
    vectorstore = get_vectorstore_repository()
    vectorstore.create_collection()


async def shutdown_services():
    try:
        parser = get_channel_parser()
        if parser.is_connected:
            await parser.disconnect()
    except Exception:
        pass

    get_embedding_service.cache_clear()
    get_llm_service.cache_clear()
    get_vectorstore_repository.cache_clear()
    get_channel_parser.cache_clear()
