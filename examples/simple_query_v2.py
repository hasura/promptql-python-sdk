"""
Simple example of using the PromptQL Natural Language API SDK with v2 API.
"""

import os
import sys
from typing import Optional
from uuid import UUID

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import AssistantAction
from promptql_api_sdk.exceptions import PromptQLAPIError
from promptql_api_sdk.client import get_message_from_chunk


def main():
    """Run the example."""
    # Get API key from environment variable
    api_key = os.environ.get("PROMPTQL_API_KEY")
    if not api_key:
        print("Please set the PROMPTQL_API_KEY environment variable")
        sys.exit(1)

    # Get build ID or build version from environment variables
    build_id_str = os.environ.get("PROMPTQL_BUILD_ID")
    build_version = os.environ.get("PROMPTQL_BUILD_VERSION")

    if not build_id_str and not build_version:
        print("Build ID or build version is not set.")
        print("Using applied build by default.")

    # Parse build_id if provided
    build_id = None
    if build_id_str:
        try:
            build_id = UUID(build_id_str)
        except ValueError:
            print(f"Invalid build ID format: {build_id_str}")
            print("Build ID should be a valid UUID")
            sys.exit(1)

    # Initialize the client with v2 API
    client = PromptQLClient(
        api_key=api_key,
        build_id=build_id,
        build_version=build_version,
        timezone="America/Los_Angeles",
    )

    # Create a conversation
    # Note: system_instructions are ignored in v2 API as they come from project config
    conversation = client.create_conversation()

    try:
        # Send a message and get a non-streaming response
        print("\n--- Non-streaming response ---")
        response = conversation.send_message("What tables do I have in my database?")
        # The response is an AssistantAction object
        assert isinstance(response, AssistantAction)
        print(f"Assistant: {response.message}")

        # Send a follow-up message with streaming response
        print("\n--- Streaming response ---")
        print("User: Can you show me the schema of the users table?")
        print("Assistant: ", end="", flush=True)

        for chunk in conversation.send_message(
            "Can you show me the schema of the users table?", stream=True
        ):
            message = get_message_from_chunk(chunk)
            if message:
                print(message, end="", flush=True)

        print("\n")

        # Show any artifacts that were created
        artifacts = conversation.get_artifacts()
        if artifacts:
            print("\n--- Artifacts ---")
            for artifact in artifacts:
                print(f"Artifact: {artifact.title} ({artifact.identifier})")
                print(f"Type: {artifact.artifact_type}")
                print(f"Data: {artifact.data}")
                print()

    except PromptQLAPIError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
