# SPDX-License-Identifier: BSD-3-Clause
"""Registry path and examples-merge smoke tests."""

from __future__ import annotations

from pathlib import Path

from soju.registry.examples import merge_default_examples
from soju.registry.targets import glob_validate_targets
from soju.registry.topics import topic_path
from soju.registry.verbs import verb_forms_path
from soju.services.keys import example_key
from tests.constants import WORD_ID


def test_topic_path_derive_by_id(data_root: Path) -> None:
    path = topic_path("family", data_root)
    assert path == data_root / "content" / "topics" / "family" / "topic.yaml"


def test_topic_path_unknown_raises(data_root: Path) -> None:
    try:
        topic_path("missing", data_root)
        raise AssertionError("expected KeyError")
    except KeyError as exc:
        assert "missing" in str(exc)


def test_verb_forms_path(data_root: Path) -> None:
    path = verb_forms_path("present", data_root)
    assert path == data_root / "content" / "verbs" / "forms" / "present.yaml"


def test_glob_validate_targets_layout(data_root: Path) -> None:
    targets = glob_validate_targets(data_root)
    assert "registry-vocabulary" in targets
    assert "verb-forms" in targets
    assert "staging-vocabulary" in targets
    for key, files in targets.items():
        if not files:
            continue
        for file_path in files:
            if key.startswith("staging-"):
                assert "/staging/" in file_path.replace("\\", "/")
                assert "/content/staging/" not in file_path.replace("\\", "/")
            else:
                assert "/content/" in file_path.replace("\\", "/")


def test_merge_default_examples_dedupes(data_root: Path) -> None:
    merged = merge_default_examples(
        WORD_ID,
        [{"hangul": "학교에 가요.", "english": "I go to school."}],
        data_root,
        example_key=example_key,
    )
    assert merged == 0
    merged = merge_default_examples(
        WORD_ID,
        [{"hangul": "좋은 학교예요.", "english": "It is a good school."}],
        data_root,
        example_key=example_key,
    )
    assert merged == 1
