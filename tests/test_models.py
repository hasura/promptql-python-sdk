"""
Unit tests for the PromptQL Natural Language API models.
"""

import unittest
import json

from promptql_api_sdk.types.models import (
    LLMProviderType,
    HasuraLLMProvider,
    AnthropicLLMProvider,
    OpenAILLMProvider,
    DDNConfig,
    ArtifactType,
    Artifact,
    UserMessage,
    AssistantAction,
    Interaction,
    QueryRequest,
    QueryResponse,
    ChunkType,
    AssistantActionChunk,
    ArtifactUpdateChunk,
    ErrorChunk,
)


class TestModels(unittest.TestCase):
    """Test cases for the data models."""

    def test_llm_providers(self):
        """Test LLM provider models."""
        # Test Hasura provider
        hasura = HasuraLLMProvider()
        self.assertEqual(hasura.provider, LLMProviderType.HASURA)

        # Test Anthropic provider
        anthropic = AnthropicLLMProvider(api_key="test-api-key")
        self.assertEqual(anthropic.provider, LLMProviderType.ANTHROPIC)
        self.assertEqual(anthropic.api_key, "test-api-key")

        # Test OpenAI provider
        openai = OpenAILLMProvider(api_key="test-api-key")
        self.assertEqual(openai.provider, LLMProviderType.OPENAI)
        self.assertEqual(openai.api_key, "test-api-key")

    def test_ddn_config(self):
        """Test DDN configuration model."""
        # Test with default headers
        ddn = DDNConfig(url="https://test-url.hasura.app")
        self.assertEqual(ddn.url, "https://test-url.hasura.app")
        self.assertEqual(ddn.headers, {})

        # Test with custom headers
        headers = {"Authorization": "Bearer token"}
        ddn = DDNConfig(url="https://test-url.hasura.app", headers=headers)
        self.assertEqual(ddn.headers, headers)

    def test_artifact(self):
        """Test artifact model."""
        # Test text artifact
        text_artifact = Artifact(
            identifier="test-text",
            title="Test Text",
            artifact_type=ArtifactType.TEXT,
            data="This is test data",
        )
        self.assertEqual(text_artifact.identifier, "test-text")
        self.assertEqual(text_artifact.title, "Test Text")
        self.assertEqual(text_artifact.artifact_type, ArtifactType.TEXT)
        self.assertEqual(text_artifact.data, "This is test data")

        # Test table artifact
        table_data = {
            "headers": ["id", "name"],
            "rows": [[1, "Test"], [2, "Test 2"]],
        }
        table_artifact = Artifact(
            identifier="test-table",
            title="Test Table",
            artifact_type=ArtifactType.TABLE,
            data=table_data,
        )
        self.assertEqual(table_artifact.artifact_type, ArtifactType.TABLE)
        self.assertEqual(table_artifact.data, table_data)

    def test_user_message(self):
        """Test user message model."""
        message = UserMessage(text="Test message")
        self.assertEqual(message.text, "Test message")

    def test_assistant_action(self):
        """Test assistant action model."""
        # Test with all fields
        action = AssistantAction(
            message="Test message",
            plan="Test plan",
            code="print('Hello')",
            code_output="Hello",
            code_error=None,
        )
        self.assertEqual(action.message, "Test message")
        self.assertEqual(action.plan, "Test plan")
        self.assertEqual(action.code, "print('Hello')")
        self.assertEqual(action.code_output, "Hello")
        self.assertIsNone(action.code_error)

        # Test with minimal fields
        action = AssistantAction(message="Test message")
        self.assertEqual(action.message, "Test message")
        self.assertIsNone(action.plan)
        self.assertIsNone(action.code)
        self.assertIsNone(action.code_output)
        self.assertIsNone(action.code_error)

    def test_interaction(self):
        """Test interaction model."""
        # Test with assistant actions
        interaction = Interaction(
            user_message=UserMessage(text="Test message"),
            assistant_actions=[AssistantAction(message="Test response")],
        )
        self.assertEqual(interaction.user_message.text, "Test message")
        self.assertIsNotNone(interaction.assistant_actions)
        # Check if assistant_actions is not None to help type checker
        actions = interaction.assistant_actions
        if actions is not None:
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].message, "Test response")

        # Test without assistant actions
        interaction = Interaction(
            user_message=UserMessage(text="Test message"),
        )
        self.assertEqual(interaction.user_message.text, "Test message")
        self.assertIsNone(interaction.assistant_actions)

    def test_query_request(self):
        """Test query request model."""
        request = QueryRequest(
            promptql_api_key="test-api-key",
            llm=HasuraLLMProvider(),
            ddn=DDNConfig(url="https://test-url.hasura.app"),
            timezone="UTC",
            interactions=[
                Interaction(
                    user_message=UserMessage(text="Test message"),
                )
            ],
            stream=True,
        )

        self.assertEqual(request.version, "v1")
        self.assertEqual(request.promptql_api_key, "test-api-key")
        self.assertEqual(request.llm.provider, LLMProviderType.HASURA)
        self.assertEqual(request.ddn.url, "https://test-url.hasura.app")
        self.assertEqual(request.timezone, "UTC")
        self.assertEqual(len(request.interactions), 1)
        self.assertEqual(request.interactions[0].user_message.text, "Test message")
        self.assertTrue(request.stream)

        # Test serialization
        json_data = request.model_dump_json()
        data = json.loads(json_data)
        self.assertEqual(data["version"], "v1")
        self.assertEqual(data["promptql_api_key"], "test-api-key")
        self.assertEqual(data["llm"]["provider"], "hasura")
        self.assertEqual(data["ddn"]["url"], "https://test-url.hasura.app")
        self.assertEqual(data["timezone"], "UTC")
        self.assertEqual(data["stream"], True)

    def test_query_response(self):
        """Test query response model."""
        response = QueryResponse(
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

        self.assertEqual(len(response.assistant_actions), 1)
        self.assertEqual(response.assistant_actions[0].message, "Test response")
        self.assertEqual(len(response.modified_artifacts), 1)
        self.assertEqual(response.modified_artifacts[0].identifier, "test-artifact")

    def test_stream_chunks(self):
        """Test stream chunk models."""
        # Test assistant action chunk
        action_chunk = AssistantActionChunk(
            message="Test message",
            index=0,
        )
        self.assertEqual(action_chunk.type, ChunkType.ASSISTANT_ACTION_CHUNK)
        self.assertEqual(action_chunk.message, "Test message")
        self.assertEqual(action_chunk.index, 0)

        # Test artifact update chunk
        artifact = Artifact(
            identifier="test-artifact",
            title="Test Artifact",
            artifact_type=ArtifactType.TEXT,
            data="Test data",
        )
        artifact_chunk = ArtifactUpdateChunk(
            artifact=artifact,
        )
        self.assertEqual(artifact_chunk.type, ChunkType.ARTIFACT_UPDATE_CHUNK)
        self.assertEqual(artifact_chunk.artifact.identifier, "test-artifact")

        # Test error chunk
        error_chunk = ErrorChunk(
            error="Test error",
        )
        self.assertEqual(error_chunk.type, ChunkType.ERROR_CHUNK)
        self.assertEqual(error_chunk.error, "Test error")


if __name__ == "__main__":
    unittest.main()
