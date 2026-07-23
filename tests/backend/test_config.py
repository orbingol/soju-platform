# SPDX-License-Identifier: BSD-3-Clause
"""Backend YAML config load / merge."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pydantic")

from soju.backend.config import deep_merge, load_settings, resolve_config_path, user_config_path


def test_deep_merge_nested() -> None:
    base = {"llm": {"base_url": "http://a", "chat_model": "m1"}, "tts": {"engine": "edge"}}
    override = {"llm": {"base_url": "http://b"}}
    assert deep_merge(base, override) == {
        "llm": {"base_url": "http://b", "chat_model": "m1"},
        "tts": {"engine": "edge"},
    }


def test_load_settings_defaults() -> None:
    settings = load_settings()
    assert settings.llm.provider == "ollama"
    assert settings.tts.engine in {"edge", "piper"}
    assert settings.client.tutor_name
    assert settings.server.port >= 1


def test_load_settings_explicit_override(tmp_path: Path) -> None:
    path = tmp_path / "backend.yaml"
    path.write_text("llm:\n  chat_model: unit-model\nserver:\n  port: 9001\n", encoding="utf-8")
    settings = load_settings(path)
    assert settings.llm.chat_model == "unit-model"
    assert settings.server.port == 9001
    assert settings.tts.engine == "edge"


def test_load_settings_missing_explicit_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_settings(tmp_path / "missing.yaml")


def test_resolve_config_path_explicit(tmp_path: Path) -> None:
    path = tmp_path / "x.yaml"
    assert resolve_config_path(path) == path
    assert user_config_path().name == "backend.yaml"
