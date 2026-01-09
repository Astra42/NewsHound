"""
Database repositories - слой доступа к данным PostgreSQL.

Принцип SOLID:
- Liskov Substitution: репозитории реализуют интерфейсы из services/interfaces/
- Single Responsibility: каждый репозиторий работает с одной сущностью
"""

from backend.infrastructure.database.repositories.channel_repository import (
    ChannelRepository,
    AsyncChannelRepository,
)
from backend.infrastructure.database.repositories.user_repository import (
    UserRepository,
    AsyncUserRepository,
)
from backend.infrastructure.database.repositories.post_repository import (
    PostRepository,
    AsyncPostRepository,
)

__all__ = [
    # Синхронные
    "ChannelRepository",
    "UserRepository",
    "PostRepository",
    # Асинхронные (основные)
    "AsyncChannelRepository",
    "AsyncUserRepository",
    "AsyncPostRepository",
]
