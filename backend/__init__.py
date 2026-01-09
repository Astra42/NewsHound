"""
NewsHound Backend Module.

AI-powered Telegram News Monitor - бэкенд для RAG и API.

Архитектура:
- core/           - конфигурация и базовые компоненты
- domain/         - доменные модели (сущности)
- services/       - бизнес-логика и интерфейсы
- infrastructure/ - реализации внешних сервисов
- api/            - FastAPI роутеры и схемы

Принципы:
- SOLID: Single Responsibility, Open/Closed, Liskov Substitution,
         Interface Segregation, Dependency Inversion
- Слоистая архитектура: Presentation -> Business Logic -> Data Access
"""

__version__ = "1.0.0"
__author__ = "NewsHound Team"

# Экспортируем основные компоненты для удобного импорта
from app import app, create_app
from core.config import settings

__all__ = [
    "settings",
    "app",
    "create_app",
    "__version__",
]
