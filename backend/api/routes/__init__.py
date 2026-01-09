"""
FastAPI роутеры.
"""

from api.routes.channels import router as channels_router
from api.routes.completion import router as completion_router
from api.routes.health import router as health_router
from api.routes.summary import router as summary_router
from fastapi import APIRouter

# Главный роутер API
router = APIRouter(prefix="/api")

# Подключаем роутеры
router.include_router(health_router, tags=["Health"])
router.include_router(completion_router, tags=["Completion"])
router.include_router(summary_router, tags=["Summary"])
router.include_router(channels_router, tags=["Channels"])
