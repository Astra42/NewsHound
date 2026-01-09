"""
Completion (RAG) endpoints.
"""

from api.dependencies import get_completion_service
from api.schemas.common import ErrorResponseSchema
from api.schemas.completion import (
    CompletionRequestSchema,
    CompletionResponseSchema,
)
from core.exceptions import LLMException, RetrievalException
from domain.completion import CompletionRequest
from fastapi import APIRouter, Depends, HTTPException, status
from services.completion_service import CompletionService

router = APIRouter()


@router.post(
    "/completion",
    response_model=CompletionResponseSchema,
    responses={
        500: {"model": ErrorResponseSchema, "description": "Ошибка сервера"},
        503: {"model": ErrorResponseSchema, "description": "Сервис недоступен"},
    },
    summary="Генерация ответа (RAG)",
    description="Получить AI-ответ на вопрос на основе собранных новостей",
)
async def create_completion(
    request: CompletionRequestSchema,
    service: CompletionService = Depends(get_completion_service),
) -> CompletionResponseSchema:
    """
    Генерация ответа на вопрос пользователя с использованием RAG.

    Процесс:
    1. Преобразование вопроса в эмбеддинг
    2. Поиск релевантных документов в Qdrant
    3. Формирование контекста
    4. Генерация ответа через LLM
    5. Возврат ответа с источниками

    Args:
        request: запрос с вопросом пользователя

    Returns:
        ответ с источниками информации
    """
    try:
        # Преобразуем схему запроса в доменную модель
        domain_request = CompletionRequest(
            user_id=request.user_id,
            question=request.question,
            top_k=request.top_k,
            channels=request.channels,
        )

        # Вызываем сервис
        response = await service.acomplete(domain_request)

        # Возвращаем ответ
        return CompletionResponseSchema(
            answer=response.answer,
            sources=[
                {
                    "channel": s.channel,
                    "date": s.date,
                    "post_id": s.post_id,
                    "url": s.url,
                    "relevance_score": s.relevance_score,
                }
                for s in response.sources
            ],
            processing_time=response.processing_time,
        )

    except LLMException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "LLMError",
                "message": str(e),
            },
        )
    except RetrievalException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RetrievalError",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "message": f"Внутренняя ошибка: {type(e).__name__}",
            },
        )
