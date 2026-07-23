# SPDX-License-Identifier: BSD-3-Clause
"""Pydantic models for the Soju backend HTTP API."""

from __future__ import annotations

from soju.backend.models.speech import SpeechRequest, resolve_text, resolve_voice

__all__ = [
    "SpeechRequest",
    "resolve_text",
    "resolve_voice",
]
