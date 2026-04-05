"""LLM provider adapters."""

from waterloo.providers.base import ChatProvider
from waterloo.providers.ollama import OllamaProvider
from waterloo.providers.openai_provider import OpenAICompatibleProvider

__all__ = ["ChatProvider", "OllamaProvider", "OpenAICompatibleProvider"]
