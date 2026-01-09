"""
Domain Layer - доменные модели и сущности.

Принцип SOLID:
- Single Responsibility: каждая модель представляет одну сущность
"""

from backend.domain.document import Document, DocumentMetadata, SearchResult
from backend.domain.channel import Channel, ChannelStatus
from backend.domain.completion import (
    CompletionRequest,
    CompletionResponse,
    SummaryRequest,
    SummaryResponse,
    SourceReference,
)

__all__ = [
    "Document",
    "DocumentMetadata",
    "SearchResult",
    "Channel",
    "ChannelStatus",
    "CompletionRequest",
    "CompletionResponse",
    "SummaryRequest",
    "SummaryResponse",
    "SourceReference",
]

