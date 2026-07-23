# SPDX-License-Identifier: BSD-3-Clause
"""Backend adapter protocols (LLM / TTS)."""

from __future__ import annotations

from soju.backend.abstract.llm import LlmProvider, LlmProviderError
from soju.backend.abstract.tts import TtsEngine, TtsError

__all__ = [
    "LlmProvider",
    "LlmProviderError",
    "TtsEngine",
    "TtsError",
]
