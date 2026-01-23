"""
Domain Layer - доменные модели и сущности.

Принцип SOLID:
- Single Responsibility: каждая модель представляет одну сущность
"""

from domain.channel import Channel, ChannelStatus
from domain.completion import (
    CompletionRequest,
    CompletionResponse,
    SourceReference,
    SummaryRequest,
    SummaryResponse,
)
from domain.document import Document, DocumentMetadata, SearchResult

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
