# SPDX-License-Identifier: BSD-3-Clause
"""Import session and promote round-trips on a fixture tree."""

from __future__ import annotations

from pathlib import Path

from soju import db
from soju.import_ import ImportReport, ImportSession, import_verb_record, import_word_record
from soju.promote import promote_topic
from tests.constants import WORD_ID


def test_import_word_record_adds_and_refs(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {
            "hangul": "책",
            "romanization": "chaek",
            "english": "book",
            "examples": [{"hangul": "책이 있어요.", "english": "There is a book."}],
        },
        session,
        report,
        section_id="general",
    )
    session.commit(dry_run=False)
    assert report.added == 1
    vocab = db.load_vocabulary(data_root)
    assert any(e["hangul"] == "책" for e in vocab)
    topic = db.load_topic("family", data_root)
    refs = [e.get("ref") for e in topic["sections"][0]["entries"]]
    assert any(r and r != WORD_ID for r in refs)
    store = db.load_examples_store(data_root)
    new_id = next(e["id"] for e in vocab if e["hangul"] == "책")
    assert store[new_id]["default"]


def test_import_existing_sense_merges_examples_and_add_ref(data_root: Path) -> None:
    # Clear the existing topic ref so add_ref can fire.
    topic = db.load_topic("family", data_root)
    topic["sections"][0]["entries"] = []
    db.save_topic("family", topic, data_root)

    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {
            "hangul": "학교",
            "romanization": "hak-gyo",
            "english": "school",
            "examples": [{"hangul": "큰 학교예요.", "english": "It is a big school."}],
        },
        session,
        report,
        section_id="general",
    )
    session.commit(dry_run=False)
    assert report.merged_examples == 1
    assert report.add_ref == 1
    assert report.added == 0


def test_import_missing_fields_errors(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record({"hangul": "책"}, session, report, section_id="general")
    assert report.errors
    assert report.skipped == 1


def test_resolve_topic_section_requires_section(data_root: Path) -> None:
    from soju.import_ import resolve_topic_section

    topic = {
        "sections": [
            {"id": "a", "label": "A", "entries": []},
            {"id": "b", "label": "B", "entries": []},
        ]
    }
    try:
        resolve_topic_section(topic, None)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "section" in str(exc).lower()


def test_import_verb_record(data_root: Path) -> None:
    session = ImportSession.open_verbs(data_root)
    report = ImportReport()
    import_verb_record(
        {
            "hangul": "가다",
            "romanization": "ga-da",
            "english": "to go",
            "forms": {
                "present": {"casual_polite": "가요", "formal_polite": "갑니다"},
                "past": {"casual_polite": "갔어요", "formal_polite": "갔습니다"},
                "future": {"casual_polite": "갈 거예요", "formal_polite": "가겠습니다"},
            },
        },
        session,
        report,
    )
    session.commit(dry_run=False)
    assert report.added == 1
    forms = db.load_verb_forms_file("present", data_root)
    new_id = next(e["id"] for e in db.load_vocabulary(data_root) if e["hangul"] == "가다")
    assert forms[new_id]["casual_polite"] == "가요"


def test_promote_topic_converts_local_to_ref(data_root: Path) -> None:
    topic = db.load_topic("family", data_root)
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
    db.save_topic("family", topic, data_root)

    counts = promote_topic("family", root=data_root)
    assert counts["promoted"] == 1
    vocab = db.vocabulary_by_id(data_root)
    assert local_id in vocab
    topic = db.load_topic("family", data_root)
    assert {"ref": local_id} in topic["sections"][0]["entries"]


def test_promote_skips_existing_sense(data_root: Path) -> None:
    topic = db.load_topic("family", data_root)
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
    db.save_topic("family", topic, data_root)

    counts = promote_topic("family", root=data_root)
    assert counts["skipped"] == 1
    assert counts["promoted"] == 0
    topic = db.load_topic("family", data_root)
    assert {"ref": WORD_ID} in topic["sections"][0]["entries"]
