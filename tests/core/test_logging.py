# SPDX-License-Identifier: BSD-3-Clause
"""Logging configuration from env / .env."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pytest

from soju.core import logging as logutil


@pytest.fixture(autouse=True)
def _reset_logging(monkeypatch: pytest.MonkeyPatch):
    logutil.reset_logging()
    for key in (logutil.ENV_ENABLED, logutil.ENV_DESTINATION, logutil.ENV_DIR, logutil.ENV_LEVEL):
        monkeypatch.delenv(key, raising=False)
    yield
    logutil.reset_logging()


def test_logging_disabled_by_default() -> None:
    logger = logutil.configure_logging(force=True)
    assert logger.level == logging.WARNING
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)
    assert logutil.log_path() is None


def test_resolve_log_path_uses_cwd_when_dir_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    when = datetime(2026, 7, 15, 18, 1, 45)
    path = logutil.resolve_log_path(when=when)
    assert path == tmp_path / "soju-log-20260715-180145.log"


def test_resolve_log_path_uses_log_dir(tmp_path: Path) -> None:
    out = tmp_path / "logs"
    when = datetime(2026, 7, 15, 18, 1, 45)
    path = logutil.resolve_log_path(log_dir=str(out), when=when)
    assert path == out.resolve() / "soju-log-20260715-180145.log"


def test_file_destination_writes_to_cwd_when_dir_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(logutil.ENV_ENABLED, "true")
    monkeypatch.setenv(logutil.ENV_DESTINATION, "file")
    monkeypatch.setenv(logutil.ENV_LEVEL, "DEBUG")

    logger = logutil.configure_logging(force=True)
    logger.debug("hello from test")

    path = logutil.log_path()
    assert path is not None
    assert path.parent == tmp_path
    assert path.name.startswith("soju-log-")
    assert path.name.endswith(".log")
    assert path.is_file()
    assert "hello from test" in path.read_text(encoding="utf-8")


def test_file_destination_uses_log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "out"
    monkeypatch.setenv(logutil.ENV_ENABLED, "1")
    monkeypatch.setenv(logutil.ENV_DESTINATION, "file")
    monkeypatch.setenv(logutil.ENV_DIR, str(out))

    logger = logutil.configure_logging(force=True)
    logger.info("dir target")

    path = logutil.log_path()
    assert path is not None
    assert path.parent == out.resolve()
    assert path.is_file()
    assert "dir target" in path.read_text(encoding="utf-8")


def test_stderr_destination(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv(logutil.ENV_ENABLED, "yes")
    monkeypatch.setenv(logutil.ENV_DESTINATION, "stderr")
    monkeypatch.setenv(logutil.ENV_LEVEL, "INFO")

    logger = logutil.configure_logging(force=True)
    logger.info("stderr message")
    captured = capsys.readouterr()
    assert "stderr message" in captured.err
    assert logutil.log_path() is None


def test_get_logger_is_child_of_soju(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(logutil.ENV_ENABLED, "true")
    monkeypatch.setenv(logutil.ENV_DESTINATION, "stderr")
    child = logutil.get_logger("soju.llm.ollama")
    assert child.name == "soju.llm.ollama"
