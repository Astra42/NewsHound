"""
Channel management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_channel_service
from backend.api.schemas.channels import (
    AddChannelRequestSchema,
    ChannelListResponseSchema,
    ChannelResponseSchema,
)
from backend.api.schemas.common import ErrorResponseSchema, SuccessResponseSchema
from backend.core.exceptions import (
    ChannelAlreadyExistsException,
    ChannelNotFoundException,
    InvalidChannelLinkException,
    TelegramParserException,
)
from backend.services.channel_service import ChannelService

router = APIRouter(prefix="/channels")


@router.get(
    "/",
    response_model=ChannelListResponseSchema,
    summary="Список каналов",
    description="Получить список всех отслеживаемых каналов",
)
async def list_channels(
    service: ChannelService = Depends(get_channel_service),
) -> ChannelListResponseSchema:
    """
    Получение списка всех каналов.

    Returns:
        список каналов с информацией о каждом
    """
    channels = await service.get_channels()

    return ChannelListResponseSchema(
        channels=[
            ChannelResponseSchema(
                username=ch.username,
                title=ch.title,
                link=ch.link,
                status=ch.status,
                posts_count=ch.posts_count,
                last_post_date=ch.last_post_date,
                created_at=ch.created_at,
            )
            for ch in channels
        ],
        total=len(channels),
    )


@router.post(
    "/",
    response_model=ChannelResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponseSchema, "description": "Невалидная ссылка"},
        409: {"model": ErrorResponseSchema, "description": "Канал уже существует"},
        503: {"model": ErrorResponseSchema, "description": "Telegram недоступен"},
    },
    summary="Добавить канал",
    description="Добавить Telegram-канал в список мониторинга",
)
async def add_channel(
    request: AddChannelRequestSchema,
    service: ChannelService = Depends(get_channel_service),
) -> ChannelResponseSchema:
    """
    Добавление нового канала.

    Действия:
    1. Валидация ссылки на канал
    2. Получение информации о канале
    3. Парсинг исторических постов (если index_posts=True)
    4. Индексация в векторное хранилище + PostgreSQL
    5. Активация мониторинга

    Args:
        request: запрос с ссылкой на канал

    Returns:
        информация о добавленном канале
    """
    try:
        channel = await service.add_channel(
            channel_link=request.channel_link,
            index_posts=request.index_posts,
            posts_limit=request.posts_limit,
        )

        return ChannelResponseSchema(
            username=channel.username,
            title=channel.title,
            link=channel.link,
            status=channel.status,
            posts_count=channel.posts_count,
            last_post_date=channel.last_post_date,
            created_at=channel.created_at,
        )

    except ChannelAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "ChannelExists",
                "message": str(e),
            },
        )
    except InvalidChannelLinkException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidLink",
                "message": str(e),
            },
        )
    except TelegramParserException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "TelegramError",
                "message": str(e),
            },
        )


@router.delete(
    "/{channel_username}",
    response_model=SuccessResponseSchema,
    responses={
        404: {"model": ErrorResponseSchema, "description": "Канал не найден"},
    },
    summary="Удалить канал",
    description="Удалить канал из мониторинга",
)
async def remove_channel(
    channel_username: str,
    service: ChannelService = Depends(get_channel_service),
) -> SuccessResponseSchema:
    """
    Удаление канала.

    Действия:
    1. Удаление из PostgreSQL (каскадно с постами)
    2. Удаление векторных эмбеддингов из Qdrant

    Args:
        channel_username: username канала (без @)

    Returns:
        статус операции
    """
    try:
        await service.remove_channel(channel_username)

        return SuccessResponseSchema(
            success=True,
            message=f"Канал @{channel_username} успешно удалён",
        )

    except ChannelNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ChannelNotFound",
                "message": str(e),
            },
        )


@router.post(
    "/{channel_username}/refresh",
    response_model=SuccessResponseSchema,
    responses={
        404: {"model": ErrorResponseSchema, "description": "Канал не найден"},
    },
    summary="Обновить канал",
    description="Обновить посты канала (индексировать новые)",
)
async def refresh_channel(
    channel_username: str,
    posts_limit: int = 50,
    service: ChannelService = Depends(get_channel_service),
) -> SuccessResponseSchema:
    """
    Обновление постов канала.

    Args:
        channel_username: username канала
        posts_limit: лимит новых постов

    Returns:
        количество новых постов
    """
    try:
        new_posts = await service.refresh_channel(
            channel_link=channel_username,
            posts_limit=posts_limit,
        )

        return SuccessResponseSchema(
            success=True,
            message=f"Добавлено {new_posts} новых постов для @{channel_username}",
        )

    except ChannelNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ChannelNotFound",
                "message": str(e),
            },
        )
