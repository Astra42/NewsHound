"""
Infrastructure Layer - реализации внешних сервисов.

Принцип SOLID:
- Dependency Inversion: реализации зависят от интерфейсов
- Open/Closed: легко добавить новые реализации (OpenAI, другие VectorDB)
"""

from infrastructure.database.connection import get_async_db, get_db, init_db
from infrastructure.database.models import ChannelModel, PostModel, UserModel
from infrastructure.embeddings.huggingface_embeddings import HuggingFaceEmbeddingService
from infrastructure.llm.mistral_llm import MistralLLMService
from infrastructure.telegram.telethon_parser import TelethonChannelParser
from infrastructure.vectorstore.qdrant_store import QdrantVectorStoreRepository

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
