"""Сервис для генерации саммари за период."""

import time
from datetime import datetime
from typing import List, Optional

from domain.completion import SummaryRequest, SummaryResponse
from domain.document import SearchResult
from services.interfaces.llm import ILLMService
from services.interfaces.vectorstore import IVectorStoreRepository

SUMMARY_SYSTEM_PROMPT = """Ты — AI-ассистент для анализа новостей из Telegram-каналов.
Твоя задача — создать краткое и информативное саммари новостей за указанный период.
Группируй новости по темам, выделяй ключевые события."""

SUMMARY_PROMPT_TEMPLATE = """Новости за период {period}:

{news_content}

---

Создай структурированное саммари этих новостей:
1. Выдели 3-5 основных тем
2. Для каждой темы кратко опиши ключевые события
3. В конце добавь общий вывод
4. Если в контексте недостаточно информации для ответа на вопрос - сообщи об этом

Формат ответа:
📰 САММАРИ НОВОСТЕЙ ЗА {period}

📌 [Тема 1]:
- ...

📌 [Тема 2]:
- ...

💡 Общий вывод:
..."""


class SummaryService:
    def __init__(
        self,
        llm_service: ILLMService,
        vectorstore_repository: IVectorStoreRepository,
    ):
        self._llm = llm_service
        self._vectorstore = vectorstore_repository

    def generate_summary(self, request: SummaryRequest) -> SummaryResponse:
        start_time = time.time()

        period_str = self._format_period(request.start_date, request.end_date)
        query = f"новости события {period_str}"

        results = self._vectorstore.search(
            query=query,
            k=50,
        )

        filtered_results = self._filter_by_period(
            results,
            request.start_date,
            request.end_date,
            request.channels,
        )

        if not filtered_results:
            return SummaryResponse(
                summary=f"Не найдено новостей за период {period_str}",
                posts_processed=0,
                period=period_str,
                topics=[],
                channels_included=[],
                processing_time=time.time() - start_time,
            )

        news_content = self._prepare_news_content(filtered_results)

        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            period=period_str,
            news_content=news_content,
        )
        full_prompt = f"{SUMMARY_SYSTEM_PROMPT}\n\n{prompt}"

        summary_text = self._llm.generate(full_prompt)

        channels_included = list(
            set(r.metadata.channel for r in filtered_results if r.metadata.channel)
        )

        return SummaryResponse(
            summary=summary_text,
            posts_processed=len(filtered_results),
            period=period_str,
            topics=[],
            channels_included=channels_included,
            processing_time=time.time() - start_time,
        )

    async def agenerate_summary(self, request: SummaryRequest) -> SummaryResponse:
        start_time = time.time()

        period_str = self._format_period(request.start_date, request.end_date)

        query = f"новости события {period_str}"
        results = await self._vectorstore.asearch(query=query, k=50)

        filtered_results = self._filter_by_period(
            results,
            request.start_date,
            request.end_date,
            request.channels,
        )

        if not filtered_results:
            return SummaryResponse(
                summary=f"Не найдено новостей за период {period_str}",
                posts_processed=0,
                period=period_str,
                topics=[],
                channels_included=[],
                processing_time=time.time() - start_time,
            )

        news_content = self._prepare_news_content(filtered_results)

        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            period=period_str,
            news_content=news_content,
        )
        full_prompt = f"{SUMMARY_SYSTEM_PROMPT}\n\n{prompt}"

        summary_text = await self._llm.agenerate(full_prompt)

        channels_included = list(
            set(r.metadata.channel for r in filtered_results if r.metadata.channel)
        )

        processing_time = time.time() - start_time

        return SummaryResponse(
            summary=summary_text,
            posts_processed=len(filtered_results),
            filtered_results=filtered_results,
            period=period_str,
            topics=[],
            channels_included=channels_included,
            processing_time=processing_time,
        )

    def _format_period(self, start_date: datetime, end_date: datetime) -> str:
        return f"{start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')}"

    def _filter_by_period(
        self,
        results: List[SearchResult],
        start_date: datetime,
        end_date: datetime,
        channels: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        filtered = []

        for result in results:
            doc_date = result.metadata.date

            if doc_date:
                if hasattr(doc_date, "replace"):
                    doc_date_naive = (
                        doc_date.replace(tzinfo=None) if doc_date.tzinfo else doc_date
                    )
                    start_naive = (
                        start_date.replace(tzinfo=None)
                        if start_date.tzinfo
                        else start_date
                    )
                    end_naive = (
                        end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                    )

                    if not (start_naive <= doc_date_naive <= end_naive):
                        continue

            if channels:
                doc_channel = result.metadata.channel
                if doc_channel and doc_channel not in channels:
                    continue

            filtered.append(result)

        return filtered

    def _prepare_news_content(
        self,
        results: List[SearchResult],
        max_chars: int = 10000,
    ) -> str:
        content_parts = []
        total_chars = 0

        for result in results:
            channel = result.metadata.channel or "unknown"
            date = result.metadata.date
            date_str = date.strftime("%d.%m.%Y") if date else "N/A"

            part = f"[{channel}, {date_str}]\n{result.content}\n"

            if total_chars + len(part) > max_chars:
                break

            content_parts.append(part)
            total_chars += len(part)

        return "\n---\n".join(content_parts)
