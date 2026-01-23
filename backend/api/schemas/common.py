"""
Общие схемы для API.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorResponseSchema(BaseModel):
    """Схема ошибки."""

    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Описание ошибки")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Дополнительные детали"
    )


class HealthResponseSchema(BaseModel):
    """Схема ответа health check."""

    status: str = Field(..., description="Статус сервиса")
    version: str = Field(default="1.0.0", description="Версия API")
    vectorstore_status: Optional[str] = Field(
        default=None, description="Статус векторного хранилища"
    )
    documents_count: Optional[int] = Field(
        default=None, description="Количество документов"
    )


class SuccessResponseSchema(BaseModel):
    """Схема успешного ответа."""

    success: bool = Field(default=True)
    message: str = Field(..., description="Сообщение")
