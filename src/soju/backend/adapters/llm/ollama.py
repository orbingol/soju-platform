# SPDX-License-Identifier: BSD-3-Clause
"""Ollama LLM provider via OpenAI-compatible HTTP endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.models.settings import LlmSettings


class OllamaLlmProvider:
    """Proxy to Ollama's OpenAI-compatible ``/v1`` API (with native embeddings fallback)."""

    def __init__(
        self,
        *,
        base_url: str,
        chat_model: str,
        embed_model: str,
        timeout_s: float = 600,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._chat_model = chat_model
        self._embed_model = embed_model
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout_s),
        )

    @classmethod
    def from_settings(cls, settings: LlmSettings, *, client: httpx.AsyncClient | None = None) -> OllamaLlmProvider:
        """Build a provider from :class:`~soju.backend.models.settings.LlmSettings`."""
        return cls(
            base_url=settings.base_url,
            chat_model=settings.chat_model,
            embed_model=settings.embed_model,
            timeout_s=float(settings.timeout_s),
            client=client,
        )

    @property
    def name(self) -> str:
        return "ollama"

    def _ensure_model(self, body: dict[str, Any], default: str) -> dict[str, Any]:
        payload = dict(body)
        model = payload.get("model")
        if not isinstance(model, str) or not model.strip():
            payload["model"] = default
        return payload

    async def list_models(self) -> dict[str, Any]:
        try:
            response = await self._client.get("/v1/models")
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"Ollama /v1/models failed: {exc}") from exc
        if not isinstance(data, dict):
            raise LlmProviderError("Ollama /v1/models returned a non-object JSON payload")
        return data

    async def chat_completions(
        self,
        body: dict[str, Any],
        *,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[bytes]:
        payload = self._ensure_model(body, self._chat_model)
        payload["stream"] = stream

        if not stream:
            try:
                response = await self._client.post("/v1/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                raise LlmProviderError(f"Ollama /v1/chat/completions failed: {exc}") from exc
            if not isinstance(data, dict):
                raise LlmProviderError("Ollama /v1/chat/completions returned a non-object JSON payload")
            return data

        return self._stream_chat_completions(payload)

    async def _stream_chat_completions(self, payload: dict[str, Any]) -> AsyncIterator[bytes]:
        try:
            async with self._client.stream("POST", "/v1/chat/completions", json=payload) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    await response.aread()
                    raise LlmProviderError(f"Ollama /v1/chat/completions stream failed: {exc}") from exc
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
        except LlmProviderError:
            raise
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"Ollama /v1/chat/completions stream failed: {exc}") from exc

    async def embeddings(self, body: dict[str, Any]) -> dict[str, Any]:
        payload = self._ensure_model(body, self._embed_model)
        try:
            response = await self._client.post("/v1/embeddings", json=payload)
            if response.status_code == 404:
                return await self._embeddings_native_fallback(payload)
            response.raise_for_status()
            data = response.json()
        except LlmProviderError:
            raise
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"Ollama /v1/embeddings failed: {exc}") from exc
        if not isinstance(data, dict):
            raise LlmProviderError("Ollama /v1/embeddings returned a non-object JSON payload")
        return data

    async def _embeddings_native_fallback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Translate OpenAI embeddings body to Ollama ``/api/embeddings`` (single prompt)."""
        model = payload.get("model") or self._embed_model
        raw_input = payload.get("input")
        if isinstance(raw_input, list):
            if len(raw_input) != 1 or not isinstance(raw_input[0], str):
                raise LlmProviderError(
                    "Native Ollama embeddings fallback supports a single string input only "
                    "(or use OpenAI-compatible /v1/embeddings)."
                )
            prompt = raw_input[0]
        elif isinstance(raw_input, str):
            prompt = raw_input
        else:
            raise LlmProviderError("Embeddings request missing string 'input'")

        try:
            response = await self._client.post("/api/embeddings", json={"model": model, "prompt": prompt})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"Ollama /api/embeddings failed: {exc}") from exc

        embedding = data.get("embedding") if isinstance(data, dict) else None
        if not isinstance(embedding, list) or not embedding:
            raise LlmProviderError("Ollama /api/embeddings returned an empty or invalid embedding")

        return {
            "object": "list",
            "model": model,
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": embedding,
                }
            ],
        }

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
