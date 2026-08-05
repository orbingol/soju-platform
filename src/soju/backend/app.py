# SPDX-License-Identifier: BSD-3-Clause
"""FastAPI application factory for the Soju backend."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from soju.backend.adapters.llm import build_llm_provider
from soju.backend.adapters.tts import build_tts_engine
from soju.backend.config.settings import BackendSettings
from soju.backend.config.loader import load_settings
from soju.backend.routes import client_config, health, llm, practice, tts
from soju.backend.services.bag import AppServices
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.tts import TtsService


def create_app(settings: BackendSettings | None = None) -> FastAPI:
    """Build the Soju backend FastAPI app.

    Args:
        settings: Optional preloaded settings; when omitted, loads via :func:`~soju.backend.config.load_settings`
            (``~/.config/soju/backend.yaml`` if present, else packaged defaults).
    """
    resolved = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        llm_provider = build_llm_provider(resolved.llm)
        tts_engine = build_tts_engine(resolved.tts)
        llm_service = LlmProxyService(llm_provider)
        tts_service = TtsService(tts_engine, default_voice=resolved.tts.voice)
        app.state.services = AppServices(settings=resolved, llm=llm_service, tts=tts_service)
        try:
            yield
        finally:
            await llm_service.aclose()
            await tts_service.aclose()

    app = FastAPI(
        title="Soju Backend",
        version="0.1.0",
        lifespan=lifespan,
        # So Swagger UI fetches /api/openapi.json when nginx strips the /api prefix.
        root_path=resolved.server.root_path,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.server.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def redirect_root_to_docs() -> RedirectResponse:
        # Absolute path (includes root_path) so /api without a trailing slash does not
        # resolve relative "docs" as host /docs (Sphinx).
        root = resolved.server.root_path
        return RedirectResponse(url=f"{root}/docs" if root else "/docs")

    app.include_router(health.router)
    app.include_router(tts.router)
    app.include_router(llm.router)
    app.include_router(client_config.router)
    app.include_router(practice.router)
    return app
