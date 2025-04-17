"""
Advanced example of using the PromptQL Natural Language API SDK with streaming and artifacts.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from promptql_api_sdk import (
    PromptQLClient,
    HasuraLLMProvider,
    AnthropicLLMProvider,
    OpenAILLMProvider,
    Artifact,
    ArtifactType,
)
from promptql_api_sdk.exceptions import PromptQLAPIError


def get_llm_provider(provider_name: str) -> Any:
    """Get the LLM provider based on the name."""
    if provider_name == "hasura":
        return HasuraLLMProvider()
    elif provider_name == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Please set the ANTHROPIC_API_KEY environment variable")
            sys.exit(1)
        return AnthropicLLMProvider(api_key=api_key)
    elif provider_name == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Please set the OPENAI_API_KEY environment variable")
            sys.exit(1)
        return OpenAILLMProvider(api_key=api_key)
    else:
        print(f"Unknown provider: {provider_name}")
        print("Supported providers: hasura, anthropic, openai")
        sys.exit(1)


def create_sample_artifacts() -> List[Artifact]:
    """Create some sample artifacts for the conversation."""
    text_artifact = Artifact(
        identifier="sample_text",
        title="Sample Text",
        artifact_type=ArtifactType.TEXT,
        data="This is a sample text artifact that provides some context for the conversation.",
    )

    table_artifact = Artifact(
        identifier="sample_table",
        title="Sample Table",
        artifact_type=ArtifactType.TABLE,
        data={
            "headers": ["id", "name", "email"],
            "rows": [
                [1, "John Doe", "john@example.com"],
                [2, "Jane Smith", "jane@example.com"],
                [3, "Bob Johnson", "bob@example.com"],
            ],
        },
    )

    return [text_artifact, table_artifact]


def interactive_conversation(client: PromptQLClient):
    """Run an interactive conversation with the PromptQL API."""
    print("\n=== PromptQL Interactive Conversation ===")
    print("Type 'exit' to quit, 'stream' to toggle streaming, 'artifacts' to show artifacts")
    
    # Create a conversation with sample artifacts
    conversation = client.create_conversation(
        system_instructions="You are a helpful assistant that provides information about data."
    )
    
    # Add sample artifacts
    for artifact in create_sample_artifacts():
        conversation._update_artifact(artifact)
    
    # Set initial streaming mode
    streaming = True
    print(f"Streaming mode: {'ON' if streaming else 'OFF'}")
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for commands
        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "stream":
            streaming = not streaming
            print(f"Streaming mode: {'ON' if streaming else 'OFF'}")
            continue
        elif user_input.lower() == "artifacts":
            artifacts = conversation.get_artifacts()
            if artifacts:
                print("\n--- Artifacts ---")
                for artifact in artifacts:
                    print(f"Artifact: {artifact.title} ({artifact.identifier})")
                    print(f"Type: {artifact.artifact_type}")
                    print()
            else:
                print("No artifacts available")
            continue
        
        # Send the message
        try:
            if streaming:
                print("Assistant: ", end="", flush=True)
                for chunk in conversation.send_message(user_input, stream=True):
                    if hasattr(chunk, "message") and chunk.message:
                        print(chunk.message, end="", flush=True)
                print()
            else:
                response = conversation.send_message(user_input)
                print(f"Assistant: {response.message}")
                
                if response.code:
                    print("\n--- Code ---")
                    print(response.code)
                    
                if response.code_output:
                    print("\n--- Code Output ---")
                    print(response.code_output)
                    
                if response.code_error:
                    print("\n--- Code Error ---")
                    print(response.code_error)
        
        except PromptQLAPIError as e:
            print(f"Error: {e}")


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
    
    # Get LLM provider from command line or default to hasura
    provider_name = sys.argv[1] if len(sys.argv) > 1 else "hasura"
    llm_provider = get_llm_provider(provider_name)

    # Initialize the client
    client = PromptQLClient(
        api_key=api_key,
        ddn_url=ddn_url,
        llm_provider=llm_provider,
        timezone="America/Los_Angeles",
    )

    # Run the interactive conversation
    interactive_conversation(client)


if __name__ == "__main__":
    main()
