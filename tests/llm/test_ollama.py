# SPDX-License-Identifier: BSD-3-Clause
"""Ollama client helpers (mocked network + URL validation)."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest

from soju.llm.ollama import OllamaClient, OllamaError, _request, validate_base_url


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


def test_request_http_error() -> None:
    import urllib.error

    err = urllib.error.HTTPError(
        url="http://localhost/api/tags",
        code=500,
        msg="boom",
        hdrs=None,
        fp=io.BytesIO(b"server error"),
    )
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(OllamaError, match="HTTP 500"):
            _request("http://localhost:11434", "/api/tags")


def test_request_url_error() -> None:
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
        with pytest.raises(OllamaError, match="Cannot reach Ollama"):
            _request("http://localhost:11434", "/api/tags")


def test_request_invalid_json_body() -> None:
    response = MagicMock()
    response.read.return_value = b"not-json"
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("urllib.request.urlopen", return_value=response):
        with pytest.raises(OllamaError, match="invalid JSON"):
            _request("http://localhost:11434", "/api/tags")


def test_check_available_false_on_error() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="gemma4:e4b")
    with patch("soju.llm.ollama._request", side_effect=OllamaError("nope")):
        assert client.check_available() is False


def test_check_available_true() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="gemma4:e4b")
    with patch("soju.llm.ollama._request", return_value={"models": []}):
        assert client.check_available() is True


def test_chat_returns_content() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="gemma4:e4b")
    payload = {"message": {"content": ' {"ok": true} '}}
    with patch("soju.llm.ollama._request", return_value=payload) as req:
        content = client.chat([{"role": "user", "content": "hi"}], json_mode=True)
        assert content == '{"ok": true}'
        assert req.call_args.args[1] == "/api/chat"
        assert req.call_args.args[2]["format"] == "json"


def test_chat_empty_content_raises() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="gemma4:e4b")
    with patch("soju.llm.ollama._request", return_value={"message": {"content": "  "}}):
        with pytest.raises(OllamaError, match="empty response"):
            client.chat([{"role": "user", "content": "hi"}])


def test_chat_propagates_request_error() -> None:
    client = OllamaClient(base_url="http://localhost:11434", model="gemma4:e4b")
    with patch("soju.llm.ollama._request", side_effect=OllamaError("fail")):
        with pytest.raises(OllamaError, match="fail"):
            client.chat([{"role": "user", "content": "hi"}])
