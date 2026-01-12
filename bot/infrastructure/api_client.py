"""HTTP клиент для взаимодействия с backend API."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from utils.logger import get_logger

logger = get_logger(__name__)


class IBackendClient(ABC):
    """Интерфейс для клиента backend API."""

    @abstractmethod
    async def get_channels(self) -> List[Dict]:
        """Получить список каналов."""
        pass

    @abstractmethod
    async def add_channel(
        self,
        channel_link: str,
        index_posts: bool = True,
        posts_limit: Optional[int] = None,
    ) -> Dict:
        """Добавить канал."""
        pass

    @abstractmethod
    async def remove_channel(self, channel_username: str) -> Dict:
        """Удалить канал."""
        pass

    @abstractmethod
    async def get_summary(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        channels: Optional[List[str]] = None,
    ) -> Dict:
        """Получить саммари новостей."""
        pass

    @abstractmethod
    async def get_completion(
        self, user_id: int, question: str, channels: Optional[List[str]] = None
    ) -> Dict:
        """Получить ответ на вопрос (RAG)."""
        pass


class BackendClient(IBackendClient):
    """Реализация HTTP клиента для backend API."""

    def __init__(self, base_url: str, timeout: float = 60.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_channels(self) -> List[Dict]:
        """Получить список каналов."""
        url = f"{self._base_url}/api/channels/"
        logger.debug(f"GET {url}")
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(url)
                logger.debug(f"Response status: {response.status_code}, size: {len(response.content)} bytes")
                response.raise_for_status()
                data = response.json()
                channels = data.get("channels", [])
                logger.info(f"Получено {len(channels)} каналов")
                return channels
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при получении каналов: {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(f"Ошибка соединения с backend API: {e}. Проверьте, что backend доступен по адресу {self._base_url}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении каналов: {e}")
            raise

    async def add_channel(
        self,
        channel_link: str,
        index_posts: bool = True,
        posts_limit: Optional[int] = None,
    ) -> Dict:
        """Добавить канал."""
        url = f"{self._base_url}/api/channels/"
        payload = {
            "channel_link": channel_link,
            "index_posts": index_posts,
        }
        if posts_limit:
            payload["posts_limit"] = posts_limit

        logger.debug(f"POST {url} с payload: channel_link={channel_link}, index_posts={index_posts}, posts_limit={posts_limit}")
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(url, json=payload)
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                logger.info(f"Канал '{channel_link}' успешно добавлен: {result.get('username', 'unknown')}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при добавлении канала '{channel_link}': {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(f"Ошибка соединения с backend API: {e}. Проверьте, что backend доступен по адресу {self._base_url}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при добавлении канала '{channel_link}': {e}")
            raise

    async def remove_channel(self, channel_username: str) -> Dict:
        """Удалить канал."""
        username = channel_username.lstrip("@")
        url = f"{self._base_url}/api/channels/{username}"
        logger.debug(f"DELETE {url}")
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.delete(url)
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                logger.info(f"Канал '{username}' успешно удален")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при удалении канала '{username}': {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(f"Ошибка соединения с backend API: {e}. Проверьте, что backend доступен по адресу {self._base_url}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при удалении канала '{username}': {e}")
            raise

    async def get_summary(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        channels: Optional[List[str]] = None,
    ) -> Dict:
        """Получить саммари новостей."""
        url = f"{self._base_url}/api/summary"
        payload = {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if channels:
            payload["channels"] = channels

        # Увеличиваем таймаут для summary запросов (генерация может занимать много времени)
        summary_timeout = 300.0  # 5 минут для генерации саммари
        
        logger.debug(f"POST {url} для user_id={user_id}, период: {start_date} - {end_date}, channels={channels}")
        try:
            async with httpx.AsyncClient(
                timeout=summary_timeout, 
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
                response = await client.post(url, json=payload)
                logger.debug(
                    f"Response status: {response.status_code}, "
                    f"size: {len(response.content)} bytes, "
                    f"headers: {dict(response.headers)}"
                )
                response.raise_for_status()
                
                # Проверяем Content-Type
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    logger.warning(
                        f"Неожиданный Content-Type для user_id={user_id}: {content_type}. "
                        f"Response text (first 500 chars): {response.text[:500]}"
                    )
                
                # Пытаемся распарсить JSON с обработкой ошибок
                try:
                    # Используем response.content для получения сырых байтов
                    # и декодируем вручную для лучшей обработки ошибок
                    try:
                        text = response.text
                    except UnicodeDecodeError as decode_error:
                        logger.error(
                            f"Ошибка декодирования ответа для user_id={user_id}: {decode_error}. "
                            f"Content-Type: {content_type}, "
                            f"Response content (first 500 bytes): {response.content[:500]}"
                        )
                        raise httpx.UnexpectedResponse(
                            f"Ошибка декодирования ответа: {decode_error}",
                            request=response.request,
                            response=response,
                        )
                    
                    # Пытаемся распарсить JSON
                    result = response.json()
                except ValueError as json_error:
                    # ValueError возникает при ошибке парсинга JSON
                    logger.error(
                        f"Ошибка парсинга JSON ответа для user_id={user_id}: {json_error}. "
                        f"Content-Type: {content_type}, "
                        f"Response length: {len(response.content)} bytes, "
                        f"Response text (first 1000 chars): {text[:1000] if 'text' in locals() else 'N/A'}"
                    )
                    raise httpx.UnexpectedResponse(
                        f"Не удалось распарсить JSON ответ: {json_error}",
                        request=response.request,
                        response=response,
                    )
                except Exception as json_error:
                    logger.error(
                        f"Неожиданная ошибка при парсинге JSON для user_id={user_id}: {json_error}. "
                        f"Content-Type: {content_type}, "
                        f"Response length: {len(response.content)} bytes, "
                        f"Error type: {type(json_error).__name__}"
                    )
                    raise
                
                posts_count = result.get("posts_processed", 0)
                logger.info(f"Саммари получено для user_id={user_id}: обработано {posts_count} постов")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при получении саммари для user_id={user_id}: {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(f"Ошибка соединения с backend API: {e}. Проверьте, что backend доступен по адресу {self._base_url}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при получении саммари для user_id={user_id}: {e}")
            raise
        except (httpx.UnexpectedResponse, httpx.RemoteProtocolError) as e:
            logger.error(f"Неожиданный ответ от сервера при получении саммари для user_id={user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении саммари для user_id={user_id}: {e}")
            raise

    async def get_completion(
        self, user_id: int, question: str, channels: Optional[List[str]] = None
    ) -> Dict:
        """Получить ответ на вопрос (RAG)."""
        url = f"{self._base_url}/api/completion"
        payload = {
            "user_id": user_id,
            "question": question,
        }
        if channels:
            payload["channels"] = channels

        logger.debug(f"POST {url} для user_id={user_id}, question='{question[:50]}...', channels={channels}")
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(url, json=payload)
                logger.debug(f"Response status: {response.status_code}, size: {len(response.content)} bytes")
                response.raise_for_status()
                result = response.json()
                sources_count = len(result.get("sources", []))
                processing_time = result.get("processing_time", 0)
                logger.info(f"Completion получен для user_id={user_id}: {sources_count} источников, время: {processing_time:.2f}s")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при получении completion для user_id={user_id}: {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
            logger.error(f"Ошибка соединения с backend API: {e}. Проверьте, что backend доступен по адресу {self._base_url}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении completion для user_id={user_id}: {e}")
            raise
