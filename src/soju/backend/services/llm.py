# SPDX-License-Identifier: BSD-3-Clause
"""Application service: OpenAI-compatible LLM facade over an adapter."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from soju.backend.abstract.llm import LlmProvider, LlmProviderError


class LlmProxyService:
    """Application service wrapping an :class:`~soju.backend.abstract.llm.LlmProvider`."""

    def __init__(self, provider: LlmProvider) -> None:
        self._provider = provider

    @property
    def name(self) -> str:
        return self._provider.name

    async def list_models(self) -> dict[str, Any]:
        return await self._provider.list_models()

    async def chat_completions(
        self,
        body: dict[str, Any],
        *,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[bytes]:
        result = await self._provider.chat_completions(body, stream=stream)
        if stream:
            if not isinstance(result, AsyncIterator):
                raise LlmProviderError("LLM stream did not return an async iterator")
            return result
        if not isinstance(result, dict):
            raise LlmProviderError("LLM completion did not return a JSON object")
        return result

    async def embeddings(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._provider.embeddings(body)

    async def aclose(self) -> None:
        await self._provider.aclose()
