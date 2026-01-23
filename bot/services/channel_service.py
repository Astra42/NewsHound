"""Сервис для работы с каналами."""

import re

import httpx
from infrastructure.api_client import IBackendClient
from utils.logger import get_logger

logger = get_logger(__name__)


def escape_markdown_v2(text: str) -> str:
    """
    Экранировать специальные символы для Telegram Markdown V2.

    Args:
        text: текст для экранирования

    Returns:
        экранированный текст
    """
    # Символы, которые нужно экранировать в Markdown V2
    special_chars = r"_*[]()~`>#+-=|{}.!"
    # Экранируем каждый специальный символ
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


class ChannelService:
    """Сервис для управления каналами."""

    def __init__(self, client: IBackendClient):
        self._client = client

    async def list_channels(self) -> str:
        """Получить форматированный список каналов."""
        logger.info("Запрос списка каналов")
        try:
            channels = await self._client.get_channels()

            if not channels:
                logger.info("Список каналов пуст")
                return "📋 Подключенных каналов пока нет."

            message = "📋 *Подключенные новостные каналы:*\n\n"
            for i, channel in enumerate(channels, 1):
                username = channel.get("username") or "unknown"
                title = channel.get("title") or username
                posts_count = channel.get("posts_count", 0)

                # Экранируем специальные символы Markdown в данных канала
                # Преобразуем в строку и убираем None значения
                escaped_title = escape_markdown_v2(str(title) if title else "unknown")
                escaped_username = escape_markdown_v2(
                    str(username) if username else "unknown"
                )

                message += f"{i}\\. {escaped_title} \\(@{escaped_username}\\) \\- {posts_count} постов\n"

            message += f"\n📊 Всего каналов: {len(channels)}"
            logger.info(f"Список каналов сформирован: {len(channels)} каналов")
            return message

        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(f"Ошибка соединения с backend: {e}")
            return "⚠️ Не удалось связаться с сервером новостей или соединение было разорвано.\nУбедитесь, что backend запущен."
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP ошибка при получении списка каналов: {e.response.status_code}"
            )
            if e.response.status_code == 404:
                return "⚠️ Сервис недоступен."
            return f"❌ Ошибка сервера: {e.response.status_code}"
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении списка каналов: {e}")
            return "⚠️ Произошла ошибка при получении списка каналов."

    async def add_channel(self, channel_link: str) -> str:
        """Добавить канал."""
        logger.info(f"Добавление канала: {channel_link}")
        try:
            channel = await self._client.add_channel(channel_link, index_posts=True)

            username = channel.get("username", "unknown")
            title = channel.get("title", username)
            posts_count = channel.get("posts_count", 0)

            logger.info(
                f"Канал '{channel_link}' успешно добавлен: @{username}, {posts_count} постов"
            )
            return (
                f"✅ Канал {title} (@{username}) успешно добавлен!\n"
                f"📊 Проиндексировано постов: {posts_count}"
            )

        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(
                f"Ошибка соединения при добавлении канала '{channel_link}': {e}"
            )
            return "❌ Не удалось подключиться к серверу или соединение было разорвано."
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"HTTP ошибка при добавлении канала '{channel_link}': {e.response.status_code}"
            )
            if e.response.status_code == 409:
                error_data = e.response.json()
                detail = error_data.get("detail", {})
                message = detail.get("message", "Канал уже существует")
                logger.info(f"Канал '{channel_link}' уже существует")
                return f"⚠️ {message}"
            elif e.response.status_code == 400:
                error_data = e.response.json()
                detail = error_data.get("detail", {})
                message = detail.get("message", "Неверная ссылка на канал")
                logger.warning(f"Неверная ссылка на канал '{channel_link}': {message}")
                return f"❌ {message}"
            elif e.response.status_code == 503:
                error_data = e.response.json()
                detail = error_data.get("detail", {})
                message = detail.get("message", "Ошибка Telegram API")
                logger.error(
                    f"Ошибка Telegram API при добавлении канала '{channel_link}': {message}"
                )
                # Если сообщение содержит информацию о сессии, делаем его более понятным
                if "сессия" in message.lower() or "session" in message.lower():
                    return (
                        f"❌ {message}\n\n"
                        f"💡 Решение: Удалите файл сессии Telegram (обычно в папке sessions/) "
                        f"и перезапустите backend для переавторизации."
                    )
                return f"❌ {message}"
            return f"❌ Ошибка сервера: {e.response.status_code}"
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при добавлении канала '{channel_link}': {e}"
            )
            return f"❌ Произошла ошибка при добавлении канала: {str(e)}"

    async def remove_channel(self, channel_username: str) -> str:
        """Удалить канал."""
        logger.info(f"Удаление канала: {channel_username}")
        try:
            result = await self._client.remove_channel(channel_username)
            message = result.get("message", "Канал успешно удалён")
            logger.info(f"Канал '{channel_username}' успешно удален")
            return f"✅ {message}"

        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(
                f"Ошибка соединения при удалении канала '{channel_username}': {e}"
            )
            return "❌ Не удалось подключиться к серверу или соединение было разорвано.\nПожалуйста, убедитесь, что сервис запущен и попробуйте позже."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Канал '{channel_username}' не найден")
                return "❌ Канал не найден. Проверьте правильность названия канала."
            logger.error(
                f"HTTP ошибка при удалении канала '{channel_username}': {e.response.status_code}"
            )
            return f"❌ Ошибка сервера: {e.response.status_code}"
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при удалении канала '{channel_username}': {e}"
            )
            return f"❌ Произошла ошибка при удалении канала: {str(e)}"
