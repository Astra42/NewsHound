"""
Mistral LLM реализация.

Принцип SOLID:
- Single Responsibility: только работа с Mistral API
- Liskov Substitution: можно заменить на другую реализацию ILLMService
"""

import asyncio
import time
from typing import List, Optional

import httpx
from core.config import settings
from core.exceptions import (
    LLMException,
    LLMRateLimitException,
    LLMTimeoutException,
)
from langchain_mistralai import ChatMistralAI
from services.interfaces.llm import ILLMService

# Промпты
DEFAULT_SYSTEM_PROMPT = """Ты — AI-ассистент для анализа новостей из Telegram-каналов.
Отвечай на вопросы пользователя, используя только предоставленный контекст.
Если информации недостаточно, честно скажи об этом.
Отвечай на русском языке, кратко и по существу."""

RAG_PROMPT_TEMPLATE = """Контекст (новости из Telegram-каналов):
{context}

---

Вопрос пользователя: {question}

Ответь на вопрос, используя только информацию из контекста выше. 
Если информации недостаточно, укажи это."""


class MistralLLMService(ILLMService):
    """
    Реализация LLM сервиса с использованием Mistral AI.

    Attributes:
        _model: экземпляр ChatMistralAI
        _model_name: название модели
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Инициализация Mistral LLM сервиса.

        Args:
            model_name: название модели (по умолчанию из настроек)
            api_key: API ключ (по умолчанию из настроек)
            timeout: таймаут запроса
            max_retries: количество повторных попыток
        """
        self._model_name = model_name or settings.llm_model
        self._api_key = api_key or settings.mistral_api_key
        self._timeout = timeout or settings.llm_timeout
        self._max_retries = max_retries or settings.llm_max_retries

        self._model = ChatMistralAI(
            model=self._model_name,
            api_key=self._api_key,
            max_retries=self._max_retries,
            timeout=self._timeout,
        )

    @property
    def model_name(self) -> str:
        """Название модели."""
        return self._model_name

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Синхронная генерация текста.

        Args:
            prompt: входной промпт
            max_tokens: максимальное количество токенов
            temperature: температура генерации

        Returns:
            сгенерированный текст

        Raises:
            LLMException: при ошибках API
            LLMTimeoutException: при таймауте
        """
        for attempt in range(self._max_retries):
            try:
                response = self._model.invoke(prompt)
                return response.content

            except httpx.TimeoutException:
                if attempt == self._max_retries - 1:
                    raise LLMTimeoutException(self._timeout)
                time.sleep(2**attempt)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise LLMRateLimitException()
                raise LLMException(f"HTTP ошибка: {e.response.status_code}")

            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise LLMException(
                        f"Ошибка генерации: {type(e).__name__}: {str(e)}"
                    )
                time.sleep(2**attempt)

        raise LLMException("Не удалось сгенерировать ответ")

    async def agenerate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Асинхронная генерация текста.
        """
        for attempt in range(self._max_retries):
            try:
                response = await self._model.ainvoke(prompt)
                return response.content

            except httpx.TimeoutException:
                if attempt == self._max_retries - 1:
                    raise LLMTimeoutException(self._timeout)
                await asyncio.sleep(2**attempt)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise LLMRateLimitException()
                raise LLMException(f"HTTP ошибка: {e.response.status_code}")

            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise LLMException(
                        f"Ошибка генерации: {type(e).__name__}: {str(e)}"
                    )
                await asyncio.sleep(2**attempt)

        raise LLMException("Не удалось сгенерировать ответ")

    def generate_with_context(
        self,
        question: str,
        context: List[str],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Генерация ответа с контекстом (RAG).

        Args:
            question: вопрос пользователя
            context: список документов контекста
            system_prompt: системный промпт

        Returns:
            сгенерированный ответ
        """
        context_str = "\n\n".join(f"[{i + 1}] {doc}" for i, doc in enumerate(context))

        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context_str,
            question=question,
        )

        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"
        else:
            prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\n{prompt}"

        return self.generate(prompt)

    async def agenerate_with_context(
        self,
        question: str,
        context: List[str],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Асинхронная генерация ответа с контекстом.
        """
        context_str = "\n\n".join(f"[{i + 1}] {doc}" for i, doc in enumerate(context))

        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context_str,
            question=question,
        )

        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"
        else:
            prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\n{prompt}"

        return await self.agenerate(prompt)
