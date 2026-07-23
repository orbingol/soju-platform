# SPDX-License-Identifier: BSD-3-Clause
"""Browser bootstrap config endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from soju.backend.models.client_config import ClientConfigResponse, client_config_from_settings
from soju.backend.services import AppServices, get_services

router = APIRouter(tags=["client-config"])


@router.get("/v1/soju/client-config", response_model=ClientConfigResponse)
async def client_config(services: Annotated[AppServices, Depends(get_services)]) -> ClientConfigResponse:
    """Return non-secret settings for the web app (models, tutor prompt, TTS defaults)."""
    return client_config_from_settings(services.settings)
