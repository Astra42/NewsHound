import uuid
from typing import Any, Dict, List

# Импорт конфигурации
import config as cfg
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class VectorStore:
    """Класс для работы с Qdrant векторным хранилищем."""

    def __init__(self, host: str = None, port: int = None, collection_name: str = None):
        host = host or cfg.QDRANT_HOST
        port = port or cfg.QDRANT_PORT
        collection_name = collection_name or cfg.QDRANT_COLLECTION
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None
        self.embeddings = None
        self.vector_size = None

        self._connect()
        self._init_embeddings()

    def _connect(self):
        """Подключение к Qdrant."""
        print(f"Подключение к Qdrant: {self.host}:{self.port}")
        self.client = QdrantClient(host=self.host, port=self.port)
        print("Подключено к Qdrant")

    def _init_embeddings(self):
        """Инициализация модели эмбеддингов."""
        print(f"Загрузка модели эмбеддингов: {cfg.EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=cfg.EMBEDDING_MODEL,
            model_kwargs={"device": cfg.EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
        # Определяем размер вектора
        test_embedding = self.embeddings.embed_query("test")
        self.vector_size = len(test_embedding)
        print(f"Размер вектора: {self.vector_size}")

    def create_collection(self, recreate: bool = False):
        """Создание коллекции."""
        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name in collections:
            if recreate:
                print(f"Удаление существующей коллекции: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            else:
                print(f"Коллекция {self.collection_name} уже существует")
                return

        print(f"Создание коллекции: {self.collection_name}")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size, distance=Distance.COSINE
            ),
        )
        print("Коллекция создана")

    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """
        Добавление документов в коллекцию.

        Args:
            documents: список документов в формате {"content": str, "metadata": dict}
            batch_size: размер батча для загрузки
        """
        self.create_collection()

        print(f"Добавление {len(documents)} документов...")

        points = []
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Создаем эмбеддинг
            embedding = self.embeddings.embed_query(content)

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"content": content, **metadata},
            )
            points.append(point)

            # Загружаем батчами
            if len(points) >= batch_size:
                self.client.upsert(collection_name=self.collection_name, points=points)
                print(f"  Загружено {i + 1}/{len(documents)} документов")
                points = []

        # Загружаем остаток
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

        print(f"Загружено {len(documents)} документов")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск похожих документов.

        Args:
            query: поисковый запрос
            k: количество результатов

        Returns:
            список документов с контентом и метаданными
        """
        query_embedding = self.embeddings.embed_query(query)

        # Используем query_points вместо search (API изменился в qdrant-client >= 1.16.0)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=k,
            with_payload=True,
            with_vectors=False,
        )

        documents = []
        for hit in results.points:
            documents.append(
                {
                    "content": hit.payload.get("content", "") if hit.payload else "",
                    "metadata": {
                        key: val
                        for key, val in (hit.payload.items() if hit.payload else {})
                        if key != "content"
                    },
                    "score": hit.score,
                }
            )

        return documents

    def get_collection_info(self) -> Dict[str, Any]:
        """Информация о коллекции."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_collection(self):
        """Удаление коллекции."""
        self.client.delete_collection(self.collection_name)
        print(f"Коллекция {self.collection_name} удалена")


# Удобные функции для использования из notebook


def init_vectorstore() -> VectorStore:
    """Инициализация векторного хранилища."""
    return VectorStore()


def index_documents(
    documents: List[Dict[str, Any]], recreate: bool = False
) -> VectorStore:
    """
    Индексация документов в Qdrant.

    Args:
        documents: список документов {"content": str, "metadata": dict}
        recreate: пересоздать коллекцию

    Returns:
        VectorStore instance
    """
    vs = VectorStore()
    if recreate:
        vs.create_collection(recreate=True)
    vs.add_documents(documents)
    return vs


def search_documents(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Поиск документов."""
    vs = VectorStore()
    return vs.search(query, k)
