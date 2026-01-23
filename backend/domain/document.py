"""
Доменные модели для документов.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Метаданные документа."""

    source: str = Field(default="telegram", description="Источник документа")
    channel: str = Field(default="", description="Канал-источник")
    channel_id: Optional[int] = Field(default=None, description="ID канала")
    message_id: Optional[int] = Field(default=None, description="ID сообщения")
    date: Optional[datetime] = Field(default=None, description="Дата публикации")
    url: Optional[str] = Field(default=None, description="Ссылка на пост")
    views: Optional[int] = Field(default=None, description="Количество просмотров")

    class Config:
        extra = "allow"  # Разрешаем дополнительные поля


class Document(BaseModel):
    """Модель документа для индексации и поиска."""

    id: Optional[str] = Field(default=None, description="Уникальный ID документа")
    content: str = Field(..., description="Текстовое содержимое")
    metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata, description="Метаданные документа"
    )
    embedding: Optional[List[float]] = Field(
        default=None, description="Векторное представление (эмбеддинг)"
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Создание документа из словаря."""
        content = data.get("content", data.get("text", ""))
        metadata_dict = data.get("metadata", {})

        # Если metadata не словарь, создаём пустой
        if not isinstance(metadata_dict, dict):
            metadata_dict = {}

        return cls(
            id=data.get("id"),
            content=content,
            metadata=DocumentMetadata(**metadata_dict),
            embedding=data.get("embedding"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для хранения."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.model_dump(),
            "embedding": self.embedding,
        }


class SearchResult(BaseModel):
    """Результат поиска документа."""

    document: Document = Field(..., description="Найденный документ")
    score: float = Field(..., description="Оценка релевантности (0-1)")

    @property
    def content(self) -> str:
        """Сокращённый доступ к контенту."""
        return self.document.content

    @property
    def metadata(self) -> DocumentMetadata:
        """Сокращённый доступ к метаданным."""
        return self.document.metadata
