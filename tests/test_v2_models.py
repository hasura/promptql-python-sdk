"""
Unit tests for the PromptQL Natural Language API v2 models.
"""

import unittest
import json
from uuid import uuid4, UUID

from promptql_api_sdk.types.models import (
    DDNConfigV2,
    QueryRequestV2,
    Interaction,
    UserMessage,
    ThreadMetadataChunk,
    ChunkType,
)


class TestV2Models(unittest.TestCase):
    """Test cases for the v2 data models."""

    def test_ddn_config_v2(self):
        """Test DDNConfigV2 model."""
        # Test with build_id
        build_id = uuid4()
        config = DDNConfigV2(build_id=build_id)
        self.assertEqual(config.build_id, build_id)
        self.assertIsNone(config.build_version)
        self.assertEqual(config.headers, {})

        # Test with build_version
        config = DDNConfigV2(build_version="505331f4b2")
        self.assertIsNone(config.build_id)
        self.assertEqual(config.build_version, "505331f4b2")
        self.assertEqual(config.headers, {})

        # Test with neither (uses applied build)
        config = DDNConfigV2()
        self.assertIsNone(config.build_id)
        self.assertIsNone(config.build_version)
        self.assertEqual(config.headers, {})

        # Test with custom headers
        headers = {"Authorization": "Bearer token"}
        config = DDNConfigV2(build_id=build_id, headers=headers)
        self.assertEqual(config.headers, headers)

        # Test validation error when both are specified
        with self.assertRaises(ValueError):
            DDNConfigV2(build_id=build_id, build_version="505331f4b2")

    def test_query_request_v2(self):
        """Test QueryRequestV2 model."""
        build_id = uuid4()
        request = QueryRequestV2(
            ddn=DDNConfigV2(build_id=build_id),
            timezone="UTC",
            interactions=[
                Interaction(
                    user_message=UserMessage(text="Test message"),
                )
            ],
            stream=True,
        )

        self.assertEqual(request.version, "v2")
        self.assertEqual(request.ddn.build_id, build_id)
        self.assertEqual(request.timezone, "UTC")
        self.assertEqual(len(request.interactions), 1)
        self.assertEqual(request.interactions[0].user_message.text, "Test message")
        self.assertTrue(request.stream)

        # Test serialization
        json_data = request.model_dump_json()
        data = json.loads(json_data)
        self.assertEqual(data["version"], "v2")
        self.assertEqual(UUID(data["ddn"]["build_id"]), build_id)
        self.assertEqual(data["timezone"], "UTC")
        self.assertEqual(data["stream"], True)

    def test_serialization(self):
        """Test that v2 request can be serialized correctly."""
        # Create a v2 request
        build_id = uuid4()
        v2_request = QueryRequestV2(
            ddn=DDNConfigV2(build_id=build_id),
            timezone="UTC",
            interactions=[
                Interaction(
                    user_message=UserMessage(text="Test message"),
                )
            ],
        )

        # Test that it can be serialized correctly
        json_data = v2_request.model_dump_json()
        data = json.loads(json_data)
        self.assertEqual(data["version"], "v2")

    def test_thread_metadata_chunk(self):
        """Test ThreadMetadataChunk model."""
        thread_id = uuid4()
        chunk = ThreadMetadataChunk(thread_id=thread_id)
        self.assertEqual(chunk.type, ChunkType.THREAD_METADATA_CHUNK)
        self.assertEqual(chunk.thread_id, thread_id)


if __name__ == "__main__":
    unittest.main()
