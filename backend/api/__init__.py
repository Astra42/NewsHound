"""
API Layer - FastAPI роутеры и схемы.

Принцип SOLID:
- Single Responsibility: только HTTP-интерфейс
- Dependency Inversion: зависит от сервисов через DI
"""

from api.routes import router

__all__ = ["router"]
