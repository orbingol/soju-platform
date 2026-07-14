# SPDX-License-Identifier: BSD-3-Clause
"""Canonical merge/write CLI for Soju vocabulary data."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from soju import db


@dataclass
class ImportReport:
    added: int = 0
    merged_examples: int = 0
    add_ref: int = 0
    skipped: int = 0
    homonyms: int = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [
            f"added={self.added}",
            f"merged_examples={self.merged_examples}",
            f"add_ref={self.add_ref}",
            f"skipped={self.skipped}",
            f"errors={len(self.errors)}",
        ]
        if self.homonyms:
            parts.append(f"homonyms={self.homonyms}")
        return " ".join(parts)


@dataclass
class ImportSession:
    """In-memory import state: load once, mutate, write once."""

    root: Path | None
    vocabulary: list[dict]
    by_sense: dict[tuple[str, str], dict]
    examples: dict
    topic_id: str | None = None
    topic: dict | None = None
    forms_by_tense: dict[str, dict] = field(default_factory=dict)
    vocab_dirty: bool = False
    examples_dirty: bool = False
    topic_dirty: bool = False
    forms_dirty: set[str] = field(default_factory=set)

    @classmethod
    def open_words(cls, topic_id: str, root=None) -> ImportSession:
        vocabulary = db.load_vocabulary(root)
        return cls(
            root=root,
            vocabulary=vocabulary,
            by_sense=db.build_sense_index(vocabulary),
            examples=db.load_examples_store(root),
            topic_id=topic_id,
            topic=db.load_topic(topic_id, root),
        )

    @classmethod
    def open_verbs(cls, root=None) -> ImportSession:
        vocabulary = db.load_vocabulary(root)
        return cls(
            root=root,
            vocabulary=vocabulary,
            by_sense=db.build_sense_index(vocabulary),
            examples=db.load_examples_store(root),
            forms_by_tense=db.load_all_verb_forms(root),
        )

    def commit(self, *, dry_run: bool) -> None:
        if dry_run:
            return
        if self.vocab_dirty:
            db.save_vocabulary(self.vocabulary, self.root)
        if self.examples_dirty:
            db.save_examples_store(self.examples, self.root)
        if self.topic_dirty and self.topic_id is not None and self.topic is not None:
            db.save_topic(self.topic_id, self.topic, self.root)
        for tense in sorted(self.forms_dirty):
            db.save_verb_forms_file(tense, self.forms_by_tense[tense], self.root)


def load_records_json(stdin: bool, path: Path | None) -> list[dict]:
    if stdin:
        payload = json.load(sys.stdin)
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "records" in payload:
        return payload["records"]
    if isinstance(payload, list):
        return payload
    raise ValueError("JSON input must be a list or an object with 'records'.")


def resolve_topic_section(topic: dict, section_id: str | None) -> dict:
    sections = topic.get("sections", [])
    if not sections:
        raise ValueError("Topic has no sections.")
    if section_id:
        section = db.find_section(topic, section_id)
        if section is None:
            raise ValueError(f"Unknown section id: {section_id}")
        return section
    if len(sections) == 1:
        return sections[0]
    raise ValueError("Topic has multiple sections; pass --section <id>.")


def import_word_record(
    record: dict,
    session: ImportSession,
    report: ImportReport,
    *,
    section_id: str | None = None,
    dry_run: bool = False,
) -> None:
    required = {"hangul", "romanization", "english"}
    if not required.issubset(record):
        report.errors.append(f"Word record missing fields: {sorted(required - set(record))}")
        report.skipped += 1
        return

    assert session.topic is not None
    try:
        section = resolve_topic_section(session.topic, section_id)
    except ValueError as exc:
        report.errors.append(str(exc))
        report.skipped += 1
        return

    sense = db.sense_key(record["hangul"], record["english"])
    examples = record.get("examples", [])
    english = db.normalize_english_gloss(record["english"])

    local = db.find_local_entry(session.topic, record["hangul"], english)
    if local:
        if examples and not dry_run:
            merged = db.merge_default_examples(local["id"], examples, session.root, store=session.examples)
            if merged:
                session.examples_dirty = True
        else:
            merged = len(examples) if examples else 0
        if merged:
            report.merged_examples += merged
        else:
            report.skipped += 1
        return

    if sense in session.by_sense:
        entry = session.by_sense[sense]
        if examples:
            if not dry_run:
                merged = db.merge_default_examples(entry["id"], examples, session.root, store=session.examples)
                if merged:
                    session.examples_dirty = True
            else:
                merged = len(examples)
            if merged:
                report.merged_examples += merged
        if not db.topic_has_ref(session.topic, entry["id"]):
            if not dry_run:
                section.setdefault("entries", []).append({"ref": entry["id"]})
                session.topic_dirty = True
            report.add_ref += 1
        else:
            report.skipped += 1
        return

    homonym_entries = db.entries_for_hangul(session.vocabulary, record["hangul"])
    if homonym_entries:
        existing = ", ".join(f"{e['english']}" for e in homonym_entries)
        report.notes.append(f"Homonym: {record['hangul']} ({record['english']}) — existing sense(s): {existing}")
        report.homonyms += 1

    vocab_id = record.get("id") or db.new_id()
    word_type = record.get("type", "noun")
    registry_entry = {
        "id": vocab_id,
        "hangul": record["hangul"],
        "romanization": record["romanization"],
        "english": english,
        "type": word_type,
    }

    if not dry_run:
        session.vocabulary.append(registry_entry)
        session.by_sense[sense] = registry_entry
        session.vocab_dirty = True
        if examples:
            merged = db.merge_default_examples(vocab_id, examples, session.root, store=session.examples)
            if merged:
                session.examples_dirty = True
        section.setdefault("entries", []).append({"ref": vocab_id})
        session.topic_dirty = True
    elif examples:
        report.merged_examples += len(examples)

    report.added += 1


def import_verb_record(
    record: dict,
    session: ImportSession,
    report: ImportReport,
    *,
    dry_run: bool = False,
) -> None:
    required = {"hangul", "romanization", "english", "forms"}
    if not required.issubset(record):
        report.errors.append(f"Verb record missing fields: {sorted(required - set(record))}")
        report.skipped += 1
        return

    sense = db.sense_key(record["hangul"], record["english"])
    english = db.normalize_english_gloss(record["english"])

    if sense in session.by_sense:
        report.errors.append(f"Verb already exists: {record['hangul']} ({english}) (use merge via structured update — not implemented)")
        report.skipped += 1
        return

    homonym_entries = db.entries_for_hangul(session.vocabulary, record["hangul"])
    if homonym_entries:
        existing = ", ".join(f"{e['english']}" for e in homonym_entries)
        report.notes.append(f"Homonym verb: {record['hangul']} ({record['english']}) — existing sense(s): {existing}")
        report.homonyms += 1

    vocab_id = record.get("id") or db.new_id()
    if not dry_run:
        session.vocabulary.append(
            {
                "id": vocab_id,
                "hangul": record["hangul"],
                "romanization": record["romanization"],
                "english": english,
                "type": "verb",
            }
        )
        session.by_sense[sense] = session.vocabulary[-1]
        session.vocab_dirty = True

        for tense, variants in record["forms"].items():
            forms_file = session.forms_by_tense.setdefault(tense, {})
            forms_file[vocab_id] = dict(variants)
            session.forms_dirty.add(tense)

        for tense, variant_map in record.get("examples", {}).items():
            for variant, examples in variant_map.items():
                merged = db.merge_verb_examples(
                    vocab_id,
                    tense,
                    variant,
                    examples,
                    session.root,
                    store=session.examples,
                )
                if merged:
                    session.examples_dirty = True

    report.added += 1


def import_words_from_staging(
    staging_path: Path,
    session: ImportSession,
    report: ImportReport,
    *,
    section_id: str | None = None,
    dry_run: bool = False,
) -> None:
    data = db.load_yaml(staging_path)
    if not isinstance(data, dict):
        raise ValueError("Staging file must be a mapping.")
    for entry in data.get("entries", []):
        import_word_record(entry, session, report, section_id=section_id, dry_run=dry_run)


def import_words_from_lines(
    lines: list[str],
    session: ImportSession,
    report: ImportReport,
    *,
    section_id: str | None = None,
    dry_run: bool = False,
) -> None:
    assert session.topic is not None
    for line in lines:
        parsed = db.parse_import_line(line)
        if parsed is None:
            continue
        entry, example = parsed
        if not db.has_hangul(entry) and db.has_hangul(example or ""):
            entry, example = example, entry

        hangul_key = db.normalize_hangul(entry) if db.has_hangul(entry) else ""
        english_key = db.normalize_english(entry).casefold() if entry and not db.has_hangul(entry) else None

        word = None
        if hangul_key and english_key:
            word = session.by_sense.get((hangul_key, english_key))
        elif hangul_key:
            matches = db.entries_for_hangul(session.vocabulary, entry)
            if len(matches) == 1:
                word = matches[0]
            elif len(matches) > 1:
                senses = ", ".join(m["english"] for m in matches)
                report.errors.append(f"Ambiguous hangul '{entry.strip()}': multiple senses ({senses}); use --stdin-json")
                report.skipped += 1
                continue

        if word is not None:
            if example:
                hangul_part = example if db.has_hangul(example) else entry
                english_part = entry if not db.has_hangul(entry) else example
                ex = {"hangul": hangul_part, "english": english_part}
                if not dry_run:
                    merged = db.merge_default_examples(word["id"], [ex], session.root, store=session.examples)
                    if merged:
                        session.examples_dirty = True
                else:
                    merged = 1
                if merged:
                    report.merged_examples += merged
            if not db.topic_has_ref(session.topic, word["id"]):
                if not dry_run:
                    section = resolve_topic_section(session.topic, section_id)
                    section.setdefault("entries", []).append({"ref": word["id"]})
                    session.topic_dirty = True
                report.add_ref += 1
            else:
                report.skipped += 1
            continue

        report.errors.append(f"Cannot add new word from line '{line.strip()}' without romanization/english; use --stdin-json")
        report.skipped += 1


def cmd_words(args: argparse.Namespace) -> int:
    report = ImportReport()
    try:
        session = ImportSession.open_words(args.topic)
        if args.from_staging:
            import_words_from_staging(
                Path(args.from_staging),
                session,
                report,
                section_id=args.section,
                dry_run=args.dry_run,
            )
        elif args.stdin_json:
            for record in load_records_json(True, None):
                import_word_record(
                    record,
                    session,
                    report,
                    section_id=args.section,
                    dry_run=args.dry_run,
                )
        elif args.file:
            lines = Path(args.file).read_text(encoding="utf-8").splitlines()
            import_words_from_lines(
                lines,
                session,
                report,
                section_id=args.section,
                dry_run=args.dry_run,
            )
        else:
            print("Provide --file, --stdin-json, or --from-staging.", file=sys.stderr)
            return 2
        session.commit(dry_run=args.dry_run)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}{report.summary()}")
    for note in report.notes:
        print(f"  note: {note}", file=sys.stderr)
    for error in report.errors:
        print(f"  error: {error}", file=sys.stderr)
    return 1 if report.errors and report.added == 0 and report.merged_examples == 0 else 0


def cmd_verbs(args: argparse.Namespace) -> int:
    report = ImportReport()
    try:
        session = ImportSession.open_verbs()
        if args.stdin_json:
            for record in load_records_json(True, None):
                import_verb_record(record, session, report, dry_run=args.dry_run)
        elif args.file:
            print(
                "Verb file import requires --stdin-json with full conjugations.",
                file=sys.stderr,
            )
            return 2
        else:
            print("Provide --stdin-json for verbs.", file=sys.stderr)
            return 2
        session.commit(dry_run=args.dry_run)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}{report.summary()}")
    for note in report.notes:
        print(f"  note: {note}", file=sys.stderr)
    for error in report.errors:
        print(f"  error: {error}", file=sys.stderr)
    return 1 if report.errors and report.added == 0 else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import vocabulary into Soju data files.")
    sub = parser.add_subparsers(dest="kind", required=True)

    words = sub.add_parser("words", help="Import words into a topic")
    words.add_argument("--dry-run", action="store_true")
    words.add_argument("--topic", required=True, help="Topic id from topics manifest")
    words.add_argument("--section", help="Section id within the topic (required if multiple)")
    words.add_argument("--file", help="Plain-text word list file")
    words.add_argument("--stdin-json", action="store_true", help="Read JSON records from stdin")
    words.add_argument("--from-staging", help="Staging YAML file path")
    words.set_defaults(func=cmd_words)

    verbs = sub.add_parser("verbs", help="Import verbs")
    verbs.add_argument("--dry-run", action="store_true")
    verbs.add_argument("--file", help="Not supported without --stdin-json")
    verbs.add_argument("--stdin-json", action="store_true", help="Read JSON records from stdin")
    verbs.set_defaults(func=cmd_verbs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
