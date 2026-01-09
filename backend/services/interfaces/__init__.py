"""
Интерфейсы (абстрактные классы) для сервисов.

Принципы SOLID:
- Interface Segregation: маленькие специфичные интерфейсы
- Dependency Inversion: зависимость от абстракций, не от реализаций
"""

from backend.services.interfaces.llm import ILLMService
from backend.services.interfaces.embeddings import IEmbeddingService
from backend.services.interfaces.vectorstore import IVectorStoreRepository
from backend.services.interfaces.channel_parser import IChannelParser
from backend.services.interfaces.database import (
    IChannelRepository,
    IPostRepository,
    IUserRepository,
)

__all__ = [
    "ILLMService",
    "IEmbeddingService",
    "IVectorStoreRepository",
    "IChannelParser",
    "IChannelRepository",
    "IPostRepository",
    "IUserRepository",
]

