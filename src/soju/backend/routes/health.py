# SPDX-License-Identifier: BSD-3-Clause
"""Health probe for the Soju backend."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from soju.backend.config.settings import BackendSettings
from soju.backend.services.deps import get_llm, get_settings, get_tts
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.tts import TtsService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    llm: Annotated[LlmProxyService, Depends(get_llm)],
    tts: Annotated[TtsService, Depends(get_tts)],
    settings: Annotated[BackendSettings, Depends(get_settings)],
) -> dict[str, Any]:
    """Return a lightweight readiness payload (no secrets)."""
    return {
        "ok": True,
        "llm_provider": llm.name,
        "tts_engine": tts.name,
        "chat_model": settings.llm.chat_model,
        "embed_model": settings.llm.embed_model,
    }
