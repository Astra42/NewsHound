"""
Интерфейсы (абстрактные классы) для сервисов.

Принципы SOLID:
- Interface Segregation: маленькие специфичные интерфейсы
- Dependency Inversion: зависимость от абстракций, не от реализаций
"""

from services.interfaces.channel_parser import IChannelParser
from services.interfaces.database import (
    IChannelRepository,
    IPostRepository,
    IUserRepository,
)
from services.interfaces.embeddings import IEmbeddingService
from services.interfaces.llm import ILLMService
from services.interfaces.vectorstore import IVectorStoreRepository

__all__ = [
    "ILLMService",
    "IEmbeddingService",
    "IVectorStoreRepository",
    "IChannelParser",
    "IChannelRepository",
    "IPostRepository",
    "IUserRepository",
]
