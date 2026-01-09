"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_vectorstore_repository
from backend.api.schemas.common import HealthResponseSchema
from backend.services.interfaces.vectorstore import IVectorStoreRepository

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponseSchema,
    summary="Health Check",
    description="Проверка состояния сервиса и его компонентов",
)
async def health_check(
    vectorstore: IVectorStoreRepository = Depends(get_vectorstore_repository),
) -> HealthResponseSchema:
    """
    Проверка состояния сервиса.

    Возвращает:
    - Статус сервиса
    - Статус векторного хранилища
    - Количество документов
    """
    try:
        info = vectorstore.get_collection_info()
        vectorstore_status = info.get("status", "unknown")
        documents_count = info.get("points_count", 0)
    except Exception as e:
        vectorstore_status = f"error: {str(e)}"
        documents_count = None

    return HealthResponseSchema(
        status="healthy",
        version="1.0.0",
        vectorstore_status=vectorstore_status,
        documents_count=documents_count,
    )


@router.get(
    "/",
    summary="API Info",
    description="Информация о API",
)
async def api_info():
    """Информация о API."""
    return {
        "name": "NewsHound RAG API",
        "version": "1.0.0",
        "description": "AI-powered Telegram News Monitor",
        "docs": "/docs",
    }
