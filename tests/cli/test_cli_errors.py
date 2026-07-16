# SPDX-License-Identifier: BSD-3-Clause
"""CLI error / usage paths via in-process Typer CliRunner (counts toward coverage)."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from soju.cli import examples as examples_cli
from soju.cli import promote as promote_cli
from soju.cli import translate as translate_cli
from soju.cli import validate as validate_cli
from soju.cli import words as words_cli
from soju.registry.vocabulary import load_vocabulary, save_vocabulary

runner = CliRunner()


def test_import_words_requires_input(data_env: Path) -> None:
    result = runner.invoke(
        words_cli.app,
        ["words", "--topic", "family", "--section", "general"],
        catch_exceptions=False,
    )
    assert result.exit_code == 2
    assert "Provide --file" in result.output or "Provide --file" in result.stderr


def test_import_verbs_requires_stdin_json(data_env: Path) -> None:
    result = runner.invoke(words_cli.app, ["verbs"], catch_exceptions=False)
    assert result.exit_code == 2


def test_promote_unknown_topic(data_env: Path) -> None:
    result = runner.invoke(promote_cli.app, ["--topic", "nope"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "Error:" in result.output or "Error:" in result.stderr


def test_translate_missing_file(data_env: Path, tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    result = runner.invoke(
        translate_cli.app,
        ["--file", str(missing)],
        catch_exceptions=False,
    )
    assert result.exit_code == 2
    assert "not found" in result.output.lower() or "not found" in result.stderr.lower()


def test_translate_ollama_unreachable(data_env: Path, tmp_path: Path, monkeypatch) -> None:
    word_list = tmp_path / "words.txt"
    word_list.write_text("사과\n", encoding="utf-8")

    class _Down:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def check_available(self) -> bool:
            return False

    monkeypatch.setattr(translate_cli, "OllamaClient", _Down)
    result = runner.invoke(
        translate_cli.app,
        ["--file", str(word_list)],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "Ollama" in result.output or "Ollama" in result.stderr


def test_fill_examples_rejects_bad_examples_count(data_env: Path) -> None:
    result = runner.invoke(
        examples_cli.app,
        ["--examples", "0", "--local"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "examples" in result.output.lower() or "examples" in result.stderr.lower()


def test_fill_examples_ollama_unreachable(data_env: Path, monkeypatch) -> None:
    class _Down:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def check_available(self) -> bool:
            return False

    monkeypatch.setattr(examples_cli, "OllamaClient", _Down)
    result = runner.invoke(
        examples_cli.app,
        ["--nouns-only", "--limit", "1"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "Ollama" in result.output or "Ollama" in result.stderr


def test_registry_validation_failure(data_env: Path) -> None:
    vocab = load_vocabulary(data_env)
    vocab.append(dict(vocab[0]))  # duplicate id
    save_vocabulary(vocab, data_env)
    result = runner.invoke(validate_cli.registry_app, [], catch_exceptions=False)
    assert result.exit_code == 1
    assert "Duplicate" in result.output or "Duplicate" in result.stderr


def test_align_validation_failure(data_env: Path) -> None:
    # Drop verb forms so alignment fails.
    forms_path = data_env / "content" / "verbs" / "forms" / "present.yaml"
    forms_path.write_text("{}\n", encoding="utf-8")
    result = runner.invoke(validate_cli.align_app, [], catch_exceptions=False)
    assert result.exit_code == 1
    assert "alignment" in result.output.lower() or "alignment" in result.stderr.lower() or "missing" in (result.output + result.stderr).lower()


def test_schemas_validation_failure(data_env: Path) -> None:
    # Empty patterns object fails grammar_manifest schema (minProperties: 1).
    manifest = data_env / "content" / "grammar" / "manifest.yaml"
    manifest.write_text(yaml.safe_dump({"patterns": {}}), encoding="utf-8")
    result = runner.invoke(validate_cli.schemas_app, [], catch_exceptions=False)
    assert result.exit_code == 1
    assert "Schema" in result.output or "Schema" in result.stderr or "failed" in (result.output + result.stderr).lower()
