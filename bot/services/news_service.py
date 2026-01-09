"""Сервис для работы с новостями."""

from datetime import datetime, timedelta

import httpx
from infrastructure.api_client import IBackendClient
from utils.logger import get_logger

logger = get_logger(__name__)


class NewsService:
    """Сервис для получения новостей."""

    def __init__(self, client: IBackendClient):
        self._client = client

    async def get_summary(self, user_id: int, days: int = 7) -> str:
        """Получить саммари новостей за период."""
        logger.info(f"Запрос саммари для user_id={user_id}, период: {days} дней")
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            summary_data = await self._client.get_summary(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )

            summary_text = summary_data.get("summary", "Пустой ответ от сервера")
            posts_processed = summary_data.get("posts_processed", 0)
            period = summary_data.get("period", "")
            processing_time = summary_data.get("processing_time", 0)

            if posts_processed == 0:
                logger.info(
                    f"Саммари для user_id={user_id}: новостей не найдено за период {period}"
                )
                return f"📰 За период {period} не найдено новостей."

            logger.info(
                f"Саммари для user_id={user_id}: обработано {posts_processed} постов, "
                f"время обработки: {processing_time:.2f}s"
            )
            return summary_text

        except httpx.ConnectError as e:
            logger.error(
                f"Ошибка подключения при получении саммари для user_id={user_id}: {e}"
            )
            return (
                "❌ Не удалось подключиться к серверу \n"
                "Пожалуйста, убедитесь, что сервис запущен на порту 8000."
            )
        except httpx.TimeoutException as e:
            logger.warning(f"Таймаут при получении саммари для user_id={user_id}: {e}")
            return (
                "⏱️ Время ожидания ответа истекло.\n"
                "Сервер обрабатывает слишком много данных или недоступен."
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP ошибка при получении саммари для user_id={user_id}: {e.response.status_code}"
            )
            error_data = e.response.json()
            detail = error_data.get("detail", {})
            message = detail.get("message", f"Ошибка сервера: {e.response.status_code}")
            return f"❌ {message}"
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при получении саммари для user_id={user_id}: {e}"
            )
            return f"❌ Ошибка при получении новостей: {str(e)}"

    async def get_completion(self, user_id: int, question: str) -> str:
        """Получить ответ на вопрос (RAG)."""
        logger.info(
            f"Запрос completion для user_id={user_id}, вопрос: '{question[:50]}...'"
        )
        try:
            completion_data = await self._client.get_completion(
                user_id=user_id, question=question
            )

            answer = completion_data.get("answer", "Не удалось получить ответ")
            sources = completion_data.get("sources", [])
            processing_time = completion_data.get("processing_time", 0)

            if sources:
                answer += "\n\n📚 Источники:"
                for i, source in enumerate(sources[:3], 1):
                    channel = source.get("channel", "unknown")
                    url = source.get("url", "")
                    if url:
                        answer += f"\n{i}. {channel}: {url}"

            logger.info(
                f"Completion для user_id={user_id}: {len(sources)} источников, "
                f"время обработки: {processing_time:.2f}s"
            )
            return answer

        except httpx.ConnectError as e:
            logger.error(
                f"Ошибка подключения при получении completion для user_id={user_id}: {e}"
            )
            return (
                "❌ Не удалось подключиться к серверу \n"
                "Пожалуйста, убедитесь, что сервис запущен."
            )
        except httpx.TimeoutException as e:
            logger.warning(
                f"Таймаут при получении completion для user_id={user_id}: {e}"
            )
            return (
                "⏱️ Время ожидания ответа истекло.\n"
                "Сервер обрабатывает слишком много данных или недоступен."
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP ошибка при получении completion для user_id={user_id}: {e.response.status_code}"
            )
            error_data = e.response.json()
            detail = error_data.get("detail", {})
            message = detail.get("message", f"Ошибка сервера: {e.response.status_code}")
            return f"❌ {message}"
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при получении completion для user_id={user_id}: {e}"
            )
            return f"❌ Ошибка при получении ответа: {str(e)}"
