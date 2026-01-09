"""Сервис для retrieval (поиска документов)."""

from typing import Any, Dict, List, Optional

from core.config import settings
from domain.document import SearchResult
from services.interfaces.vectorstore import IVectorStoreRepository


class RetrievalService:
    def __init__(self, vectorstore_repository: IVectorStoreRepository):
        self._vectorstore = vectorstore_repository

    def retrieve(
        self,
        query: str,
        k: int = None,
        channels: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        k = k or settings.retrieval_k

        if channels:
            all_results = []
            for channel in channels:
                results = self._vectorstore.search(
                    query=query,
                    k=k,
                    filter_dict={"channel": channel},
                )
                all_results.extend(results)

            all_results.sort(key=lambda x: x.score, reverse=True)
            results = all_results[:k]
        else:
            results = self._vectorstore.search(query=query, k=k)

        if min_score > 0:
            results = [r for r in results if r.score >= min_score]

        return results

    async def aretrieve(
        self,
        query: str,
        k: int = None,
        channels: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        k = k or settings.retrieval_k

        if channels:
            all_results = []
            for channel in channels:
                results = await self._vectorstore.asearch(
                    query=query,
                    k=k,
                    filter_dict={"channel": channel},
                )
                all_results.extend(results)

            all_results.sort(key=lambda x: x.score, reverse=True)
            results = all_results[:k]
        else:
            results = await self._vectorstore.asearch(query=query, k=k)

        if min_score > 0:
            results = [r for r in results if r.score >= min_score]

        return results

    def get_context_texts(self, results: List[SearchResult]) -> List[str]:
        return [r.content for r in results]

    def get_collection_stats(self) -> Dict[str, Any]:
        return self._vectorstore.get_collection_info()
