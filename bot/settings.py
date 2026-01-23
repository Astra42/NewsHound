import os

from dotenv import load_dotenv

load_dotenv()


def get_bot_token():
    """
    Получить токен Telegram бота.
    
    Raises:
        ValueError: если токен не установлен
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError(
            "BOT_TOKEN не установлен! "
            "Установите переменную окружения BOT_TOKEN в .env файле или в окружении. "
            "Получить токен можно у @BotFather в Telegram."
        )
    return token


def get_backend_url():
    """
    Получить URL backend API.

    В Docker контейнере использует имя сервиса 'backend' из docker-compose.
    При локальной разработке использует 'localhost'.
    """
    # Проверяем переменную окружения (может быть задана явно)
    backend_url = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL")

    if backend_url:
        return backend_url

    # Определяем окружение: Docker или локальное
    # В Docker контейнере обычно есть /app или другие маркеры
    is_docker = (
        os.path.exists("/app")
        or os.path.exists("/.dockerenv")
        or os.getenv("DOCKER_CONTAINER") == "true"
    )

    if is_docker:
        # В Docker используем имя сервиса из docker-compose
        return "http://backend:8000"
    else:
        # Локально используем localhost
        return "http://localhost:8000"
