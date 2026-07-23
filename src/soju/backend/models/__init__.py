# SPDX-License-Identifier: BSD-3-Clause
"""Pydantic models for the Soju backend."""

from __future__ import annotations

from soju.backend.models.client_config import ClientConfigResponse, client_config_from_settings
from soju.backend.models.settings import (
    BackendSettings,
    ClientSettings,
    LlmSettings,
    PiperTtsSettings,
    ServerSettings,
    TtsSettings,
)
from soju.backend.models.speech import SpeechRequest, resolve_text, resolve_voice

__all__ = [
    "BackendSettings",
    "ClientConfigResponse",
    "ClientSettings",
    "LlmSettings",
    "PiperTtsSettings",
    "ServerSettings",
    "SpeechRequest",
    "TtsSettings",
    "client_config_from_settings",
    "resolve_text",
    "resolve_voice",
]
