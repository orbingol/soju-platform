# SPDX-License-Identifier: BSD-3-Clause
"""FastAPI route smoke tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.app import create_app
from soju.backend.config.settings import BackendSettings


class FakeLlm:
    name = "fake-llm"

    def __init__(self, *, fail_models: bool = False) -> None:
        self.fail_models = fail_models

    async def list_models(self) -> dict[str, Any]:
        if self.fail_models:
            raise LlmProviderError("upstream models down")
        return {"object": "list", "data": [{"id": "fake"}]}

    async def chat_completions(
        self,
        body: dict[str, Any],
        *,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[bytes]:
        _ = body
        if stream:

            async def gen() -> AsyncIterator[bytes]:
                yield b"data: {}\n\n"

            return gen()
        return {"choices": [{"message": {"content": "ok"}}]}

    async def embeddings(self, body: dict[str, Any]) -> dict[str, Any]:
        _ = body
        return {
            "data": [{"embedding": [1.0], "index": 0, "object": "embedding"}],
            "object": "list",
            "model": "e",
        }

    async def aclose(self) -> None:
        return None


class FakeTts:
    name = "fake-tts"

    async def synthesize(self, text: str, *, voice: str | None = None, speed: float = 1.0) -> tuple[bytes, str]:
        _ = voice, speed
        if text == "boom":
            from soju.backend.abstract.tts import TtsError

            raise TtsError("synth failed")
        return b"AUDIO", "audio/mpeg"

    async def aclose(self) -> None:
        return None


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr("soju.backend.app.build_llm_provider", lambda _settings: FakeLlm())
    monkeypatch.setattr("soju.backend.app.build_tts_engine", lambda _settings: FakeTts())
    app = create_app(BackendSettings())
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["llm_provider"] == "fake-llm"
    assert body["tts_engine"] == "fake-tts"


def test_client_config(client: TestClient) -> None:
    response = client.get("/v1/soju/client-config")
    assert response.status_code == 200
    body = response.json()
    assert body["tts_engine_label"] == "local"
    assert "system_prompt" in body
    assert body["chat_model"]


def test_speech_missing_text(client: TestClient) -> None:
    response = client.post("/v1/audio/speech", json={"input": "  "})
    assert response.status_code == 400


def test_speech_ok(client: TestClient) -> None:
    response = client.post("/v1/audio/speech", json={"input": "안녕"})
    assert response.status_code == 200
    assert response.content == b"AUDIO"
    assert response.headers["content-type"].startswith("audio/mpeg")


def test_speech_tts_error(client: TestClient) -> None:
    response = client.post("/v1/audio/speech", json={"input": "boom"})
    assert response.status_code == 502


def test_models(client: TestClient) -> None:
    response = client.get("/v1/models")
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "fake"


def test_models_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("soju.backend.app.build_llm_provider", lambda _settings: FakeLlm(fail_models=True))
    monkeypatch.setattr("soju.backend.app.build_tts_engine", lambda _settings: FakeTts())
    app = create_app(BackendSettings())
    with TestClient(app) as test_client:
        response = test_client.get("/v1/models")
    assert response.status_code == 502
    assert "upstream models down" in response.json()["detail"]


def test_chat_completions_json(client: TestClient) -> None:
    response = client.post("/v1/chat/completions", json={"messages": []})
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "ok"


def test_chat_completions_stream(client: TestClient) -> None:
    response = client.post("/v1/chat/completions", json={"messages": [], "stream": True})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert b"data:" in response.content


def test_chat_completions_bad_json(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        content=b"{not-json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Request body must be JSON"


def test_chat_completions_non_object_json(client: TestClient) -> None:
    response = client.post("/v1/chat/completions", json=["not", "an", "object"])
    assert response.status_code == 400
    assert response.json()["detail"] == "Request body must be a JSON object"


def test_embeddings(client: TestClient) -> None:
    response = client.post("/v1/embeddings", json={"input": "theme"})
    assert response.status_code == 200
    assert response.json()["data"][0]["embedding"] == [1.0]
