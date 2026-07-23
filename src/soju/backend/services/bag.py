# SPDX-License-Identifier: BSD-3-Clause
"""Runtime dependency bag attached to the FastAPI app."""

from __future__ import annotations

from dataclasses import dataclass

from soju.backend.config.settings import BackendSettings
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.tts import TtsService


@dataclass(slots=True)
class AppServices:
    """Runtime dependencies: settings plus application services."""

    settings: BackendSettings
    llm: LlmProxyService
    tts: TtsService
