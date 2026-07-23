# SPDX-License-Identifier: BSD-3-Clause
"""FastAPI dependency accessors for backend application services."""

from __future__ import annotations

from fastapi import Request

from soju.backend.config import BackendSettings
from soju.backend.services.bag import AppServices
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.tts import TtsService


def get_services(request: Request) -> AppServices:
    """Return :class:`AppServices` from ``request.app.state``."""
    return request.app.state.services


def get_llm(request: Request) -> LlmProxyService:
    """Return the LLM application service."""
    return get_services(request).llm


def get_tts(request: Request) -> TtsService:
    """Return the TTS application service."""
    return get_services(request).tts


def get_settings(request: Request) -> BackendSettings:
    """Return backend settings from the service bag."""
    return get_services(request).settings
