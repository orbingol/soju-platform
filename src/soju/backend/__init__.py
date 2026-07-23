# SPDX-License-Identifier: BSD-3-Clause
"""Soju FastAPI backend (LLM / TTS adapters and OpenAI-compatible HTTP API)."""

from __future__ import annotations

from soju.backend.config import load_settings
from soju.backend.models.settings import BackendSettings

__all__ = ["BackendSettings", "load_settings"]
