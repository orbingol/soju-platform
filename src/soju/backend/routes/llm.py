# SPDX-License-Identifier: BSD-3-Clause
"""OpenAI-compatible LLM proxy routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.routes._http import raise_llm_502, require_json_object
from soju.backend.services.deps import get_llm
from soju.backend.services.llm import LlmProxyService

router = APIRouter(tags=["llm"])


@router.get("/v1/models")
async def list_models(llm: Annotated[LlmProxyService, Depends(get_llm)]) -> dict[str, Any]:
    """Proxy OpenAI-compatible model listing."""
    try:
        return await llm.list_models()
    except LlmProviderError as exc:
        raise_llm_502(exc)


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    llm: Annotated[LlmProxyService, Depends(get_llm)],
) -> Any:
    """Proxy chat completions (JSON or SSE stream)."""
    body = await require_json_object(request)
    stream = bool(body.get("stream"))
    try:
        result = await llm.chat_completions(body, stream=stream)
    except LlmProviderError as exc:
        raise_llm_502(exc)

    if stream:
        return StreamingResponse(result, media_type="text/event-stream")
    return result


@router.post("/v1/embeddings")
async def embeddings(
    request: Request,
    llm: Annotated[LlmProxyService, Depends(get_llm)],
) -> dict[str, Any]:
    """Proxy OpenAI-compatible embeddings."""
    body = await require_json_object(request)
    try:
        return await llm.embeddings(body)
    except LlmProviderError as exc:
        raise_llm_502(exc)
