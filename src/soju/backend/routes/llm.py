# SPDX-License-Identifier: BSD-3-Clause
"""OpenAI-compatible LLM proxy routes."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.services import AppServices, get_services

router = APIRouter(tags=["llm"])


@router.get("/v1/models")
async def list_models(services: Annotated[AppServices, Depends(get_services)]) -> dict[str, Any]:
    """Proxy OpenAI-compatible model listing."""
    try:
        return await services.llm.list_models()
    except LlmProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    services: Annotated[AppServices, Depends(get_services)],
) -> Any:
    """Proxy chat completions (JSON or SSE stream)."""
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001 - invalid JSON from client
        raise HTTPException(status_code=400, detail="Request body must be JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    stream = bool(body.get("stream"))
    try:
        result = await services.llm.chat_completions(body, stream=stream)
    except LlmProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if stream:
        if not isinstance(result, AsyncIterator):
            raise HTTPException(status_code=502, detail="LLM stream did not return an async iterator")
        return StreamingResponse(result, media_type="text/event-stream")
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="LLM completion did not return a JSON object")
    return result


@router.post("/v1/embeddings")
async def embeddings(
    request: Request,
    services: Annotated[AppServices, Depends(get_services)],
) -> dict[str, Any]:
    """Proxy OpenAI-compatible embeddings."""
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001 - invalid JSON from client
        raise HTTPException(status_code=400, detail="Request body must be JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    try:
        return await services.llm.embeddings(body)
    except LlmProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
