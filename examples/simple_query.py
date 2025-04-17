"""
Simple example of using the PromptQL Natural Language API SDK.
"""

import os
import sys
from typing import Optional

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from promptql_api_sdk import PromptQLClient, HasuraLLMProvider
from promptql_api_sdk.exceptions import PromptQLAPIError


def main():
    """Run the example."""
    # Get API key from environment variable
    api_key = os.environ.get("PROMPTQL_API_KEY")
    if not api_key:
        print("Please set the PROMPTQL_API_KEY environment variable")
        sys.exit(1)

    # Get DDN URL from environment variable
    ddn_url = os.environ.get("PROMPTQL_DDN_URL")
    if not ddn_url:
        print("Please set the PROMPTQL_DDN_URL environment variable")
        sys.exit(1)

    # Initialize the client
    client = PromptQLClient(
        api_key=api_key,
        ddn_url=ddn_url,
        llm_provider=HasuraLLMProvider(),
        timezone="America/Los_Angeles",
    )

    # Create a conversation
    conversation = client.create_conversation(
        system_instructions="You are a helpful assistant that provides information about data."
    )

    try:
        # Send a message and get a non-streaming response
        print("\n--- Non-streaming response ---")
        response = conversation.send_message("What tables do I have in my database?")
        print(f"Assistant: {response.message}")

        # Send a follow-up message with streaming response
        print("\n--- Streaming response ---")
        print("User: Can you show me the schema of the users table?")
        print("Assistant: ", end="", flush=True)
        
        for chunk in conversation.send_message(
            "Can you show me the schema of the users table?", stream=True
        ):
            if hasattr(chunk, "message") and chunk.message:
                print(chunk.message, end="", flush=True)
        
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
