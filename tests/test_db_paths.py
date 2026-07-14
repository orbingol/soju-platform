# SPDX-License-Identifier: BSD-3-Clause
"""Path helpers and content layout contracts."""

from __future__ import annotations

from pathlib import Path

from soju import db
from tests.constants import WORD_ID


def test_data_root_override(data_root: Path) -> None:
    assert db.data_root(data_root) == data_root


def test_data_root_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert db.data_root() == tmp_path


def test_data_root_default_cwd(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    assert db.data_root() == tmp_path / "data"


def test_content_and_staging_roots(data_root: Path) -> None:
    assert db.content_root(data_root) == data_root / "content"
    assert db.staging_root(data_root) == data_root / "staging"


def test_schema_rel_for_registry_depth(data_root: Path) -> None:
    path = data_root / "content" / "registry" / "vocabulary.yaml"
    rel = db.schema_rel_for(path, "registry_vocabulary.schema.json", data_root)
    assert rel == "../../schemas/registry_vocabulary.schema.json"


def test_schema_rel_for_staging_depth(data_root: Path) -> None:
    path = data_root / "staging" / "vocabulary-candidates.yaml"
    rel = db.schema_rel_for(path, "staging_vocabulary.schema.json", data_root)
    assert rel == "../schemas/staging_vocabulary.schema.json"


def test_topic_path_derive_by_id(data_root: Path) -> None:
    path = db.topic_path("family", data_root)
    assert path == data_root / "content" / "topics" / "family" / "topic.yaml"


def test_topic_path_unknown_raises(data_root: Path) -> None:
    try:
        db.topic_path("missing", data_root)
        raise AssertionError("expected KeyError")
    except KeyError as exc:
        assert "missing" in str(exc)


def test_verb_forms_path(data_root: Path) -> None:
    path = db.verb_forms_path("present", data_root)
    assert path == data_root / "content" / "verbs" / "forms" / "present.yaml"


def test_glob_validate_targets_layout(data_root: Path) -> None:
    targets = db.glob_validate_targets(data_root)
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


def test_normalize_english_gloss_proper_names() -> None:
    assert db.normalize_english_gloss("south korea") == "South Korea"
    assert db.normalize_english_gloss("a book") == "a book"


def test_sense_key_and_parse_import_line() -> None:
    key = db.sense_key("학교", "school")
    assert key[0] == "학교"
    assert key[1] == "school"
    parsed = db.parse_import_line("학교 (I go to school)")
    assert parsed is not None
    entry, example = parsed
    assert entry == "학교"
    assert example == "I go to school"
    assert db.parse_import_line("# comment") is None


def test_merge_default_examples_dedupes(data_root: Path) -> None:
    merged = db.merge_default_examples(
        WORD_ID,
        [{"hangul": "학교에 가요.", "english": "I go to school."}],
        data_root,
    )
    assert merged == 0
    merged = db.merge_default_examples(
        WORD_ID,
        [{"hangul": "좋은 학교예요.", "english": "It is a good school."}],
        data_root,
    )
    assert merged == 1
