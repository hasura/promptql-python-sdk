"""
Comparison example showing the differences between v1 and v2 API usage.
"""

import os
import sys
from uuid import UUID

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import HasuraLLMProvider, AssistantAction
from promptql_api_sdk.exceptions import PromptQLAPIError


def example_v1():
    """Example using v1 API."""
    print("=== v1 API Example ===")

    # Get required environment variables for v1
    api_key = os.environ.get("PROMPTQL_API_KEY")
    ddn_url = os.environ.get("PROMPTQL_DDN_URL")

    if not api_key or not ddn_url:
        print("For v1 API, please set:")
        print("  PROMPTQL_API_KEY")
        print("  PROMPTQL_DDN_URL")
        return

    # Initialize v1 client
    client = PromptQLClient(
        api_key=api_key,
        ddn_url=ddn_url,
        llm_provider=HasuraLLMProvider(),
        timezone="UTC",
    )

    print(f"✓ v1 client initialized with DDN URL: {ddn_url}")
    print(f"✓ LLM provider: {client.llm_provider.provider}")
    print(f"✓ API version: {client.api_version}")

    try:
        # Create conversation with system instructions
        conversation = client.create_conversation(
            system_instructions="You are a helpful data analyst."
        )

        # Send a simple query
        response = conversation.send_message(
            "Hello, can you help me with data analysis?"
        )
        assert isinstance(response, AssistantAction)
        if response.message:
            print(f"✓ Response: {response.message[:100]}...")

    except PromptQLAPIError as e:
        print(f"✗ Error: {e}")


def example_v2():
    """Example using v2 API."""
    print("\n=== v2 API Example ===")

    # Get required environment variables for v2
    api_key = os.environ.get("PROMPTQL_API_KEY")
    build_id_str = os.environ.get("PROMPTQL_BUILD_ID")
    build_version = os.environ.get("PROMPTQL_BUILD_VERSION")

    if not api_key:
        print("For v2 API, please set PROMPTQL_API_KEY")
        return

    if not build_id_str and not build_version:
        print("For v2 API, please set either:")
        print("  PROMPTQL_BUILD_ID (UUID format)")
        print("  PROMPTQL_BUILD_VERSION (string)")
        return

    # Parse build_id if provided
    build_id = None
    if build_id_str:
        try:
            build_id = UUID(build_id_str)
        except ValueError:
            print(f"Invalid build ID format: {build_id_str}")
            return

    # Initialize v2 client
    client = PromptQLClient(
        api_key=api_key,
        build_id=build_id,
        build_version=build_version,
        timezone="UTC",
    )

    print(f"✓ v2 client initialized")
    if build_id:
        print(f"✓ Build ID: {build_id}")
    if build_version:
        print(f"✓ Build version: {build_version}")
    print(f"✓ API version: {client.api_version}")

    try:
        # Create conversation (system instructions come from project config)
        conversation = client.create_conversation()

        # Send a simple query
        response = conversation.send_message(
            "Hello, can you help me with data analysis?"
        )
        assert isinstance(response, AssistantAction)
        if response.message:
            print(f"✓ Response: {response.message[:100]}...")

    except PromptQLAPIError as e:
        print(f"✗ Error: {e}")


def main():
    """Run both examples."""
    print("PromptQL API SDK - v1 vs v2 Comparison")
    print("=" * 50)

    print("\nKey Differences:")
    print("v1 API:")
    print("  - Requires DDN URL and LLM provider configuration")
    print("  - System instructions specified in requests")
    print("  - More configuration required")

    print("\nv2 API:")
    print("  - Uses build ID or build version")
    print("  - LLM config comes from project settings")
    print("  - System instructions come from project settings")
    print("  - Simpler configuration")

    print("\n" + "=" * 50)

    # Run examples
    example_v1()
    example_v2()

    print("\n" + "=" * 50)
    print(
        "Recommendation: Use v2 API for new projects as it's simpler and more maintainable."
    )


if __name__ == "__main__":
    main()
