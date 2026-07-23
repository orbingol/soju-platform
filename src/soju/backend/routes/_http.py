# SPDX-License-Identifier: BSD-3-Clause
"""Shared HTTP helpers for backend routes."""

from __future__ import annotations

from typing import Any, NoReturn

from fastapi import HTTPException, Request

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.abstract.tts import TtsError


async def require_json_object(request: Request) -> dict[str, Any]:
    """Parse the request body as a JSON object or raise HTTP 400."""
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001 - invalid JSON from client
        raise HTTPException(status_code=400, detail="Request body must be JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    return body


def raise_llm_502(exc: LlmProviderError) -> NoReturn:
    """Map an LLM provider failure to HTTP 502."""
    raise HTTPException(status_code=502, detail=str(exc)) from exc


def raise_tts_502(exc: TtsError) -> NoReturn:
    """Map a TTS failure to HTTP 502."""
    raise HTTPException(status_code=502, detail=str(exc) or "TTS failed") from exc
