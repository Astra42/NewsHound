"""
Pydantic схемы для API запросов и ответов.
"""

from api.schemas.channels import (
    AddChannelRequestSchema,
    ChannelListResponseSchema,
    ChannelResponseSchema,
)
from api.schemas.common import (
    ErrorResponseSchema,
    HealthResponseSchema,
)
from api.schemas.completion import (
    CompletionRequestSchema,
    CompletionResponseSchema,
)
from api.schemas.summary import (
    SummaryRequestSchema,
    SummaryResponseSchema,
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
