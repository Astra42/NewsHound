"""
Summary endpoints.
"""

from api.dependencies import get_summary_service
from api.schemas.common import ErrorResponseSchema
from api.schemas.summary import SummaryRequestSchema, SummaryResponseSchema
from core.exceptions import LLMException
from domain.completion import SummaryRequest
from fastapi import APIRouter, Depends, HTTPException, status
from services.summary_service import SummaryService

router = APIRouter()


@router.post(
    "/summary",
    response_model=SummaryResponseSchema,
    responses={
        500: {"model": ErrorResponseSchema, "description": "Ошибка сервера"},
        503: {"model": ErrorResponseSchema, "description": "Сервис недоступен"},
    },
    summary="Генерация саммари",
    description="Создать краткое аналитическое резюме новостей за указанный период",
)
async def create_summary(
    request: SummaryRequestSchema,
    service: SummaryService = Depends(get_summary_service),
) -> SummaryResponseSchema:
    """
    Генерация саммари новостей за период.

    Процесс:
    1. Запрос документов за период
    2. Группировка по темам
    3. Генерация саммари через LLM
    4. Формирование итогового отчёта

    Args:
        request: запрос с параметрами периода

    Returns:
        саммари с метаданными
    """
    try:
        # Преобразуем в доменную модель
        domain_request = SummaryRequest(
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            channels=request.channels,
            max_topics=request.max_topics,
        )

        # Вызываем сервис
        response = await service.agenerate_summary(domain_request)

        # Возвращаем ответ
        return SummaryResponseSchema(
            summary=response.summary,
            posts_processed=response.posts_processed,
            period=response.period,
            topics=response.topics,
            channels_included=response.channels_included,
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "message": f"Внутренняя ошибка: {type(e).__name__}",
            },
        )
