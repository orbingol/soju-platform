# SPDX-License-Identifier: BSD-3-Clause
"""Pydantic models for the Soju backend."""

from __future__ import annotations

from soju.backend.models.settings import (
    BackendSettings,
    ClientSettings,
    LlmSettings,
    PiperTtsSettings,
    ServerSettings,
    TtsSettings,
)

__all__ = [
    "BackendSettings",
    "ClientSettings",
    "LlmSettings",
    "PiperTtsSettings",
    "ServerSettings",
    "TtsSettings",
]
