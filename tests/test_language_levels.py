# SPDX-License-Identifier: BSD-3-Clause
"""Language levels config loading under content/."""

from __future__ import annotations

from pathlib import Path

from soju.language_levels import default_level_id, load_levels_config, vocabulary_for_level
from tests.constants import WORD_ID


def test_loads_from_content_levels_yaml(data_root: Path) -> None:
    assert default_level_id(data_root) == "1A"
    config = load_levels_config(data_root)
    assert "1A" in config["levels"]


def test_missing_levels_raises(tmp_path: Path) -> None:
    try:
        default_level_id(tmp_path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Missing levels config" in str(exc)


def test_vocabulary_for_level_filters(data_root: Path) -> None:
    # Untagged entries belong to the default level.
    entries = vocabulary_for_level("1A", data_root)
    ids = {e["id"] for e in entries}
    assert WORD_ID in ids


def test_vocabulary_for_level_empty_when_no_matches(data_root: Path) -> None:
    import yaml

    levels = data_root / "content" / "levels.yaml"
    levels.write_text(
        yaml.safe_dump(
            {
                "default": "1A",
                "levels": {
                    "1A": {"label": "1A", "guidance": "x"},
                    "2A": {"label": "2A", "guidance": "y"},
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    # All fixture vocabulary is untagged → belongs to default 1A only.
    assert vocabulary_for_level("2A", data_root) == []
