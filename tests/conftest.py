# SPDX-License-Identifier: BSD-3-Clause
"""Shared fixtures for Soju Python tests (content/ + staging/ layout)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from tests.constants import VERB_ID, WORD_ID


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register optional flags used by system / LLM tests."""
    parser.addoption(
        "--llm",
        action="store_true",
        default=False,
        help="Run @pytest.mark.llm tests (requires a reachable Ollama).",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip LLM tests unless ``--llm`` or ``SOJU_RUN_LLM_TESTS=1`` is set."""
    run_llm = config.getoption("--llm") or os.environ.get("SOJU_RUN_LLM_TESTS", "").strip() in {
        "1",
        "true",
        "yes",
    }
    if run_llm:
        return
    skip_llm = pytest.mark.skip(reason="needs --llm or SOJU_RUN_LLM_TESTS=1")
    for item in items:
        if item.get_closest_marker("llm") is not None:
            item.add_marker(skip_llm)


@pytest.fixture
def data_env(data_root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``DATA_DIR`` at the fixture tree for in-process CLI / service calls."""
    monkeypatch.setenv("DATA_DIR", str(data_root))
    return data_root


def _dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    """Minimal valid data tree under tmp_path (pass as db root)."""
    content = tmp_path / "content"
    staging = tmp_path / "staging"

    _dump(
        content / "registry" / "types.yaml",
        {
            "types": [
                {"id": "noun", "slug": "nouns", "label": "Noun"},
                {"id": "verb", "slug": "verbs", "label": "Verb"},
                {"id": "phrase", "slug": "phrases", "label": "Phrase"},
            ]
        },
    )
    _dump(
        content / "registry" / "vocabulary.yaml",
        [
            {
                "id": WORD_ID,
                "hangul": "학교",
                "romanization": "hak-gyo",
                "english": "school",
                "type": "noun",
            },
            {
                "id": VERB_ID,
                "hangul": "먹다",
                "romanization": "meok-da",
                "english": "to eat",
                "type": "verb",
            },
        ],
    )
    _dump(
        content / "registry" / "examples.yaml",
        {
            WORD_ID: {
                "default": [
                    {"hangul": "학교에 가요.", "english": "I go to school."},
                ]
            }
        },
    )
    _dump(
        content / "words" / "table.yaml",
        {
            "fields": {
                "hangul": {"label": "Word"},
                "romanization": {"label": "Romanization"},
                "english": {"label": "English"},
            },
            "examples": {"label": "Examples"},
        },
    )
    _dump(
        content / "topics" / "manifest.yaml",
        {
            "topics": {
                "family": {"label": "Family", "description": "Family words"},
            }
        },
    )
    _dump(
        content / "topics" / "table.yaml",
        {
            "fields": {
                "hangul": {"label": "Word"},
                "romanization": {"label": "Romanization"},
                "english": {"label": "English"},
            },
            "examples": {"label": "Examples"},
        },
    )
    _dump(
        content / "topics" / "family" / "topic.yaml",
        {
            "sections": [
                {
                    "id": "general",
                    "label": "General",
                    "entries": [{"ref": WORD_ID}],
                }
            ]
        },
    )
    _dump(
        content / "verbs" / "manifest.yaml",
        {
            "table": "table.yaml",
            "forms": {
                "present": "forms/present.yaml",
                "past": "forms/past.yaml",
                "future": "forms/future.yaml",
            },
            "constructions": {},
        },
    )
    _dump(
        content / "verbs" / "table.yaml",
        {
            "fields": {
                "hangul": {"label": "Dictionary form"},
                "romanization": {"label": "Romanization"},
                "english": {"label": "Meaning"},
            },
            "sections": [
                {
                    "id": "present",
                    "label": "Present",
                    "css": "pres",
                    "columns": [
                        {
                            "variant": "casual_polite",
                            "label": "Casual Polite",
                            "subtitle": "해요",
                        },
                        {
                            "variant": "formal_polite",
                            "label": "Formal Polite",
                            "subtitle": "합니다",
                        },
                    ],
                },
                {
                    "id": "past",
                    "label": "Past",
                    "css": "past",
                    "columns": [
                        {
                            "variant": "casual_polite",
                            "label": "Casual Polite",
                            "subtitle": "했어요",
                        },
                        {
                            "variant": "formal_polite",
                            "label": "Formal Polite",
                            "subtitle": "했습니다",
                        },
                    ],
                },
                {
                    "id": "future",
                    "label": "Future",
                    "css": "fut",
                    "columns": [
                        {
                            "variant": "casual_polite",
                            "label": "Casual Polite",
                            "subtitle": "할 거예요",
                        },
                        {
                            "variant": "formal_polite",
                            "label": "Formal Polite",
                            "subtitle": "하겠습니다",
                        },
                    ],
                },
            ],
        },
    )
    for tense, casual, formal in (
        ("present", "먹어요", "먹습니다"),
        ("past", "먹었어요", "먹었습니다"),
        ("future", "먹을 거예요", "먹겠습니다"),
    ):
        _dump(
            content / "verbs" / "forms" / f"{tense}.yaml",
            {
                VERB_ID: {
                    "casual_polite": casual,
                    "formal_polite": formal,
                }
            },
        )
    _dump(
        content / "levels.yaml",
        {
            "default": "1A",
            "levels": {
                "1A": {
                    "label": "Korean 1A",
                    "description": "Beginner",
                    "guidance": "Keep it simple.",
                },
                "1B": {
                    "label": "Korean 1B",
                    "description": "High beginner",
                    "guidance": "Slightly richer sentences.",
                },
            },
        },
    )
    _dump(
        content / "grammar" / "manifest.yaml",
        {
            "patterns": {
                "do": {
                    "path": "patterns/do.yaml",
                    "label": "도",
                    "form": "-도",
                    "english": "also / even",
                    "category": "particles",
                    "description": "Additive particle.",
                }
            }
        },
    )
    _dump(
        content / "grammar" / "patterns" / "do.yaml",
        {
            "id": "do",
            "form": "-도",
            "romanization": "do",
            "english": "also / even",
            "category": "particles",
            "summary": "Additive particle: also/too, or even.",
            "sections": [
                {
                    "id": "also",
                    "label": "Also / too",
                    "examples": [
                        {"hangul": "저도 학생이에요.", "english": "I am also a student."},
                    ],
                }
            ],
        },
    )
    _dump(staging / "vocabulary-candidates.yaml", {"staging": True, "entries": []})
    (staging / "exercises").mkdir(parents=True, exist_ok=True)
    (staging / "stories").mkdir(parents=True, exist_ok=True)
    return tmp_path
