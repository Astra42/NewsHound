"""Сервис для генерации ответов (RAG Completion)."""

import time
from typing import List

from domain.completion import (
    CompletionRequest,
    CompletionResponse,
    SourceReference,
)
from domain.document import SearchResult
from services.interfaces.llm import ILLMService
from services.retrieval_service import RetrievalService


class CompletionService:
    def __init__(
        self,
        llm_service: ILLMService,
        retrieval_service: RetrievalService,
    ):
        self._llm = llm_service
        self._retrieval = retrieval_service

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        start_time = time.time()

        search_results = self._retrieval.retrieve(
            query=request.question,
            k=request.top_k,
            channels=request.channels,
        )

        if not search_results:
            return CompletionResponse(
                answer="К сожалению, не удалось найти релевантную информацию по вашему запросу.",
                sources=[],
                processing_time=time.time() - start_time,
            )

        context_texts = self._retrieval.get_context_texts(search_results)
        answer = self._llm.generate_with_context(
            question=request.question,
            context=context_texts,
        )
        sources = self._build_sources(search_results)

        return CompletionResponse(
            answer=answer,
            sources=sources,
            processing_time=time.time() - start_time,
        )

    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        start_time = time.time()

        search_results = await self._retrieval.aretrieve(
            query=request.question,
            k=request.top_k,
            channels=request.channels,
        )

        if not search_results:
            return CompletionResponse(
                answer="К сожалению, не удалось найти релевантную информацию по вашему запросу.",
                sources=[],
                processing_time=time.time() - start_time,
            )

        context_texts = self._retrieval.get_context_texts(search_results)
        answer = await self._llm.agenerate_with_context(
            question=request.question,
            context=context_texts,
        )
        sources = self._build_sources(search_results)

        return CompletionResponse(
            answer=answer,
            sources=sources,
            processing_time=time.time() - start_time,
        )

    def _build_sources(self, results: List[SearchResult]) -> List[SourceReference]:
        sources = []
        for result in results:
            metadata = result.metadata

            source = SourceReference(
                channel=metadata.channel or "unknown",
                date=metadata.date,
                post_id=metadata.message_id,
                url=metadata.url,
                relevance_score=result.score,
            )
            sources.append(source)

        return sources
