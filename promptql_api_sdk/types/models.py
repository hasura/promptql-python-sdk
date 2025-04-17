"""
Data models for the PromptQL Natural Language API.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field


class LLMProviderType(str, Enum):
    """Supported LLM providers."""

    HASURA = "hasura"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class HasuraLLMProvider(BaseModel):
    """Hasura LLM provider configuration."""

    provider: Literal[LLMProviderType.HASURA] = LLMProviderType.HASURA


class AnthropicLLMProvider(BaseModel):
    """Anthropic LLM provider configuration."""

    provider: Literal[LLMProviderType.ANTHROPIC] = LLMProviderType.ANTHROPIC
    api_key: str


class OpenAILLMProvider(BaseModel):
    """OpenAI LLM provider configuration."""

    provider: Literal[LLMProviderType.OPENAI] = LLMProviderType.OPENAI
    api_key: str


LLMProvider = Union[HasuraLLMProvider, AnthropicLLMProvider, OpenAILLMProvider]


class DDNConfig(BaseModel):
    """DDN configuration."""

    url: str
    headers: Dict[str, str] = Field(default_factory=dict)


class ArtifactType(str, Enum):
    """Supported artifact types."""

    TEXT = "text"
    TABLE = "table"


class Artifact(BaseModel):
    """Artifact model."""

    identifier: str
    title: str
    artifact_type: ArtifactType
    data: Any


class UserMessage(BaseModel):
    """User message model."""

    text: str


class AssistantAction(BaseModel):
    """Assistant action model."""

    message: Optional[str] = None
    plan: Optional[str] = None
    code: Optional[str] = None
    code_output: Optional[str] = None
    code_error: Optional[str] = None


class Interaction(BaseModel):
    """Interaction model."""

    user_message: UserMessage
    assistant_actions: List[AssistantAction] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Query request model."""

    version: Literal["v1"] = "v1"
    promptql_api_key: str
    llm: LLMProvider
    ai_primitives_llm: Optional[LLMProvider] = None
    ddn: DDNConfig
    artifacts: List[Artifact] = Field(default_factory=list)
    system_instructions: Optional[str] = None
    timezone: str
    interactions: List[Interaction]
    stream: bool = False


class QueryResponse(BaseModel):
    """Query response model for non-streaming responses."""

    assistant_actions: List[AssistantAction]
    modified_artifacts: List[Artifact] = Field(default_factory=list)


class ChunkType(str, Enum):
    """Stream chunk types."""

    ASSISTANT_ACTION_CHUNK = "assistant_action_chunk"
    ARTIFACT_UPDATE_CHUNK = "artifact_update_chunk"
    ERROR_CHUNK = "error_chunk"


class AssistantActionChunk(BaseModel):
    """Assistant action chunk for streaming responses."""

    type: Literal[ChunkType.ASSISTANT_ACTION_CHUNK] = ChunkType.ASSISTANT_ACTION_CHUNK
    message: Optional[str] = None
    plan: Optional[str] = None
    code: Optional[str] = None
    code_output: Optional[str] = None
    code_error: Optional[str] = None
    index: int


class ArtifactUpdateChunk(BaseModel):
    """Artifact update chunk for streaming responses."""

    type: Literal[ChunkType.ARTIFACT_UPDATE_CHUNK] = ChunkType.ARTIFACT_UPDATE_CHUNK
    artifact: Artifact


class ErrorChunk(BaseModel):
    """Error chunk for streaming responses."""

    type: Literal[ChunkType.ERROR_CHUNK] = ChunkType.ERROR_CHUNK
    error: str


StreamChunk = Union[AssistantActionChunk, ArtifactUpdateChunk, ErrorChunk]
