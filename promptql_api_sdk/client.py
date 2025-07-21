"""
PromptQL Natural Language API client implementation.
"""

import json
from typing import Dict, Generator, List, Optional, Union, Any, Literal
from uuid import UUID

import requests
from requests.exceptions import RequestException

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
from promptql_api_sdk.exceptions import PromptQLAPIError


def is_assistant_action_chunk(chunk: Any) -> bool:
    """Check if a chunk is an AssistantActionChunk."""
    return isinstance(chunk, AssistantActionChunk)


def get_message_from_chunk(chunk: Any) -> Optional[str]:
    """Get the message from a chunk if it's an AssistantActionChunk."""
    if is_assistant_action_chunk(chunk) and hasattr(chunk, "message"):
        return chunk.message
    return None


class PromptQLClient:
    """
    Client for the PromptQL Natural Language API.

    This client provides methods to interact with the PromptQL Natural Language API,
    allowing you to send messages and receive responses with support for streaming.

    Supports both v1 and v2 API versions:
    - v1: Requires DDN URL and LLM provider configuration
    - v2: Requires build_version or build_id, LLM config comes from build artifacts
    """

    BASE_URL = "https://api.promptql.pro.hasura.io"
    QUERY_ENDPOINT = "/query"

    api_version: Literal["v1", "v2"]

    def __init__(
        self,
        api_key: str,
        ddn_url: Optional[str] = None,
        llm_provider: Optional[LLMProvider] = None,
        ai_primitives_llm_provider: Optional[LLMProvider] = None,
        timezone: str = "UTC",
        ddn_headers: Optional[Dict[str, str]] = None,
        # v2 parameters
        build_id: Optional[UUID] = None,
        build_version: Optional[str] = None,
    ):
        """
        Initialize the PromptQL client.

        For v1 API (legacy):
            api_key: PromptQL API key created from project settings
            ddn_url: DDN URL for the project
            llm_provider: Configuration for the main LLM provider
            ai_primitives_llm_provider: Optional configuration for the AI primitives LLM provider
            timezone: IANA timezone for interpreting time-based queries
            ddn_headers: Optional headers to pass to DDN for authentication

        For v2 API (recommended):
            api_key: PromptQL API key created from project settings
            build_id: UUID of the DDN build (optional, uses applied build if not specified)
            build_version: Version of the DDN build (optional, uses applied build if not specified)
            timezone: IANA timezone for interpreting time-based queries
            ddn_headers: Optional headers to pass to DDN for authentication
        """
        self.api_key = api_key
        self.timezone = timezone

        # Determine API version based on provided parameters
        if ddn_url is not None:
            # v1 mode
            if llm_provider is None:
                raise ValueError("llm_provider is required for v1 API")
            self.api_version = "v1"
            self.ddn_config = DDNConfig(
                url=ddn_url,
                headers=ddn_headers or {},
            )
            self.llm_provider = llm_provider
            self.ai_primitives_llm_provider = ai_primitives_llm_provider
        else:
            # v2 mode
            self.api_version = "v2"
            self.ddn_config_v2 = DDNConfigV2(
                build_id=build_id,
                build_version=build_version,
                headers=ddn_headers or {},
            )

    def query(
        self,
        message: str,
        system_instructions: Optional[str] = None,
        artifacts: Optional[List[Artifact]] = None,
        previous_interactions: Optional[List[Interaction]] = None,
        stream: bool = False,
    ) -> Union[QueryResponse, Generator[StreamChunk, None, None]]:
        """
        Send a query to the PromptQL Natural Language API.

        Args:
            message: The message to send to the API
            system_instructions: Optional system instructions for the LLM (v1 only, ignored in v2)
            artifacts: Optional list of artifacts to provide context
            previous_interactions: Optional list of previous interactions
            stream: Whether to return a streaming response

        Returns:
            Either a QueryResponse object or a generator of StreamChunk objects

        Raises:
            PromptQLAPIError: If the API returns an error
        """
        # Create the current interaction
        current_interaction = Interaction(
            user_message=UserMessage(text=message),
        )

        # Combine with previous interactions if provided
        interactions = previous_interactions or []
        interactions.append(current_interaction)

        # Create the request based on API version
        if self.api_version == "v1":
            request = QueryRequestV1(
                llm=self.llm_provider,
                ai_primitives_llm=self.ai_primitives_llm_provider,
                ddn=self.ddn_config,
                artifacts=artifacts or [],
                system_instructions=system_instructions,
                timezone=self.timezone,
                interactions=interactions,
                stream=stream,
            )
        else:  # v2
            request = QueryRequestV2(
                ddn=self.ddn_config_v2,
                artifacts=artifacts or [],
                timezone=self.timezone,
                interactions=interactions,
                stream=stream,
            )

        # Send the request
        url = f"{self.BASE_URL}{self.QUERY_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            if stream:
                return self._stream_response(url, headers, request)
            else:
                return self._send_request(url, headers, request)
        except RequestException as e:
            raise PromptQLAPIError(f"Error sending request: {str(e)}") from e

    def _send_request(
        self, url: str, headers: Dict[str, str], request: QueryRequest
    ) -> QueryResponse:
        """
        Send a non-streaming request to the API.

        Args:
            url: The API URL
            headers: Request headers
            request: The request object

        Returns:
            A QueryResponse object

        Raises:
            PromptQLAPIError: If the API returns an error
        """
        response = requests.post(url, headers=headers, data=request.model_dump_json())

        if response.status_code != 200:
            _raise_non_200(response)

        try:
            return QueryResponse.model_validate(response.json())
        except Exception as e:
            raise PromptQLAPIError(f"Error parsing response: {str(e)}") from e

    def _stream_response(
        self, url: str, headers: Dict[str, str], request: QueryRequest
    ) -> Generator[StreamChunk, None, None]:
        """
        Send a streaming request to the API and yield chunks.

        Args:
            url: The API URL
            headers: Request headers
            request: The request object

        Yields:
            StreamChunk objects

        Raises:
            PromptQLAPIError: If the API returns an error
        """
        with requests.post(
            url, headers=headers, data=request.model_dump_json(), stream=True
        ) as response:
            if response.status_code != 200:
                _raise_non_200(response)

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    # SSE format: data: {...}
                    if line.startswith(b"data: "):
                        data = json.loads(line[6:].decode("utf-8"))

                        # Determine the chunk type and parse accordingly
                        chunk_type = data.get("type")

                        if chunk_type == "thread_metadata_chunk":
                            yield ThreadMetadataChunk.model_validate(data)
                        elif chunk_type == "assistant_action_chunk":
                            yield AssistantActionChunk.model_validate(data)
                        elif chunk_type == "artifact_update_chunk":
                            yield ArtifactUpdateChunk.model_validate(data)
                        elif chunk_type == "error_chunk":
                            yield ErrorChunk.model_validate(data)
                        else:
                            # Unknown chunk type, try to parse as generic
                            raise PromptQLAPIError(f"Unknown chunk type: {chunk_type}")
                except Exception as e:
                    raise PromptQLAPIError(
                        f"Error parsing stream chunk: {str(e)}"
                    ) from e

    def create_conversation(
        self,
        system_instructions: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> "Conversation":
        """
        Create a new conversation helper for managing interactions.

        Args:
            system_instructions: Optional system instructions for the LLM
            timezone: Optional timezone override for this conversation

        Returns:
            A Conversation object
        """
        return Conversation(
            client=self,
            system_instructions=system_instructions,
            timezone=timezone or self.timezone,
        )


class Conversation:
    """
    Helper class for managing conversations with the PromptQL Natural Language API.

    This class maintains the conversation state and provides methods to send messages
    and process responses.
    """

    def __init__(
        self,
        client: PromptQLClient,
        system_instructions: Optional[str] = None,
        timezone: Optional[str] = None,
    ):
        """
        Initialize a conversation.

        Args:
            client: The PromptQLClient instance
            system_instructions: Optional system instructions for the LLM
            timezone: Optional timezone override for this conversation
        """
        self.client = client
        self.system_instructions = system_instructions
        self.timezone = timezone or client.timezone
        self.interactions: List[Interaction] = []
        self.artifacts: List[Artifact] = []

    def send_message(
        self, message: str, stream: bool = False
    ) -> Union[AssistantAction, Generator[StreamChunk, None, None]]:
        """
        Send a message in this conversation.

        Args:
            message: The message to send
            stream: Whether to return a streaming response

        Returns:
            Either an AssistantAction object or a generator of StreamChunk objects

        Raises:
            PromptQLAPIError: If the API returns an error
        """
        response = self.client.query(
            message=message,
            system_instructions=self.system_instructions,
            artifacts=self.artifacts,
            previous_interactions=self.interactions,
            stream=stream,
        )

        if stream:
            # For streaming, we need to collect the interactions and artifacts
            # as they come in, and then return the generator
            assert isinstance(response, Generator)
            return self._process_stream(response)
        else:
            # For non-streaming, we can update the state directly
            assert isinstance(response, QueryResponse)

            # Add the new interaction
            self.interactions.append(
                Interaction(
                    user_message=UserMessage(text=message),
                    assistant_actions=response.assistant_actions,
                )
            )

            # Update artifacts
            for artifact in response.modified_artifacts:
                self._update_artifact(artifact)

            # Return the assistant action
            return (
                response.assistant_actions[0]
                if response.assistant_actions
                else AssistantAction()
            )

    def _process_stream(
        self, stream: Generator[StreamChunk, None, None]
    ) -> Generator[StreamChunk, None, None]:
        """
        Process a stream of chunks, updating the conversation state.

        Args:
            stream: The stream of chunks from the API

        Yields:
            The same stream of chunks, for the caller to process

        Raises:
            PromptQLAPIError: If an error chunk is received
        """
        # We'll collect the assistant actions here
        assistant_actions: List[AssistantAction] = []

        # Create a new interaction with just the user message for now
        # We'll add the assistant actions later
        current_interaction = Interaction(
            user_message=UserMessage(text=self.interactions[-1].user_message.text),
        )

        for chunk in stream:
            # Update the conversation state based on the chunk type
            if isinstance(chunk, AssistantActionChunk):
                # Ensure we have enough assistant actions
                while len(assistant_actions) <= chunk.index:
                    assistant_actions.append(AssistantAction())

                # Update the assistant action at the specified index
                action = assistant_actions[chunk.index]

                if chunk.message is not None:
                    action.message = (action.message or "") + chunk.message
                if chunk.plan is not None:
                    action.plan = (action.plan or "") + chunk.plan
                if chunk.code is not None:
                    action.code = (action.code or "") + chunk.code
                if chunk.code_output is not None:
                    action.code_output = (action.code_output or "") + chunk.code_output
                if chunk.code_error is not None:
                    action.code_error = (action.code_error or "") + chunk.code_error

            elif isinstance(chunk, ArtifactUpdateChunk):
                # Update the artifact
                self._update_artifact(chunk.artifact)

            elif isinstance(chunk, ErrorChunk):
                # Raise an exception for error chunks
                raise PromptQLAPIError(f"Stream error: {chunk.error}")

            # Yield the chunk to the caller
            yield chunk

        # Update the interaction with the collected assistant actions
        current_interaction.assistant_actions = assistant_actions
        self.interactions.append(current_interaction)

    def _update_artifact(self, artifact: Artifact) -> None:
        """
        Update an artifact in the conversation.

        Args:
            artifact: The artifact to update
        """
        # Check if the artifact already exists
        for i, existing in enumerate(self.artifacts):
            if existing.identifier == artifact.identifier:
                # Replace the existing artifact
                self.artifacts[i] = artifact
                return

        # If we get here, the artifact doesn't exist yet, so add it
        self.artifacts.append(artifact)

    def get_artifacts(self) -> List[Artifact]:
        """
        Get all artifacts in the conversation.

        Returns:
            A list of artifacts
        """
        return self.artifacts

    def get_interactions(self) -> List[Interaction]:
        """
        Get all interactions in the conversation.

        Returns:
            A list of interactions
        """
        return self.interactions

    def clear(self) -> None:
        """
        Clear the conversation state.
        """
        self.interactions = []
        self.artifacts = []


def _raise_non_200(response: requests.Response):
    """
    Raise an exception for non-200 responses.

    Args:
        response: The response object

    Raises:
        PromptQLAPIError: If the response status is not 200
    """
    # Try to parse the error message from the response
    try:
        error_data = response.json()
        error_message = error_data.get("error", response.text or "Unknown error")
    except Exception as e:
        error_message = (
            f"Error parsing error response: {str(e)}, Response: {response.text}"
        )

    # Raise the exception with the parsed error message
    raise PromptQLAPIError(
        f"API error (status {response.status_code}): {error_message}"
    )
