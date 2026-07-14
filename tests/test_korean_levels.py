# SPDX-License-Identifier: BSD-3-Clause
"""Korean levels config loading under content/."""

from __future__ import annotations

from pathlib import Path

from soju.korean_levels import default_level_id, load_levels_config, vocabulary_for_level
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
