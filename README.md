# PromptQL Natural Language API SDK for Python

A Python SDK for interacting with the [PromptQL Natural Language API](https://hasura.io/docs/promptql/promptql-apis/natural-language-api/).

## Installation

```bash
pip install promptql-api-sdk
```

Or with Poetry:

```bash
poetry add promptql-api-sdk
```

## Features

- Full support for the PromptQL Natural Language API
- Type-safe interface with Pydantic models
- Support for streaming responses
- Conversation management
- Support for all LLM providers (Hasura, Anthropic, OpenAI)

## Quick Start

```python
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import HasuraLLMProvider

# Initialize the client
client = PromptQLClient(
    api_key="your-promptql-api-key",
    ddn_url="your-ddn-url",
    llm_provider=HasuraLLMProvider(),
    timezone="America/Los_Angeles",
)

# Send a simple query
response = client.query("What is the average temperature in San Francisco?")
print(response.assistant_actions[0].message)

# Use streaming for real-time responses
for chunk in client.query("Tell me about the weather in New York", stream=True):
    if hasattr(chunk, "message") and chunk.message:
        print(chunk.message, end="", flush=True)
```

## Conversation Management

The SDK provides a `Conversation` class to help manage multi-turn conversations:

```python
# Create a conversation
conversation = client.create_conversation(
    system_instructions="You are a helpful assistant that provides weather information."
)

# Send messages in the conversation
response = conversation.send_message("What's the weather like in London?")
print(response.message)

# Send a follow-up message
response = conversation.send_message("How about tomorrow?")
print(response.message)

# Get all artifacts created during the conversation
artifacts = conversation.get_artifacts()
```

## LLM Provider Configuration

The SDK supports multiple LLM providers:

```python
from promptql_api_sdk.types.models import HasuraLLMProvider, AnthropicLLMProvider, OpenAILLMProvider

# Hasura (default)
hasura_provider = HasuraLLMProvider()

# Anthropic
anthropic_provider = AnthropicLLMProvider(api_key="your-anthropic-api-key")

# OpenAI
openai_provider = OpenAILLMProvider(api_key="your-openai-api-key")

# Use with the client
client = PromptQLClient(
    api_key="your-promptql-api-key",
    ddn_url="your-ddn-url",
    llm_provider=anthropic_provider,
)
```

## Error Handling

```python
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.exceptions import PromptQLAPIError

client = PromptQLClient(...)

try:
    response = client.query("What is the weather like?")
except PromptQLAPIError as e:
    print(f"API Error: {e}")
```

## License

MIT
