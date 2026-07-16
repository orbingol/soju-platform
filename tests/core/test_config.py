# SPDX-License-Identifier: BSD-3-Clause
"""Data-root and schema-relative path helpers."""

from __future__ import annotations

from pathlib import Path

from soju.core import config


def test_data_root_override(data_root: Path) -> None:
    assert config.data_root(data_root) == data_root


def test_data_root_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert config.data_root() == tmp_path


def test_data_root_default_cwd(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    assert config.data_root() == tmp_path / "data"


def test_content_and_staging_roots(data_root: Path) -> None:
    assert config.content_root(data_root) == data_root / "content"
    assert config.staging_root(data_root) == data_root / "staging"


def test_schema_rel_for_registry_depth(data_root: Path) -> None:
    path = data_root / "content" / "registry" / "vocabulary.yaml"
    rel = config.schema_rel_for(path, "registry_vocabulary.schema.json", data_root)
    assert rel == "../../schemas/registry_vocabulary.schema.json"


def test_schema_rel_for_staging_depth(data_root: Path) -> None:
    path = data_root / "staging" / "vocabulary-candidates.yaml"
    rel = config.schema_rel_for(path, "staging_vocabulary.schema.json", data_root)
    assert rel == "../schemas/staging_vocabulary.schema.json"
