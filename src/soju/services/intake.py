# SPDX-License-Identifier: BSD-3-Clause
"""Canonical vocabulary import / merge orchestration (no CLI)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from soju.base.plugins import get_base_language
from soju.core.text import parse_import_line
from soju.core.yaml_io import load_yaml, new_id
from soju.languages.plugins import get_language
from soju.levels import resolve_level_id
from soju.registry.examples import load_examples_store, merge_default_examples, merge_verb_examples, save_examples_store
from soju.registry.topics import find_local_entry, find_section, load_topic, save_topic, topic_has_ref
from soju.registry.verbs import load_all_verb_forms, save_verb_forms_file
from soju.registry.vocabulary import build_sense_index, entries_for_hangul, load_vocabulary, save_vocabulary
from soju.services.keys import example_key, match_gloss, normalize_term, sense_key


@dataclass
class ImportReport:
    added: int = 0
    merged_examples: int = 0
    add_ref: int = 0
    retagged_level: int = 0
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
        if self.retagged_level:
            parts.insert(3, f"retagged_level={self.retagged_level}")
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
        vocabulary = load_vocabulary(root)
        return cls(
            root=root,
            vocabulary=vocabulary,
            by_sense=build_sense_index(vocabulary, sense_key=sense_key),
            examples=load_examples_store(root),
            topic_id=topic_id,
            topic=load_topic(topic_id, root),
        )

    @classmethod
    def open_verbs(cls, root=None) -> ImportSession:
        vocabulary = load_vocabulary(root)
        return cls(
            root=root,
            vocabulary=vocabulary,
            by_sense=build_sense_index(vocabulary, sense_key=sense_key),
            examples=load_examples_store(root),
            forms_by_tense=load_all_verb_forms(root),
        )

    def commit(self, *, dry_run: bool) -> None:
        if dry_run:
            return
        if self.vocab_dirty:
            save_vocabulary(self.vocabulary, self.root)
        if self.examples_dirty:
            save_examples_store(self.examples, self.root)
        if self.topic_dirty and self.topic_id is not None and self.topic is not None:
            save_topic(self.topic_id, self.topic, self.root)
        for tense in sorted(self.forms_dirty):
            save_verb_forms_file(tense, self.forms_by_tense[tense], self.root)


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
        section = find_section(topic, section_id)
        if section is None:
            raise ValueError(f"Unknown section id: {section_id}")
        return section
    if len(sections) == 1:
        return sections[0]
    raise ValueError("Topic has multiple sections; pass --section <id>.")


def _resolve_word_romanization(record: dict) -> str | None:
    """Return an explicit or auto-generated romanization for a word record.

    Staging / Practice candidates often omit romanization; fill it from hangul
    via the active language plugin when missing or blank.
    """
    raw = record.get("romanization")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower()

    hangul = record.get("hangul")
    if not isinstance(hangul, str) or not hangul.strip():
        return None

    generated = get_language().romanize(hangul).strip().lower()
    return generated or None


def _resolve_record_level(record: dict, cli_level: str | None, root) -> str | None:
    """Resolve course level from record then CLI; ``None`` means unassigned.

    Raises:
        ValueError: If a provided level id is not defined in ``levels.yaml``.
    """
    raw = record.get("level")
    if isinstance(raw, str) and raw.strip():
        return resolve_level_id(raw.strip(), root)
    if isinstance(cli_level, str) and cli_level.strip():
        return resolve_level_id(cli_level.strip(), root)
    return None


def import_word_record(
    record: dict,
    session: ImportSession,
    report: ImportReport,
    *,
    section_id: str | None = None,
    dry_run: bool = False,
    level_id: str | None = None,
) -> None:
    required = {"hangul", "english"}
    if not required.issubset(record):
        report.errors.append(f"Word record missing fields: {sorted(required - set(record))}")
        report.skipped += 1
        return

    romanization = _resolve_word_romanization(record)
    if not romanization:
        report.errors.append(f"Word record missing romanization and could not generate one from hangul {record.get('hangul')!r}")
        report.skipped += 1
        return

    try:
        resolved_level = _resolve_record_level(record, level_id, session.root)
    except ValueError as exc:
        report.errors.append(str(exc))
        report.skipped += 1
        return

    if session.topic is None:
        raise ValueError("Import session has no topic loaded.")
    try:
        section = resolve_topic_section(session.topic, section_id)
    except ValueError as exc:
        report.errors.append(str(exc))
        report.skipped += 1
        return

    sense = sense_key(record["hangul"], record["english"])
    examples = record.get("examples", [])
    english = get_base_language().normalize_gloss(record["english"])

    local = find_local_entry(session.topic, record["hangul"], english, normalize=normalize_term, match_gloss=match_gloss)
    if local:
        if examples and not dry_run:
            merged = merge_default_examples(local["id"], examples, session.root, store=session.examples, example_key=example_key)
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
        did_work = False
        if examples:
            if not dry_run:
                merged = merge_default_examples(entry["id"], examples, session.root, store=session.examples, example_key=example_key)
                if merged:
                    session.examples_dirty = True
            else:
                merged = len(examples)
            if merged:
                report.merged_examples += merged
                did_work = True
        if resolved_level is not None and entry.get("level") != resolved_level:
            if not dry_run:
                entry["level"] = resolved_level
                session.vocab_dirty = True
            report.retagged_level += 1
            did_work = True
        if not topic_has_ref(session.topic, entry["id"]):
            if not dry_run:
                section.setdefault("entries", []).append({"ref": entry["id"]})
                session.topic_dirty = True
            report.add_ref += 1
            did_work = True
        elif not did_work:
            report.skipped += 1
        return

    homonym_entries = entries_for_hangul(session.vocabulary, record["hangul"], normalize=normalize_term)
    if homonym_entries:
        existing = ", ".join(f"{e['english']}" for e in homonym_entries)
        report.notes.append(f"Homonym: {record['hangul']} ({record['english']}) — existing sense(s): {existing}")
        report.homonyms += 1

    vocab_id = record.get("id") or new_id()
    word_type = record.get("type", "noun")
    registry_entry = {
        "id": vocab_id,
        "hangul": record["hangul"],
        "romanization": romanization,
        "english": english,
        "type": word_type,
    }
    if resolved_level is not None:
        registry_entry["level"] = resolved_level

    if not dry_run:
        session.vocabulary.append(registry_entry)
        session.by_sense[sense] = registry_entry
        session.vocab_dirty = True
        if examples:
            merged = merge_default_examples(vocab_id, examples, session.root, store=session.examples, example_key=example_key)
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
    level_id: str | None = None,
) -> None:
    required = {"hangul", "romanization", "english", "forms"}
    if not required.issubset(record):
        report.errors.append(f"Verb record missing fields: {sorted(required - set(record))}")
        report.skipped += 1
        return

    try:
        resolved_level = _resolve_record_level(record, level_id, session.root)
    except ValueError as exc:
        report.errors.append(str(exc))
        report.skipped += 1
        return

    sense = sense_key(record["hangul"], record["english"])
    english = get_base_language().normalize_gloss(record["english"])

    if sense in session.by_sense:
        report.errors.append(f"Verb already exists: {record['hangul']} ({english}) (use merge via structured update — not implemented)")
        report.skipped += 1
        return

    homonym_entries = entries_for_hangul(session.vocabulary, record["hangul"], normalize=normalize_term)
    if homonym_entries:
        existing = ", ".join(f"{e['english']}" for e in homonym_entries)
        report.notes.append(f"Homonym verb: {record['hangul']} ({record['english']}) — existing sense(s): {existing}")
        report.homonyms += 1

    vocab_id = record.get("id") or new_id()
    if not dry_run:
        registry_entry = {
            "id": vocab_id,
            "hangul": record["hangul"],
            "romanization": record["romanization"],
            "english": english,
            "type": "verb",
        }
        if resolved_level is not None:
            registry_entry["level"] = resolved_level
        session.vocabulary.append(registry_entry)
        session.by_sense[sense] = session.vocabulary[-1]
        session.vocab_dirty = True

        for tense, variants in record["forms"].items():
            forms_file = session.forms_by_tense.setdefault(tense, {})
            forms_file[vocab_id] = dict(variants)
            session.forms_dirty.add(tense)

        for tense, variant_map in record.get("examples", {}).items():
            for variant, examples in variant_map.items():
                merged = merge_verb_examples(
                    vocab_id,
                    tense,
                    variant,
                    examples,
                    session.root,
                    store=session.examples,
                    example_key=example_key,
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
    level_id: str | None = None,
) -> None:
    data = load_yaml(staging_path)
    if not isinstance(data, dict):
        raise ValueError("Staging file must be a mapping.")
    for entry in data.get("entries", []):
        import_word_record(
            entry,
            session,
            report,
            section_id=section_id,
            dry_run=dry_run,
            level_id=level_id,
        )


def import_words_from_lines(
    lines: list[str],
    session: ImportSession,
    report: ImportReport,
    *,
    section_id: str | None = None,
    dry_run: bool = False,
    level_id: str | None = None,
) -> None:
    if session.topic is None:
        raise ValueError("Import session has no topic loaded.")
    for line in lines:
        parsed = parse_import_line(line)
        if parsed is None:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                report.errors.append(f"Skipped unparseable line: {stripped}")
                report.skipped += 1
            continue
        entry, example = parsed
        lang = get_language()
        if not lang.is_target_script(entry) and lang.is_target_script(example or ""):
            entry, example = example, entry

        hangul_key = normalize_term(entry) if lang.is_target_script(entry) else ""
        english_key = match_gloss(entry) if entry and not lang.is_target_script(entry) else None

        word = None
        if hangul_key and english_key:
            word = session.by_sense.get((hangul_key, english_key))
        elif hangul_key:
            matches = entries_for_hangul(session.vocabulary, entry, normalize=normalize_term)
            if len(matches) == 1:
                word = matches[0]
            elif len(matches) > 1:
                senses = ", ".join(m["english"] for m in matches)
                report.errors.append(f"Ambiguous hangul '{entry.strip()}': multiple senses ({senses}); use --stdin-json")
                report.skipped += 1
                continue

        if word is not None:
            did_work = False
            if level_id:
                try:
                    resolved_level = _resolve_record_level({}, level_id, session.root)
                except ValueError as exc:
                    report.errors.append(str(exc))
                    report.skipped += 1
                    continue
                if resolved_level is not None and word.get("level") != resolved_level:
                    if not dry_run:
                        word["level"] = resolved_level
                        session.vocab_dirty = True
                    report.retagged_level += 1
                    did_work = True
            if example:
                hangul_part = example if lang.is_target_script(example) else entry
                english_part = entry if not lang.is_target_script(entry) else example
                ex = {"hangul": hangul_part, "english": english_part}
                if not dry_run:
                    merged = merge_default_examples(word["id"], [ex], session.root, store=session.examples, example_key=example_key)
                    if merged:
                        session.examples_dirty = True
                else:
                    merged = 1
                if merged:
                    report.merged_examples += merged
                    did_work = True
            if not topic_has_ref(session.topic, word["id"]):
                if not dry_run:
                    section = resolve_topic_section(session.topic, section_id)
                    section.setdefault("entries", []).append({"ref": word["id"]})
                    session.topic_dirty = True
                report.add_ref += 1
                did_work = True
            elif not did_work:
                report.skipped += 1
            continue

        report.errors.append(f"Cannot add new word from line '{line.strip()}' without romanization/english; use --stdin-json")
        report.skipped += 1
