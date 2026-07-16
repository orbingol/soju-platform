# SPDX-License-Identifier: BSD-3-Clause
"""Offline system tests: CLI pipelines on a temp data tree (no Ollama)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from soju.cli.app import app as soju_app
from soju.cli import examples as examples_cli
from soju.cli import promote as promote_cli
from soju.cli import validate as validate_cli
from soju.cli import verbs as verbs_cli
from soju.cli import words as words_cli
from soju.registry.topics import load_topic, save_topic
from soju.registry.vocabulary import load_vocabulary, vocabulary_by_id
from soju.services.validation.alignment import validate_alignment
from soju.services.validation.registry_checks import validate_registry
from soju.services.validation.schemas import validate_schemas
from soju.core.yaml_io import load_yaml
from soju.registry.verbs import verb_table_path
from soju.registry.vocabulary import vocabulary_by_type

pytestmark = pytest.mark.system

runner = CliRunner()

LOCAL_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
NEW_VERB_PAYLOAD = {
    "hangul": "가다",
    "romanization": "ga-da",
    "english": "to go",
    "forms": {
        "present": {"casual_polite": "가요", "formal_polite": "갑니다"},
        "past": {"casual_polite": "갔어요", "formal_polite": "갔습니다"},
        "future": {"casual_polite": "갈 거예요", "formal_polite": "가겠습니다"},
    },
}


def test_import_promote_validate_pipeline(data_env: Path) -> None:
    """Import words → promote local → validators all succeed on the temp tree."""
    word_payload = json.dumps(
        [
            {
                "hangul": "책",
                "romanization": "chaek",
                "english": "book",
                "examples": [{"hangul": "책이 있어요.", "english": "There is a book."}],
            }
        ],
        ensure_ascii=False,
    )
    result = runner.invoke(
        words_cli.app,
        ["words", "--topic", "family", "--section", "general", "--stdin-json"],
        input=word_payload,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "added=1" in result.stdout

    topic = load_topic("family", data_env)
    topic["sections"][0]["entries"].append(
        {
            "id": LOCAL_ID,
            "local": True,
            "hangul": "친구",
            "romanization": "chin-gu",
            "english": "friend",
            "type": "noun",
            "examples": [{"hangul": "친구가 있어요.", "english": "I have a friend."}],
        }
    )
    save_topic("family", topic, data_env)

    result = runner.invoke(promote_cli.app, ["--topic", "family"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "promoted 1 entries" in result.stdout
    assert LOCAL_ID in vocabulary_by_id(data_env)
    topic = load_topic("family", data_env)
    assert {"ref": LOCAL_ID} in topic["sections"][0]["entries"]

    result = runner.invoke(validate_cli.registry_app, [], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "Registry validation OK."

    result = runner.invoke(validate_cli.align_app, [], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "Verb data alignment OK."

    result = runner.invoke(validate_cli.schemas_app, [], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "Schema validation passed."

    # Double-check service APIs agree with CLI (same DATA_DIR).
    assert validate_registry() == []
    assert validate_schemas() == []
    table = load_yaml(verb_table_path())
    assert validate_alignment(table, vocabulary_by_type("verb")) == []


def test_import_verbs_fill_verbs_and_local_examples(data_env: Path) -> None:
    """Import a verb → fill-verbs → fill-examples --local writes examples."""
    payload = json.dumps([NEW_VERB_PAYLOAD], ensure_ascii=False)
    result = runner.invoke(
        words_cli.app,
        ["verbs", "--stdin-json"],
        input=payload,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "added=1" in result.stdout

    result = runner.invoke(verbs_cli.app, ["--fill-empty"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "filled forms/examples" in result.stdout

    result = runner.invoke(
        examples_cli.app,
        ["--local", "--mode", "refresh-all", "--examples", "1"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "Generated examples for" in result.stderr

    hanguls = {e["hangul"] for e in load_vocabulary(data_env)}
    assert "가다" in hanguls


def test_unified_soju_cli_import_and_registry(data_env: Path) -> None:
    """Unified ``soju`` entry mounts import + registry against DATA_DIR."""
    payload = json.dumps(
        [{"hangul": "물", "romanization": "mul", "english": "water"}],
        ensure_ascii=False,
    )
    result = runner.invoke(
        soju_app,
        ["import", "words", "--topic", "family", "--section", "general", "--stdin-json"],
        input=payload,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "added=1" in result.stdout

    result = runner.invoke(soju_app, ["registry"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Registry validation OK." in result.stdout
