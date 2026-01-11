"""
SQLAlchemy models для PostgreSQL.

Таблицы:
- users: пользователи бота
- channels: отслеживаемые каналы
- posts: проиндексированные посты
- user_channels: связь many-to-many пользователей и каналов
"""

from datetime import datetime, timezone
from typing import List, Optional

from infrastructure.database.connection import Base
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Many-to-many связь пользователей и каналов
user_channels = Table(
    "user_channels",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "channel_id",
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class UserModel(Base):
    """Модель пользователя Telegram."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow
    )

    # Relationships
    channels: Mapped[List["ChannelModel"]] = relationship(
        "ChannelModel",
        secondary=user_channels,
        back_populates="users",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class ChannelModel(Base):
    """Модель Telegram-канала."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, unique=True, nullable=True
    )
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # active, paused, indexing, error
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    last_post_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow
    )

    # Relationships
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        secondary=user_channels,
        back_populates="channels",
    )
    posts: Mapped[List["PostModel"]] = relationship(
        "PostModel",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (Index("idx_channel_status", "status"),)

    def __repr__(self) -> str:
        return (
            f"<Channel(id={self.id}, username={self.username}, status={self.status})>"
        )


class PostModel(Base):
    """Модель поста из канала."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # ID в Qdrant

    # Relationships
    channel: Mapped["ChannelModel"] = relationship(
        "ChannelModel", back_populates="posts"
    )

    # Indexes & Constraints
    __table_args__ = (
        Index("idx_post_channel_message", "channel_id", "message_id", unique=True),
        Index("idx_post_published", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, channel_id={self.channel_id}, message_id={self.message_id})>"
