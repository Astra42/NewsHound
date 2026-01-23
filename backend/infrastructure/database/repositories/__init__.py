"""
Database repositories - слой доступа к данным PostgreSQL.

Принцип SOLID:
- Liskov Substitution: репозитории реализуют интерфейсы из services/interfaces/
- Single Responsibility: каждый репозиторий работает с одной сущностью
"""

from infrastructure.database.repositories.channel_repository import (
    AsyncChannelRepository,
    ChannelRepository,
)
from infrastructure.database.repositories.post_repository import (
    AsyncPostRepository,
    PostRepository,
)
from infrastructure.database.repositories.user_repository import (
    AsyncUserRepository,
    UserRepository,
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
