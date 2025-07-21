"""
Unit tests for the PromptQL Natural Language API client.
"""

import json
import unittest
from typing import cast
from unittest.mock import patch, MagicMock
from uuid import uuid4

from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import (
    HasuraLLMProvider,
    UserMessage,
    AssistantAction,
    Interaction,
    QueryResponse,
    ThreadMetadataChunk,
    AssistantActionChunk,
    Artifact,
    ArtifactType,
)
from promptql_api_sdk.exceptions import PromptQLAPIError


class TestPromptQLClient(unittest.TestCase):
    """Test cases for the PromptQLClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.ddn_url = "https://test-ddn-url.hasura.app"
        self.llm_provider = HasuraLLMProvider()
        self.client = PromptQLClient(
            api_key=self.api_key,
            ddn_url=self.ddn_url,
            llm_provider=self.llm_provider,
            timezone="UTC",
        )

    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.ddn_config.url, self.ddn_url)
        self.assertEqual(self.client.ddn_config.headers, {})
        self.assertEqual(self.client.llm_provider, self.llm_provider)
        self.assertEqual(self.client.timezone, "UTC")

    @patch("requests.post")
    def test_query_non_streaming(self, mock_post):
        """Test non-streaming query."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "thread_id": str(uuid4()),
            "assistant_actions": [
                {
                    "message": "This is a test response",
                    "plan": None,
                    "code": None,
                    "code_output": None,
                    "code_error": None,
                }
            ],
            "modified_artifacts": [],
        }
        mock_post.return_value = mock_response

        # Call the method
        response = self.client.query("Test message")

        # Verify the response
        self.assertIsInstance(response, QueryResponse)
        # Cast to QueryResponse to help type checker
        query_response = cast(QueryResponse, response)
        self.assertEqual(len(query_response.assistant_actions), 1)
        self.assertEqual(
            query_response.assistant_actions[0].message, "This is a test response"
        )

        # Verify the request
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.promptql.pro.hasura.io/query")
        self.assertEqual(
            kwargs["headers"],
            {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-api-key",
            },
        )

        # Parse the request data
        request_data = json.loads(kwargs["data"])
        self.assertEqual(request_data["version"], "v1")
        self.assertEqual(request_data["llm"]["provider"], "hasura")
        self.assertEqual(request_data["ddn"]["url"], self.ddn_url)
        self.assertEqual(len(request_data["interactions"]), 1)
        self.assertEqual(
            request_data["interactions"][0]["user_message"]["text"], "Test message"
        )
        self.assertEqual(request_data["stream"], False)

    @patch("requests.post")
    def test_query_streaming(self, mock_post):
        """Test streaming query."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        thread_id = str(uuid4())
        mock_response.iter_lines.return_value = [
            f'data: {{"type": "thread_metadata_chunk", "thread_id": "{thread_id}"}}'.encode(),
            b'data: {"type": "assistant_action_chunk", "message": "This is ", "plan": null, "code": null, "code_output": null, "code_error": null, "index": 0}',
            b'data: {"type": "assistant_action_chunk", "message": "a test ", "plan": null, "code": null, "code_output": null, "code_error": null, "index": 0}',
            b'data: {"type": "assistant_action_chunk", "message": "response", "plan": null, "code": null, "code_output": null, "code_error": null, "index": 0}',
        ]
        mock_post.return_value.__enter__.return_value = mock_response

        # Call the method
        chunks = list(self.client.query("Test message", stream=True))

        # Verify the chunks
        self.assertEqual(len(chunks), 4)
        self.assertIsInstance(chunks[0], ThreadMetadataChunk)
        self.assertIsInstance(chunks[1], AssistantActionChunk)
        # Check ThreadMetadataChunk
        thread_chunk = cast(ThreadMetadataChunk, chunks[0])
        self.assertIsNotNone(thread_chunk.thread_id)

        # Cast to AssistantActionChunk to help type checker
        chunk1 = cast(AssistantActionChunk, chunks[1])
        chunk2 = cast(AssistantActionChunk, chunks[2])
        chunk3 = cast(AssistantActionChunk, chunks[3])
        self.assertEqual(chunk1.message, "This is ")
        self.assertEqual(chunk2.message, "a test ")
        self.assertEqual(chunk3.message, "response")

        # Verify the request
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.promptql.pro.hasura.io/query")

        # Parse the request data
        request_data = json.loads(kwargs["data"])
        self.assertEqual(request_data["stream"], True)

    @patch("requests.post")
    def test_query_error(self, mock_post):
        """Test error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Test error message"}
        mock_post.return_value = mock_response

        # Call the method and check for exception
        with self.assertRaises(PromptQLAPIError) as context:
            self.client.query("Test message")

        # Verify the error message
        self.assertIn(
            "API error (status 400): Test error message", str(context.exception)
        )

    def test_create_conversation(self):
        """Test conversation creation."""
        conversation = self.client.create_conversation(
            system_instructions="Test instructions",
            timezone="America/New_York",
        )

        self.assertEqual(conversation.client, self.client)
        self.assertEqual(conversation.system_instructions, "Test instructions")
        self.assertEqual(conversation.timezone, "America/New_York")
        self.assertEqual(conversation.interactions, [])
        self.assertEqual(conversation.artifacts, [])


class TestConversation(unittest.TestCase):
    """Test cases for the Conversation class."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        # Create a real Conversation instance instead of a mock
        from promptql_api_sdk.client import Conversation

        self.conversation = Conversation(client=self.client)
        self.conversation.interactions = []
        self.conversation.artifacts = []

    def test_send_message_non_streaming(self):
        """Test sending a non-streaming message."""
        # Mock the client.query method
        mock_response = QueryResponse(
            thread_id=uuid4(),
            assistant_actions=[AssistantAction(message="Test response")],
            modified_artifacts=[
                Artifact(
                    identifier="test-artifact",
                    title="Test Artifact",
                    artifact_type=ArtifactType.TEXT,
                    data="Test data",
                )
            ],
        )
        self.client.query = MagicMock(return_value=mock_response)

        # Set up the conversation
        self.conversation.interactions = [
            Interaction(
                user_message=UserMessage(text="Previous message"),
                assistant_actions=[AssistantAction(message="Previous response")],
            )
        ]

        # Call the method
        response = self.conversation.send_message("Test message")

        # Verify the response
        self.assertIsInstance(response, AssistantAction)
        # Cast to AssistantAction to help type checker
        assistant_action = cast(AssistantAction, response)
        self.assertEqual(assistant_action.message, "Test response")

        # Verify the conversation state
        self.assertEqual(len(self.conversation.interactions), 2)
        self.assertEqual(
            self.conversation.interactions[1].user_message.text, "Test message"
        )
        # Check assistant actions
        actions = self.conversation.interactions[1].assistant_actions
        self.assertIsNotNone(actions)
        if actions is not None:  # This helps the type checker
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].message, "Test response")

        self.assertEqual(len(self.conversation.artifacts), 1)
        self.assertEqual(self.conversation.artifacts[0].identifier, "test-artifact")
        self.assertEqual(self.conversation.artifacts[0].title, "Test Artifact")

    def test_update_artifact_new(self):
        """Test updating a new artifact."""
        # Create a new artifact
        artifact = Artifact(
            identifier="test-artifact",
            title="Test Artifact",
            artifact_type=ArtifactType.TEXT,
            data="Test data",
        )

        # Make sure artifacts list is empty
        self.conversation.artifacts = []

        # Update the artifact
        self.conversation._update_artifact(artifact)

        # Verify the artifact was added
        self.assertEqual(len(self.conversation.artifacts), 1)
        self.assertEqual(self.conversation.artifacts[0].identifier, "test-artifact")
        self.assertEqual(self.conversation.artifacts[0].title, "Test Artifact")

    def test_update_artifact_existing(self):
        """Test updating an existing artifact."""
        # Add an existing artifact
        self.conversation.artifacts = [
            Artifact(
                identifier="test-artifact",
                title="Test Artifact",
                artifact_type=ArtifactType.TEXT,
                data="Old data",
            )
        ]

        # Create an updated artifact
        updated_artifact = Artifact(
            identifier="test-artifact",
            title="Updated Artifact",
            artifact_type=ArtifactType.TEXT,
            data="New data",
        )

        # Update the artifact
        self.conversation._update_artifact(updated_artifact)

        # Verify the artifact was updated
        self.assertEqual(len(self.conversation.artifacts), 1)
        self.assertEqual(self.conversation.artifacts[0].identifier, "test-artifact")
        self.assertEqual(self.conversation.artifacts[0].title, "Updated Artifact")
        self.assertEqual(self.conversation.artifacts[0].data, "New data")

    def test_clear(self):
        """Test clearing the conversation."""
        # Add some data
        self.conversation.interactions = [
            Interaction(
                user_message=UserMessage(text="Test message"),
                assistant_actions=[AssistantAction(message="Test response")],
            )
        ]
        self.conversation.artifacts = [
            Artifact(
                identifier="test-artifact",
                title="Test Artifact",
                artifact_type=ArtifactType.TEXT,
                data="Test data",
            )
        ]

        # Clear the conversation
        self.conversation.clear()

        # Verify the conversation was cleared
        self.assertEqual(len(self.conversation.interactions), 0)
        self.assertEqual(len(self.conversation.artifacts), 0)


if __name__ == "__main__":
    unittest.main()
