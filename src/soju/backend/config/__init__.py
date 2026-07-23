# SPDX-License-Identifier: BSD-3-Clause
"""Backend configuration package (settings models, loader, packaged YAML)."""

from __future__ import annotations

from soju.backend.config.client import ClientConfigResponse, client_config_from_settings
from soju.backend.config.loader import deep_merge, load_settings, resolve_config_path, user_config_path
from soju.backend.config.settings import (
    BackendSettings,
    ClientSettings,
    LlmSettings,
    PiperTtsSettings,
    ServerSettings,
    TtsSettings,
)

__all__ = [
    "BackendSettings",
    "ClientConfigResponse",
    "ClientSettings",
    "LlmSettings",
    "PiperTtsSettings",
    "ServerSettings",
    "TtsSettings",
    "client_config_from_settings",
    "deep_merge",
    "load_settings",
    "resolve_config_path",
    "user_config_path",
]
