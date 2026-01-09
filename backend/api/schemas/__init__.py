"""
Pydantic схемы для API запросов и ответов.
"""

from backend.api.schemas.completion import (
    CompletionRequestSchema,
    CompletionResponseSchema,
)
from backend.api.schemas.summary import (
    SummaryRequestSchema,
    SummaryResponseSchema,
)
from backend.api.schemas.channels import (
    AddChannelRequestSchema,
    ChannelResponseSchema,
    ChannelListResponseSchema,
)
from backend.api.schemas.common import (
    ErrorResponseSchema,
    HealthResponseSchema,
)

__all__ = [
    "CompletionRequestSchema",
    "CompletionResponseSchema",
    "SummaryRequestSchema",
    "SummaryResponseSchema",
    "AddChannelRequestSchema",
    "ChannelResponseSchema",
    "ChannelListResponseSchema",
    "ErrorResponseSchema",
    "HealthResponseSchema",
]

