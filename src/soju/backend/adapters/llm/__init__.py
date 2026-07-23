# SPDX-License-Identifier: BSD-3-Clause
"""LLM adapter factories and implementations."""

from __future__ import annotations

from soju.backend.abstract.llm import LlmProvider, LlmProviderError
from soju.backend.adapters.llm.ollama import OllamaLlmProvider
from soju.backend.config.settings import LlmSettings


def build_llm_provider(settings: LlmSettings) -> LlmProvider:
    """Construct the configured LLM provider.

    Raises:
        LlmProviderError: If ``settings.provider`` is unsupported.
    """
    if settings.provider == "ollama":
        return OllamaLlmProvider.from_settings(settings)
    raise LlmProviderError(f"Unknown LLM provider {settings.provider!r}; expected 'ollama'")


__all__ = [
    "build_llm_provider",
]
