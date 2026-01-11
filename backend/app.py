"""
FastAPI Application Factory.

Точка входа для приложения NewsHound RAG API.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from api.dependencies import shutdown_services, startup_services
from api.routes import router as api_router
from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.database.connection import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.

    Выполняется при старте и остановке приложения.
    """
    # Startup
    print("🚀 Запуск NewsHound Backend API...")

    # Инициализация БД
    try:
        print("📦 Инициализация PostgreSQL...")
        await init_db()
        print("✅ PostgreSQL готов")
    except Exception as e:
        print(f"⚠️ Ошибка PostgreSQL: {e}")

    # Инициализация сервисов
    try:
        await startup_services()
        print("✅ Сервисы инициализированы")
    except Exception as e:
        print(f"⚠️ Ошибка при инициализации: {e}")

    yield

    # Shutdown
    print("🛑 Остановка NewsHound Backend API...")
    await shutdown_services()
    await close_db()
    print("✅ Сервисы остановлены")


def create_app() -> FastAPI:
    """
    Фабрика для создания FastAPI приложения.

    Принцип SOLID:
    - Single Responsibility: только конфигурация приложения
    - Open/Closed: легко расширять middleware и роутеры

    Returns:
        настроенный экземпляр FastAPI
    """
    app = FastAPI(
        title="NewsHound RAG API",
        description="""
        ## AI-powered Telegram News Monitor
        
        API для интеллектуального мониторинга и анализа новостей из Telegram-каналов.
        
        ### Возможности:
        
        * 🤖 **RAG Completion** — ответы на вопросы с использованием контекста из новостей
        * 📊 **Summary** — генерация аналитических саммари за период
        * 📡 **Channels** — управление списком отслеживаемых каналов
        
        ### Технологии:
        
        * FastAPI + Pydantic
        * LangChain + Mistral AI
        * Qdrant Vector Database
        * PostgreSQL
        * Pyrogram (Telegram Parser)
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        redirect_slashes=False,  # Отключаем автоматические редиректы по слэшам
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене ограничить
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем API роутеры
    app.include_router(api_router)

    return app


# Экземпляр приложения для uvicorn
app = create_app()


if __name__ == "__main__":
    # Добавляем корень проекта в PYTHONPATH для локального запуска
    # (в Docker это не нужно, т.к. PYTHONPATH уже установлен)
    project_root = Path(__file__).parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
