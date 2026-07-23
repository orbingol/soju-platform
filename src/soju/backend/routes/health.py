# SPDX-License-Identifier: BSD-3-Clause
"""Health probe for the Soju backend."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from soju.backend.services import AppServices, get_services

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(services: Annotated[AppServices, Depends(get_services)]) -> dict[str, Any]:
    """Return a lightweight readiness payload (no secrets)."""
    return {
        "ok": True,
        "llm_provider": services.llm.name,
        "tts_engine": services.tts.name,
        "chat_model": services.settings.llm.chat_model,
        "embed_model": services.settings.llm.embed_model,
    }
