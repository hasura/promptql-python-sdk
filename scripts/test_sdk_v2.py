#!/usr/bin/env python3
"""
Local test script for promptql-api-sdk v2 API.

This script tests the v2 API functionality directly within the SDK repository.
Run this script locally to verify the SDK works with your environment.

Usage:
    poetry run python scripts/test_sdk_v2.py
    poetry run python scripts/test_sdk_v2.py --help
"""
import os
import sys
from typing import Optional
from uuid import UUID

# Import from local SDK
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import AssistantAction
from promptql_api_sdk.exceptions import PromptQLAPIError
from promptql_api_sdk.client import get_message_from_chunk


def test_v2_api():
    """Test the v2 API functionality."""
    print("PromptQL SDK v2 API Local Test")
    print("=" * 40)

    # Get environment variables
    api_key = os.environ.get("PROMPTQL_API_KEY")
    build_id_str = os.environ.get("PROMPTQL_BUILD_ID")
    build_version = os.environ.get("PROMPTQL_BUILD_VERSION")
    ddn_token = os.environ.get("PROMPTQL_DDN_TOKEN")
    api_base_url = os.environ.get("PROMPTQL_API_BASE_URL")

    # Validate required parameters
    if not api_key:
        print("❌ Error: PROMPTQL_API_KEY environment variable is required")
        print_env_help()
        return False

    print(f"✅ API Key: {'*' * 8}")

    # Handle build configuration
    build_id = None
    if build_id_str:
        try:
            build_id = UUID(build_id_str)
            print(f"✅ Build ID: {build_id}")
        except ValueError:
            print(f"❌ Error: Invalid build ID format: {build_id_str}")
            return False
    elif build_version:
        print(f"✅ Build Version: {build_version}")
    else:
        print("ℹ️  Using applied build (no specific build ID/version provided)")

    # Handle DDN token
    ddn_headers = {}
    if ddn_token:
        ddn_headers["x-hasura-ddn-token"] = ddn_token
        print(f"✅ DDN Token: {'*' * 8}")
    else:
        print("⚠️  No DDN token provided (may be required for authentication)")

    print("\n" + "-" * 40)

    # Initialize client
    try:
        print("🔧 Initializing v2 client...")
        client = PromptQLClient(
            api_key=api_key,
            build_id=build_id,
            build_version=build_version,
            timezone="UTC",
            ddn_headers=ddn_headers if ddn_headers else None,
            api_base_url=api_base_url,
        )
        print(f"✅ Client initialized (API version: {client.api_version})")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False

    # Test 1: Non-streaming query
    print("\n📋 Test 1: Non-streaming query")
    try:
        print("   Sending: 'What tables do I have in my database?'")
        response = client.query("What tables do I have in my database?", stream=False)

        print(f"   ✅ Response received")
        print(f"   📊 Assistant actions: {len(response.assistant_actions)}")
        print(f"   📄 Artifacts: {len(response.modified_artifacts)}")

        if response.assistant_actions:
            message = response.assistant_actions[0].message
            preview = message[:100] + "..." if len(message) > 100 else message
            print(f"   💬 Message preview: {preview}")

        if response.modified_artifacts:
            for i, artifact in enumerate(response.modified_artifacts):
                print(
                    f"   📄 Artifact {i+1}: {artifact.title} ({artifact.artifact_type})"
                )

    except PromptQLAPIError as e:
        print(f"   ❌ API Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

    # Test 2: Streaming query
    print("\n🔄 Test 2: Streaming query")
    try:
        print("   Sending: 'Show me the schema of my first table'")
        print("   Response: ", end="", flush=True)

        message_parts = []
        for chunk in client.query("Show me the schema of my first table", stream=True):
            message = get_message_from_chunk(chunk)
            if message:
                print(message, end="", flush=True)
                message_parts.append(message)

        print()  # New line

        if message_parts:
            print("   ✅ Streaming completed successfully")
            full_message = "".join(message_parts)
            print(f"   📏 Total message length: {len(full_message)} characters")
        else:
            print("   ⚠️  No message content received")

    except PromptQLAPIError as e:
        print(f"   ❌ Streaming API Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Streaming error: {e}")
        return False

    # Test 3: Conversation API
    print("\n💬 Test 3: Conversation API")
    try:
        print("   Creating conversation...")
        conversation = client.create_conversation()
        print("   ✅ Conversation created")

        # First message
        print("   Sending: 'Hello, can you help me analyze my data?'")
        response = conversation.send_message("Hello, can you help me analyze my data?")

        if isinstance(response, AssistantAction):
            preview = (
                response.message[:80] + "..."
                if len(response.message) > 80
                else response.message
            )
            print(f"   💬 Response: {preview}")

        # Follow-up with streaming
        print(
            "   Sending streaming follow-up: 'What are the key metrics I should track?'"
        )
        print("   Response: ", end="", flush=True)

        for chunk in conversation.send_message(
            "What are the key metrics I should track?", stream=True
        ):
            message = get_message_from_chunk(chunk)
            if message:
                print(message, end="", flush=True)

        print()  # New line
        print("   ✅ Conversation test completed")

    except PromptQLAPIError as e:
        print(f"   ❌ Conversation API Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Conversation error: {e}")
        return False

    # Success summary
    print("\n" + "=" * 40)
    print("🎉 All tests passed successfully!")
    print("✅ v2 API is working correctly")
    print("=" * 40)
    return True


def print_env_help():
    """Print environment variable help."""
    print("\n📋 Required Environment Variables:")
    print("   PROMPTQL_API_KEY     - Your PromptQL API key")
    print("\n📋 Optional Environment Variables:")
    print("   PROMPTQL_BUILD_ID    - UUID of the DDN build")
    print("   PROMPTQL_BUILD_VERSION - Version of the DDN build")
    print("   PROMPTQL_DDN_TOKEN   - DDN authentication token")
    print("\n💡 Notes:")
    print("   • If neither BUILD_ID nor BUILD_VERSION is set, applied build is used")
    print("   • DDN_TOKEN may be required depending on your DDN configuration")
    print("\n🚀 Example usage:")
    print("   export PROMPTQL_API_KEY=your-api-key")
    print("   export PROMPTQL_BUILD_VERSION=505331f4b2")
    print("   export PROMPTQL_DDN_TOKEN=your-ddn-token")
    print("   python test_sdk_v2.py")


def print_usage():
    """Print usage information."""
    print("PromptQL SDK v2 API Local Test Script")
    print("=" * 40)
    print("\nThis script tests the v2 API functionality of the PromptQL SDK.")
    print("It performs the following tests:")
    print("  1. Non-streaming query")
    print("  2. Streaming query")
    print("  3. Conversation API (both non-streaming and streaming)")
    print("\nThe script requires environment variables to be set with your")
    print("PromptQL credentials and configuration.")
    print_env_help()


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        return

    try:
        success = test_v2_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
