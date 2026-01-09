"""
HuggingFace Embeddings реализация.

Принцип SOLID:
- Single Responsibility: только создание эмбеддингов
- Liskov Substitution: можно заменить на другую реализацию IEmbeddingService
"""

import asyncio
from functools import lru_cache
from typing import List, Optional

from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.core.config import settings
from backend.services.interfaces.embeddings import IEmbeddingService


class HuggingFaceEmbeddingService(IEmbeddingService):
    """
    Реализация сервиса эмбеддингов с использованием HuggingFace.

    Использует sentence-transformers для создания векторных представлений.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
    ):
        """
        Инициализация сервиса эмбеддингов.

        Args:
            model_name: название модели HuggingFace
            device: устройство для вычислений (cpu/cuda)
            normalize_embeddings: нормализовать ли эмбеддинги
        """
        self._model_name = model_name or settings.embedding_model
        self._device = device or settings.embedding_device
        self._normalize = normalize_embeddings

        self._embeddings = HuggingFaceEmbeddings(
            model_name=self._model_name,
            model_kwargs={"device": self._device},
            encode_kwargs={"normalize_embeddings": self._normalize},
        )

        # Определяем размер вектора
        self._vector_size = len(self._embeddings.embed_query("test"))

    @property
    def vector_size(self) -> int:
        """Размерность вектора эмбеддинга."""
        return self._vector_size

    @property
    def model_name(self) -> str:
        """Название модели эмбеддингов."""
        return self._model_name

    def embed_query(self, text: str) -> List[float]:
        """
        Создание эмбеддинга для поискового запроса.

        Args:
            text: текст запроса

        Returns:
            вектор эмбеддинга
        """
        return self._embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создание эмбеддингов для списка документов.

        Args:
            texts: список текстов

        Returns:
            список векторов эмбеддингов
        """
        return self._embeddings.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """
        Асинхронное создание эмбеддинга для запроса.

        Использует run_in_executor для запуска синхронного кода.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Асинхронное создание эмбеддингов для документов.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)


@lru_cache(maxsize=1)
def get_embedding_service() -> HuggingFaceEmbeddingService:
    """
    Получение singleton экземпляра сервиса эмбеддингов.

    Использует lru_cache для кэширования (модель загружается один раз).
    """
    return HuggingFaceEmbeddingService()
