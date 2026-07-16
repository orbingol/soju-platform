# SPDX-License-Identifier: BSD-3-Clause
"""LLM provider abstraction (Dependency Inversion seam)."""

from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable


class ChatMessage(TypedDict):
    """A single chat message sent to an LLM provider."""

    role: str
    content: str


class LlmError(Exception):
    """Base error for LLM provider failures."""


@runtime_checkable
class LlmClient(Protocol):
    """Minimal chat interface used by Soju services."""

    def chat(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        *,
        json_mode: bool = True,
        temperature: float = 0.3,
        num_predict: int | None = None,
    ) -> str:
        """Return the assistant message content for ``messages``.

        Args:
            messages: Chat messages (typically system + user).
            json_mode: When True, request JSON-formatted output.
            temperature: Sampling temperature.
            num_predict: Optional max tokens / predict length.

        Returns:
            Non-empty assistant content string.

        Raises:
            LlmError: On provider/transport/empty-response failures.
        """
        ...
