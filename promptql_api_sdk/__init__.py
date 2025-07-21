"""
PromptQL Natural Language API SDK for Python.

This SDK provides a Python interface to the PromptQL Natural Language API.
"""

from promptql_api_sdk.client import PromptQLClient
from promptql_api_sdk.types import (
    LLMProvider,
    DDNConfig,
    DDNConfigV2,
    Artifact,
    UserMessage,
    AssistantAction,
    Interaction,
    QueryRequest,
    QueryRequestV1,
    QueryRequestV2,
    QueryResponse,
    StreamChunk,
    ThreadMetadataChunk,
    AssistantActionChunk,
    ArtifactUpdateChunk,
    ErrorChunk,
)

__all__ = [
    "PromptQLClient",
    "LLMProvider",
    "DDNConfig",
    "DDNConfigV2",
    "Artifact",
    "UserMessage",
    "AssistantAction",
    "Interaction",
    "QueryRequest",
    "QueryRequestV1",
    "QueryRequestV2",
    "QueryResponse",
    "StreamChunk",
    "ThreadMetadataChunk",
    "AssistantActionChunk",
    "ArtifactUpdateChunk",
    "ErrorChunk",
]

__version__ = "0.2.0"
