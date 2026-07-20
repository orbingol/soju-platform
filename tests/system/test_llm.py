# SPDX-License-Identifier: BSD-3-Clause
"""Optional LLM system tests (Ollama). Skipped unless ``--llm`` / ``SOJU_RUN_LLM_TESTS=1``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from soju.cli import examples as examples_cli
from soju.cli import translate as translate_cli
from soju.llm.ollama import DEFAULT_BASE_URL, OllamaClient

pytestmark = [pytest.mark.system, pytest.mark.llm]

runner = CliRunner()


@pytest.fixture(scope="module")
def ollama_ready() -> OllamaClient:
    client = OllamaClient(base_url=DEFAULT_BASE_URL)
    if not client.check_available():
        pytest.skip(f"Ollama not reachable at {DEFAULT_BASE_URL}")
    return client


def test_translate_words_via_cli(data_env: Path, tmp_path: Path, ollama_ready: OllamaClient) -> None:
    """``soju translate-words`` produces importable JSON for a single hangul line."""
    word_list = tmp_path / "words.txt"
    word_list.write_text("사과\n", encoding="utf-8")
    out = tmp_path / "out.json"
    result = runner.invoke(
        translate_cli.app,
        [
            "--file",
            str(word_list),
            "--output",
            str(out),
            "--batch-size",
            "1",
            "--model",
            ollama_ready.model,
            "--base-url",
            ollama_ready.base_url,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "사과" in text
    assert '"records"' in text


def test_fill_examples_via_cli_limit(data_env: Path, ollama_ready: OllamaClient) -> None:
    """``soju fill-examples`` with ``--limit 1`` talks to Ollama for one entry."""
    result = runner.invoke(
        examples_cli.app,
        [
            "--limit",
            "1",
            "--nouns-only",
            "--mode",
            "refresh-all",
            "--examples",
            "1",
            "--model",
            ollama_ready.model,
            "--base-url",
            ollama_ready.base_url,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "Generated examples for" in result.stderr
