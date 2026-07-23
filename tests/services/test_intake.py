# SPDX-License-Identifier: BSD-3-Clause
"""Import session round-trips on a fixture tree."""

from __future__ import annotations

from pathlib import Path

from soju.services.intake import ImportReport, ImportSession, import_verb_record, import_word_record
from tests.constants import WORD_ID
from soju.registry.examples import load_examples_store
from soju.registry.topics import load_topic, save_topic
from soju.registry.verbs import load_verb_forms_file
from soju.registry.vocabulary import load_vocabulary


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
    vocab = load_vocabulary(data_root)
    assert any(e["hangul"] == "책" for e in vocab)
    topic = load_topic("family", data_root)
    refs = [e.get("ref") for e in topic["sections"][0]["entries"]]
    assert any(r and r != WORD_ID for r in refs)
    store = load_examples_store(data_root)
    new_id = next(e["id"] for e in vocab if e["hangul"] == "책")
    assert store[new_id]["default"]


def test_import_existing_sense_merges_examples_and_add_ref(data_root: Path) -> None:
    # Clear the existing topic ref so add_ref can fire.
    topic = load_topic("family", data_root)
    topic["sections"][0]["entries"] = []
    save_topic("family", topic, data_root)

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


def test_import_word_record_with_level(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {
            "hangul": "책",
            "romanization": "chaek",
            "english": "book",
            "level": "1B",
        },
        session,
        report,
        section_id="general",
    )
    session.commit(dry_run=False)
    entry = next(e for e in load_vocabulary(data_root) if e["hangul"] == "책")
    assert entry["level"] == "1B"


def test_import_word_record_cli_level_default(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {"hangul": "펜", "romanization": "pen", "english": "pen"},
        session,
        report,
        section_id="general",
        level_id="1A",
    )
    session.commit(dry_run=False)
    entry = next(e for e in load_vocabulary(data_root) if e["hangul"] == "펜")
    assert entry["level"] == "1A"


def test_import_word_record_omits_level_when_unassigned(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {"hangul": "컵", "romanization": "keop", "english": "cup"},
        session,
        report,
        section_id="general",
    )
    session.commit(dry_run=False)
    entry = next(e for e in load_vocabulary(data_root) if e["hangul"] == "컵")
    assert "level" not in entry


def test_import_word_record_unknown_level_errors(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {"hangul": "책", "romanization": "chaek", "english": "book", "level": "9Z"},
        session,
        report,
        section_id="general",
    )
    assert report.added == 0
    assert report.skipped == 1
    assert any("Unknown language level" in e for e in report.errors)


def test_import_existing_sense_updates_level(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {"hangul": "학교", "romanization": "hak-gyo", "english": "school"},
        session,
        report,
        section_id="general",
        level_id="1B",
    )
    session.commit(dry_run=False)
    entry = next(e for e in load_vocabulary(data_root) if e["id"] == WORD_ID)
    assert entry["level"] == "1B"


def test_import_verb_record_with_level(data_root: Path) -> None:
    session = ImportSession.open_verbs(data_root)
    report = ImportReport()
    import_verb_record(
        {
            "hangul": "가다",
            "romanization": "ga-da",
            "english": "to go",
            "level": "1B",
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
    entry = next(e for e in load_vocabulary(data_root) if e["hangul"] == "가다")
    assert entry["level"] == "1B"


def test_resolve_topic_section_requires_section(data_root: Path) -> None:
    from soju.services.intake import resolve_topic_section

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
    forms = load_verb_forms_file("present", data_root)
    new_id = next(e["id"] for e in load_vocabulary(data_root) if e["hangul"] == "가다")
    assert forms[new_id]["casual_polite"] == "가요"


def test_import_verb_duplicate_errors(data_root: Path) -> None:
    session = ImportSession.open_verbs(data_root)
    report = ImportReport()
    import_verb_record(
        {
            "hangul": "먹다",
            "romanization": "meok-da",
            "english": "to eat",
            "forms": {
                "present": {"casual_polite": "먹어요", "formal_polite": "먹습니다"},
                "past": {"casual_polite": "먹었어요", "formal_polite": "먹었습니다"},
                "future": {"casual_polite": "먹을 거예요", "formal_polite": "먹겠습니다"},
            },
        },
        session,
        report,
    )
    assert report.skipped == 1
    assert any("already exists" in e for e in report.errors)


def test_import_words_from_lines_merges_existing(data_root: Path) -> None:
    from soju.services.intake import import_words_from_lines

    topic = load_topic("family", data_root)
    topic["sections"][0]["entries"] = []
    save_topic("family", topic, data_root)

    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    # Parenthetical hangul example for an existing registry word.
    import_words_from_lines(
        ["학교 (큰 학교예요.)"],
        session,
        report,
        section_id="general",
    )
    session.commit(dry_run=False)
    assert report.add_ref == 1
    assert report.merged_examples >= 1 or report.skipped == 0


def test_import_words_from_lines_rejects_new_without_json(data_root: Path) -> None:
    from soju.services.intake import import_words_from_lines

    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_words_from_lines(["새단어"], session, report, section_id="general")
    assert report.skipped >= 1
    assert report.errors


def test_import_words_from_staging(data_root: Path, tmp_path: Path) -> None:
    from soju.services.intake import import_words_from_staging

    staging = tmp_path / "candidates.yaml"
    staging.write_text(
        "staging: true\nentries:\n  - id: eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee\n    hangul: 물\n    romanization: mul\n    english: water\n    type: noun\n",
        encoding="utf-8",
    )
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_words_from_staging(staging, session, report, section_id="general")
    session.commit(dry_run=False)
    assert report.added == 1
    assert any(e["hangul"] == "물" for e in load_vocabulary(data_root))


def test_import_words_from_staging_generates_romanization(data_root: Path, tmp_path: Path) -> None:
    from soju.services.intake import import_words_from_staging

    staging = tmp_path / "candidates.yaml"
    # Practice / staging candidates are hangul + english only.
    staging.write_text(
        "staging: true\nentries:\n  - id: ffffffff-ffff-ffff-ffff-ffffffffffff\n    hangul: 메뉴\n    english: menu\n    type: noun\n",
        encoding="utf-8",
    )
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_words_from_staging(staging, session, report, section_id="general")
    session.commit(dry_run=False)
    assert report.added == 1
    entry = next(e for e in load_vocabulary(data_root) if e["hangul"] == "메뉴")
    assert entry["romanization"] == "me-nyu"
    assert entry["english"] == "menu"


def test_import_word_record_autofills_romanization(data_root: Path) -> None:
    session = ImportSession.open_words("family", data_root)
    report = ImportReport()
    import_word_record(
        {"hangul": "학교", "english": "academy building"},
        session,
        report,
        section_id="general",
    )
    session.commit(dry_run=False)
    assert report.added == 1
    entry = next(e for e in load_vocabulary(data_root) if e["english"] == "academy building")
    assert entry["romanization"] == "hak-gyo"


def test_load_records_json_variants(tmp_path: Path, monkeypatch) -> None:
    from soju.services.intake import load_records_json

    path = tmp_path / "recs.json"
    path.write_text('{"records":[{"hangul":"책"}]}', encoding="utf-8")
    assert len(load_records_json(False, path)) == 1

    path.write_text('[{"hangul":"책"}]', encoding="utf-8")
    assert len(load_records_json(False, path)) == 1

    path.write_text('{"nope": true}', encoding="utf-8")
    try:
        load_records_json(False, path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "records" in str(exc).lower() or "list" in str(exc).lower()
