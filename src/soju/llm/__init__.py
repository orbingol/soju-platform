# SPDX-License-Identifier: BSD-3-Clause
"""LLM provider abstraction and concrete clients."""

from soju.llm.base import ChatMessage, LlmClient, LlmError
from soju.llm.ollama import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    OllamaClient,
    OllamaError,
    validate_base_url,
)

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_MODEL",
    "ChatMessage",
    "LlmClient",
    "LlmError",
    "OllamaClient",
    "OllamaError",
    "validate_base_url",
]
