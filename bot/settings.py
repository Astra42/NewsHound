import os

from dotenv import load_dotenv

load_dotenv()


def get_bot_token():
    return os.getenv("BOT_TOKEN")


def get_backend_url():
    """
    Получить URL backend API.

    В Docker контейнере использует имя сервиса 'backend' из docker-compose.
    """
    # Проверяем переменную окружения (может быть задана явно)
    backend_url = os.getenv("BACKEND_API_URL")
    return backend_url
