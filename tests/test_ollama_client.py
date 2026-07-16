# SPDX-License-Identifier: BSD-3-Clause
"""Ollama client helpers (no network)."""

from __future__ import annotations

import pytest

from soju.ollama_client import OllamaError, validate_base_url


def test_validate_base_url_accepts_http() -> None:
    assert validate_base_url("http://localhost:11434") == "http://localhost:11434"
    assert validate_base_url("https://example.com/v1/") == "https://example.com/v1"


def test_validate_base_url_rejects_bad_schemes() -> None:
    with pytest.raises(OllamaError, match="http\\(s\\)"):
        validate_base_url("ftp://localhost")
    with pytest.raises(OllamaError, match="http\\(s\\)"):
        validate_base_url("localhost:11434")
    with pytest.raises(OllamaError, match="http\\(s\\)"):
        validate_base_url("")
