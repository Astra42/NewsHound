"""
Qdrant Vector Store реализация.

Принцип SOLID:
- Single Responsibility: только работа с Qdrant
- Liskov Substitution: можно заменить на другую реализацию IVectorStoreRepository
- Dependency Inversion: зависит от IEmbeddingService
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from backend.core.config import settings
from backend.core.exceptions import (
    VectorStoreConnectionException,
)
from backend.domain.document import Document, DocumentMetadata, SearchResult
from backend.services.interfaces.embeddings import IEmbeddingService
from backend.services.interfaces.vectorstore import IVectorStoreRepository


class QdrantVectorStoreRepository(IVectorStoreRepository):
    """
    Репозиторий для работы с Qdrant векторным хранилищем.

    Attributes:
        _client: клиент Qdrant
        _collection_name: название коллекции
        _embedding_service: сервис для создания эмбеддингов
    """

    def __init__(
        self,
        embedding_service: IEmbeddingService,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Инициализация репозитория.

        Args:
            embedding_service: сервис эмбеддингов (Dependency Injection)
            host: хост Qdrant
            port: порт Qdrant
            collection_name: название коллекции
        """
        self._host = host or settings.qdrant_host
        self._port = port or settings.qdrant_port
        self._collection_name = collection_name or settings.qdrant_collection
        self._embedding_service = embedding_service

        try:
            self._client = QdrantClient(host=self._host, port=self._port)
        except Exception:
            raise VectorStoreConnectionException(self._host, self._port)

    # =========================================================================
    # CRUD операции
    # =========================================================================

    def add_documents(self, documents: List[Document], batch_size: int = 100) -> int:
        """
        Добавление документов в Qdrant.

        Args:
            documents: список документов
            batch_size: размер батча

        Returns:
            количество добавленных документов
        """
        self.create_collection()

        points = []
        for doc in documents:
            # Создаём эмбеддинг если его нет
            if doc.embedding is None:
                doc.embedding = self._embedding_service.embed_query(doc.content)

            # Генерируем ID если нет
            doc_id = doc.id or str(uuid.uuid4())

            # Подготавливаем payload
            payload = {
                "content": doc.content,
                **doc.metadata.model_dump(),
            }

            point = PointStruct(
                id=doc_id,
                vector=doc.embedding,
                payload=payload,
            )
            points.append(point)

            # Загружаем батчами
            if len(points) >= batch_size:
                self._client.upsert(
                    collection_name=self._collection_name, points=points
                )
                points = []

        # Загружаем остаток
        if points:
            self._client.upsert(collection_name=self._collection_name, points=points)

        return len(documents)

    async def aadd_documents(
        self, documents: List[Document], batch_size: int = 100
    ) -> int:
        """
        Асинхронное добавление документов.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.add_documents(documents, batch_size)
        )

    def delete_documents(
        self,
        document_ids: Optional[List[str]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Удаление документов.

        Args:
            document_ids: список ID для удаления
            filter_dict: фильтр по метаданным (например, {"channel": "rbc_news"})

        Returns:
            количество удалённых документов
        """
        if document_ids:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=document_ids,
            )
            return len(document_ids)

        if filter_dict:
            # Строим фильтр Qdrant
            conditions = [
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filter_dict.items()
            ]

            self._client.delete(
                collection_name=self._collection_name,
                points_selector=Filter(must=conditions),
            )
            return -1  # Точное количество неизвестно

        return 0

    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Получение документа по ID.
        """
        try:
            points = self._client.retrieve(
                collection_name=self._collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=True,
            )

            if not points:
                return None

            point = points[0]
            payload = point.payload or {}

            return Document(
                id=str(point.id),
                content=payload.get("content", ""),
                metadata=DocumentMetadata(
                    **{k: v for k, v in payload.items() if k != "content"}
                ),
                embedding=point.vector if hasattr(point, "vector") else None,
            )
        except Exception:
            return None

    # =========================================================================
    # Поиск
    # =========================================================================

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Семантический поиск документов.

        Args:
            query: поисковый запрос
            k: количество результатов
            filter_dict: фильтр по метаданным

        Returns:
            список результатов поиска
        """
        query_embedding = self._embedding_service.embed_query(query)
        return self.search_by_vector(query_embedding, k, filter_dict)

    async def asearch(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Асинхронный семантический поиск.
        """
        query_embedding = await self._embedding_service.aembed_query(query)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.search_by_vector(query_embedding, k, filter_dict)
        )

    def search_by_vector(
        self,
        vector: List[float],
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Поиск по вектору.
        """
        # Строим фильтр если нужен
        query_filter = None
        if filter_dict:
            conditions = [
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filter_dict.items()
            ]
            query_filter = Filter(must=conditions)

        # Выполняем поиск
        results = self._client.query_points(
            collection_name=self._collection_name,
            query=vector,
            limit=k,
            with_payload=True,
            with_vectors=False,
            query_filter=query_filter,
        )

        # Преобразуем результаты
        search_results = []
        for hit in results.points:
            payload = hit.payload or {}

            document = Document(
                id=str(hit.id),
                content=payload.get("content", ""),
                metadata=DocumentMetadata(
                    **{k: v for k, v in payload.items() if k != "content"}
                ),
            )

            search_results.append(
                SearchResult(
                    document=document,
                    score=hit.score,
                )
            )

        return search_results

    # =========================================================================
    # Управление коллекцией
    # =========================================================================

    def create_collection(self, recreate: bool = False) -> None:
        """
        Создание коллекции в Qdrant.

        Args:
            recreate: пересоздать если существует
        """
        if self.collection_exists():
            if recreate:
                self.delete_collection()
            else:
                return

        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=VectorParams(
                size=self._embedding_service.vector_size,
                distance=Distance.COSINE,
            ),
        )

    def delete_collection(self) -> None:
        """Удаление коллекции."""
        if self.collection_exists():
            self._client.delete_collection(self._collection_name)

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Информация о коллекции.
        """
        try:
            info = self._client.get_collection(self._collection_name)
            return {
                "name": self._collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception as e:
            return {"error": str(e)}

    def collection_exists(self) -> bool:
        """Проверка существования коллекции."""
        collections = [c.name for c in self._client.get_collections().collections]
        return self._collection_name in collections
