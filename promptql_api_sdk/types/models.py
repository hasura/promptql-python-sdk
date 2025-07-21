"""
Data models for the PromptQL Natural Language API.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Literal, Any, Annotated
from uuid import UUID
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
    """DDN configuration for v1 API."""

    url: str
    headers: Dict[str, str] = Field(default_factory=dict)


class DDNConfigV2(BaseModel):
    """DDN configuration for v2 API."""

    build_id: Optional[UUID] = Field(
        default=None,
        description="UUID of the DDN build. If both build_id and build_version are None, uses the applied build.",
        examples=["8ac7ccd4-7502-44d5-b2ee-ea9639b1f653"],
    )
    build_version: Optional[str] = Field(
        default=None,
        description="Version of the DDN build. If both build_id and build_version are None, uses the applied build.",
        examples=["505331f4b2"],
    )
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers that should be forwarded to DDN",
    )

    def model_post_init(self, __context: Any) -> None:
        """Validate that build_id and build_version are not both specified."""
        if self.build_id is not None and self.build_version is not None:
            raise ValueError(
                "Cannot specify both build_id and build_version simultaneously"
            )


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


class QueryRequestBase(BaseModel):
    """Base class for query requests."""

    stream: bool = False
    artifacts: List[Artifact] = Field(default_factory=list)
    timezone: str = Field(
        description="An IANA timezone used to interpret queries that implicitly require timezones",
        examples=["America/Los_Angeles"],
    )
    interactions: List[Interaction]


class QueryRequestV1(QueryRequestBase):
    """Query request model for v1 API."""

    version: Literal["v1"] = "v1"
    promptql_api_key: str
    llm: LLMProvider
    ai_primitives_llm: Optional[LLMProvider] = None
    ddn: DDNConfig
    system_instructions: Optional[str] = None


class QueryRequestV2(QueryRequestBase):
    """Query request model for v2 API."""

    version: Literal["v2"] = "v2"
    ddn: DDNConfigV2


QueryRequest = Annotated[
    Union[QueryRequestV1, QueryRequestV2],
    Field(discriminator="version"),
]


class QueryResponse(BaseModel):
    """Query response model for non-streaming responses."""

    thread_id: UUID
    assistant_actions: List[AssistantAction]
    modified_artifacts: List[Artifact] = Field(
        default_factory=list,
        description="List of artifacts created or updated in this request. May contain duplicate artifact identifiers.",
    )


class ChunkType(str, Enum):
    """Stream chunk types."""

    THREAD_METADATA_CHUNK = "thread_metadata_chunk"
    ASSISTANT_ACTION_CHUNK = "assistant_action_chunk"
    ARTIFACT_UPDATE_CHUNK = "artifact_update_chunk"
    ERROR_CHUNK = "error_chunk"


class ThreadMetadataChunk(BaseModel):
    """Thread metadata chunk for streaming responses."""

    type: Literal[ChunkType.THREAD_METADATA_CHUNK] = ChunkType.THREAD_METADATA_CHUNK
    thread_id: UUID


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


StreamChunk = Union[
    ThreadMetadataChunk, AssistantActionChunk, ArtifactUpdateChunk, ErrorChunk
]
