# SPDX-License-Identifier: BSD-3-Clause
"""LLM provider protocol for Soju backend OpenAI-compatible facade."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


class LlmProviderError(Exception):
    """Raised when an upstream LLM provider request fails."""


@runtime_checkable
class LlmProvider(Protocol):
    """Async OpenAI-shaped LLM backend (chat, models, embeddings)."""

    @property
    def name(self) -> str:
        """Provider id (e.g. ``ollama``)."""
        ...

    async def list_models(self) -> dict[str, Any]:
        """Return an OpenAI-compatible ``/v1/models`` JSON object.

        Raises:
            LlmProviderError: On transport or upstream failures.
        """
        ...

    async def chat_completions(
        self,
        body: dict[str, Any],
        *,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[bytes]:
        """Run ``/v1/chat/completions``.

        When ``stream`` is false, return the JSON object. When true, return an async
        iterator of raw upstream SSE bytes suitable for ``StreamingResponse``.

        Raises:
            LlmProviderError: On transport or upstream failures.
        """
        ...

    async def embeddings(self, body: dict[str, Any]) -> dict[str, Any]:
        """Return an OpenAI-compatible ``/v1/embeddings`` JSON object.

        Raises:
            LlmProviderError: On transport or upstream failures.
        """
        ...

    async def aclose(self) -> None:
        """Release provider resources (e.g. HTTP clients)."""
        ...
