# SPDX-License-Identifier: BSD-3-Clause
"""FastAPI route smoke tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from soju.backend.app import create_app
from soju.backend.config import BackendSettings


class FakeLlm:
    name = "fake-llm"

    async def list_models(self) -> dict[str, Any]:
        return {"object": "list", "data": [{"id": "fake"}]}

    async def chat_completions(
        self,
        body: dict[str, Any],
        *,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[bytes]:
        if stream:

            async def gen() -> AsyncIterator[bytes]:
                yield b"data: {}\n\n"

            return gen()
        return {"choices": [{"message": {"content": "ok"}}]}

    async def embeddings(self, body: dict[str, Any]) -> dict[str, Any]:
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


def test_embeddings(client: TestClient) -> None:
    response = client.post("/v1/embeddings", json={"input": "theme"})
    assert response.status_code == 200
    assert response.json()["data"][0]["embedding"] == [1.0]
