"""
Infrastructure Layer - реализации внешних сервисов.

Принцип SOLID:
- Dependency Inversion: реализации зависят от интерфейсов
- Open/Closed: легко добавить новые реализации (OpenAI, другие VectorDB)
"""

from backend.infrastructure.llm.mistral_llm import MistralLLMService
from backend.infrastructure.embeddings.huggingface_embeddings import HuggingFaceEmbeddingService
from backend.infrastructure.vectorstore.qdrant_store import QdrantVectorStoreRepository
from backend.infrastructure.telegram.telethon_parser import TelethonChannelParser
from backend.infrastructure.database.connection import get_db, get_async_db, init_db
from backend.infrastructure.database.models import UserModel, ChannelModel, PostModel

__all__ = [
    "MistralLLMService",
    "HuggingFaceEmbeddingService",
    "QdrantVectorStoreRepository",
    "TelethonChannelParser",
    "get_db",
    "get_async_db",
    "init_db",
    "UserModel",
    "ChannelModel",
    "PostModel",
]

