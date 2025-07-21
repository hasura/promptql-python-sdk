#!/usr/bin/env python3
"""
Local test script for promptql-api-sdk v1 API.

This script tests the v1 API functionality directly within the SDK repository.
Run this script locally to verify the SDK works with your environment.

Usage:
    poetry run python scripts/test_sdk_v1.py
    poetry run python scripts/test_sdk_v1.py --help
"""
import os
import sys
from typing import Optional

# Import from local SDK
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import (
    HasuraLLMProvider,
    AnthropicLLMProvider,
    OpenAILLMProvider,
    AssistantAction,
)
from promptql_api_sdk.exceptions import PromptQLAPIError
from promptql_api_sdk.client import get_message_from_chunk


def get_llm_provider(provider_name: str = "hasura"):
    """Get the LLM provider based on the name."""
    if provider_name == "hasura":
        return HasuraLLMProvider()
    elif provider_name == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print(
                "❌ Error: ANTHROPIC_API_KEY environment variable is required for Anthropic provider"
            )
            return None
        return AnthropicLLMProvider(api_key=api_key)
    elif provider_name == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(
                "❌ Error: OPENAI_API_KEY environment variable is required for OpenAI provider"
            )
            return None
        return OpenAILLMProvider(api_key=api_key)
    else:
        print(f"❌ Error: Unknown provider: {provider_name}")
        print("Supported providers: hasura, anthropic, openai")
        return None


def test_v1_api():
    """Test the v1 API functionality."""
    print("PromptQL SDK v1 API Local Test")
    print("=" * 40)

    # Get environment variables
    api_key = os.environ.get("PROMPTQL_API_KEY")
    ddn_url = os.environ.get("PROMPTQL_DDN_URL")
    ddn_token = os.environ.get("PROMPTQL_DDN_TOKEN")
    llm_provider_name = os.environ.get("PROMPTQL_LLM_PROVIDER", "hasura")
    api_base_url = os.environ.get("PROMPTQL_API_BASE_URL")

    # Validate required parameters
    if not api_key:
        print("❌ Error: PROMPTQL_API_KEY environment variable is required")
        print_env_help()
        return False

    if not ddn_url:
        print("❌ Error: PROMPTQL_DDN_URL environment variable is required")
        print_env_help()
        return False

    print(f"✅ API Key: {'*' * 8}")
    print(f"✅ DDN URL: {ddn_url}")

    # Get LLM provider
    llm_provider = get_llm_provider(llm_provider_name)
    if llm_provider is None:
        return False

    print(f"✅ LLM Provider: {llm_provider.provider}")

    print("\n" + "-" * 40)

    # Initialize client
    try:
        print("🔧 Initializing v1 client...")
        ddn_headers = {"x-hasura-ddn-token": ddn_token} if ddn_token else None
        client = PromptQLClient(
            api_key=api_key,
            ddn_url=ddn_url,
            llm_provider=llm_provider,
            timezone="UTC",
            api_base_url=api_base_url,
            ddn_headers=ddn_headers,
        )
        print(f"✅ Client initialized (API version: {client.api_version})")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False

    # Test 1: Non-streaming query
    print("\n📋 Test 1: Non-streaming query")
    try:
        print("   Sending: 'What tables do I have in my database?'")
        response = client.query(
            "What tables do I have in my database?",
            stream=False,
            system_instructions="You are a helpful data analyst assistant.",
        )

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
        for chunk in client.query(
            "Show me the schema of my first table",
            stream=True,
            system_instructions="You are a helpful database expert.",
        ):
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
        conversation = client.create_conversation(
            system_instructions="You are a helpful data analyst who provides clear and concise answers."
        )
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
    print("✅ v1 API is working correctly")
    print("=" * 40)
    return True


def print_env_help():
    """Print environment variable help."""
    print("\n📋 Required Environment Variables:")
    print("   PROMPTQL_API_KEY     - Your PromptQL API key")
    print("   PROMPTQL_DDN_URL     - Your DDN /v1/sql endpoint URL")
    print("\n📋 Optional Environment Variables:")
    print(
        "   PROMPTQL_LLM_PROVIDER - LLM provider (hasura, anthropic, openai) [default: hasura]"
    )
    print("   ANTHROPIC_API_KEY    - Required if using Anthropic provider")
    print("   OPENAI_API_KEY       - Required if using OpenAI provider")
    print("   PROMPTQL_API_BASE_URL - Custom API base URL")
    print("\n💡 Notes:")
    print("   • v1 API requires explicit DDN URL and LLM provider configuration")
    print("   • System instructions are specified per request in v1 API")
    print("   • Hasura provider is the default and doesn't require additional API keys")
    print("\n🚀 Example usage:")
    print("   export PROMPTQL_API_KEY=your-api-key")
    print("   export PROMPTQL_DDN_URL=https://your-ddn.hasura.app/v1/sql")
    print("   export PROMPTQL_LLM_PROVIDER=hasura")
    print("   python test_sdk_v1.py")


def print_usage():
    """Print usage information."""
    print("PromptQL SDK v1 API Local Test Script")
    print("=" * 40)
    print("\nThis script tests the v1 API functionality of the PromptQL SDK.")
    print("It performs the following tests:")
    print("  1. Non-streaming query with system instructions")
    print("  2. Streaming query with system instructions")
    print("  3. Conversation API (both non-streaming and streaming)")
    print("\nThe script requires environment variables to be set with your")
    print("PromptQL credentials and DDN configuration.")
    print_env_help()


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        return

    try:
        success = test_v1_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
