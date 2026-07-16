# SPDX-License-Identifier: BSD-3-Clause
"""Promote local topic entries on a fixture tree."""

from __future__ import annotations

from pathlib import Path

from soju.services.promote import promote_topic
from tests.constants import WORD_ID
from soju.registry.topics import load_topic, save_topic
from soju.registry.vocabulary import vocabulary_by_id


def test_promote_topic_converts_local_to_ref(data_root: Path) -> None:
    topic = load_topic("family", data_root)
    local_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    topic["sections"][0]["entries"].append(
        {
            "id": local_id,
            "local": True,
            "hangul": "친구",
            "romanization": "chin-gu",
            "english": "friend",
            "type": "noun",
        }
    )
    save_topic("family", topic, data_root)

    counts = promote_topic("family", root=data_root)
    assert counts["promoted"] == 1
    vocab = vocabulary_by_id(data_root)
    assert local_id in vocab
    topic = load_topic("family", data_root)
    assert {"ref": local_id} in topic["sections"][0]["entries"]


def test_promote_skips_existing_sense(data_root: Path) -> None:
    topic = load_topic("family", data_root)
    topic["sections"][0]["entries"].append(
        {
            "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
            "local": True,
            "hangul": "학교",
            "romanization": "hak-gyo",
            "english": "school",
            "type": "noun",
        }
    )
    save_topic("family", topic, data_root)

    counts = promote_topic("family", root=data_root)
    assert counts["skipped"] == 1
    assert counts["promoted"] == 0
    topic = load_topic("family", data_root)
    assert {"ref": WORD_ID} in topic["sections"][0]["entries"]
