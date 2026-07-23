# SPDX-License-Identifier: BSD-3-Clause
"""Browser bootstrap config endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from soju.backend.config import BackendSettings, ClientConfigResponse, client_config_from_settings
from soju.backend.services.deps import get_settings

router = APIRouter(tags=["client-config"])


@router.get("/v1/soju/client-config", response_model=ClientConfigResponse)
async def client_config(settings: Annotated[BackendSettings, Depends(get_settings)]) -> ClientConfigResponse:
    """Return non-secret settings for the web app (models, tutor prompt, TTS defaults)."""
    return client_config_from_settings(settings)
