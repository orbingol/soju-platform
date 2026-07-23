# SPDX-License-Identifier: BSD-3-Clause
"""Shared FastAPI application services (adapters + settings)."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from soju.backend.abstract.llm import LlmProvider
from soju.backend.abstract.tts import TtsEngine
from soju.backend.config import BackendSettings


@dataclass(slots=True)
class AppServices:
    """Runtime dependencies attached to the FastAPI app."""

    settings: BackendSettings
    llm: LlmProvider
    tts: TtsEngine


def get_services(request: Request) -> AppServices:
    """Return :class:`AppServices` from ``request.app.state``."""
    return request.app.state.services
