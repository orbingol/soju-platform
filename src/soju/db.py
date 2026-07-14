# SPDX-License-Identifier: BSD-3-Clause
"""Shared data loaders, paths, and merge helpers for Soju tooling."""

from __future__ import annotations

import os
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any

import yaml


def data_root(root: Path | None = None) -> Path:
    """Resolve the data directory (``DATA_DIR`` env, else ``cwd/data``)."""
    if root is not None:
        return root
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env)
    return Path.cwd() / "data"


def content_root(root: Path | None = None) -> Path:
    return data_root(root) / "content"


def staging_root(root: Path | None = None) -> Path:
    return data_root(root) / "staging"


def registry_dir(root: Path | None = None) -> Path:
    return content_root(root) / "registry"


def topics_dir(root: Path | None = None) -> Path:
    return content_root(root) / "topics"


def verbs_dir(root: Path | None = None) -> Path:
    return content_root(root) / "verbs"


def schema_rel_for(path: Path, schema_name: str, root: Path | None = None) -> str:
    """Relative ``$schema`` path from a YAML file under ``data/`` to ``data/schemas/``."""
    rel = path.resolve().relative_to(data_root(root).resolve())
    # Climb to ``data/`` (exclude the filename), then into ``schemas/``.
    ups = "/".join([".."] * (len(rel.parts) - 1)) or "."
    return f"{ups}/schemas/{schema_name}"


EXAMPLE_TENSES = ("present", "past", "future")
EXAMPLE_VARIANTS = ("casual_polite", "formal_polite")

IMPORT_LINE = re.compile(r"^(?P<entry>.*?)(?:\s*[\(（](?P<example>.*?)[\)）])?\s*$")


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            data,
            handle,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


class _LiteralStr(str):
    """Marker type: emit YAML literal block scalars (|) for example sentences."""


class _ExamplesDumper(yaml.SafeDumper):
    pass


def _literal_str_representer(dumper: yaml.SafeDumper, data: _LiteralStr) -> Any:
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        str(data),
        style="|",
    )


_ExamplesDumper.add_representer(_LiteralStr, _literal_str_representer)


def _annotate_example_literal_strings(data: Any) -> Any:
    if isinstance(data, dict):
        annotated: dict[Any, Any] = {}
        for key, value in data.items():
            if key in ("hangul", "english") and isinstance(value, str):
                annotated[key] = _LiteralStr(value)
            else:
                annotated[key] = _annotate_example_literal_strings(value)
        return annotated
    if isinstance(data, list):
        return [_annotate_example_literal_strings(item) for item in data]
    return data


def write_examples_yaml_with_schema_comment(path: Path, schema_rel: str, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# yaml-language-server: $schema={schema_rel}\n\n")
        yaml.dump(
            _annotate_example_literal_strings(data),
            handle,
            Dumper=_ExamplesDumper,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=10_000,
        )


def write_yaml_with_schema_comment(path: Path, schema_rel: str, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# yaml-language-server: $schema={schema_rel}\n\n")
        yaml.safe_dump(
            data,
            handle,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


def new_id() -> str:
    return str(uuid.uuid4())


def normalize_hangul(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    return unicodedata.normalize("NFC", collapsed)


def normalize_english(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


# Proper names kept capitalized in vocabulary glosses (not example sentences).
# Longer phrases first so matching prefers e.g. "south korea" over "korea".
PROPER_NAME_GLOSS_WORDS: dict[str, str] = {
    # Multi-word places
    "new york": "New York",
    "south korea": "South Korea",
    "north korea": "North Korea",
    "united states": "United States",
    "united kingdom": "United Kingdom",
    "hong kong": "Hong Kong",
    "los angeles": "Los Angeles",
    "san francisco": "San Francisco",
    "harry potter": "Harry Potter",
    # Languages and demonyms
    "korean": "Korean",
    "english": "English",
    "japanese": "Japanese",
    "chinese": "Chinese",
    "french": "French",
    "german": "German",
    "spanish": "Spanish",
    "italian": "Italian",
    "russian": "Russian",
    "vietnamese": "Vietnamese",
    "thai": "Thai",
    "hindi": "Hindi",
    "arabic": "Arabic",
    "portuguese": "Portuguese",
    "american": "American",
    "british": "British",
    # Countries and regions
    "korea": "Korea",
    "japan": "Japan",
    "china": "China",
    "america": "America",
    "france": "France",
    "germany": "Germany",
    "spain": "Spain",
    "italy": "Italy",
    "russia": "Russia",
    "vietnam": "Vietnam",
    "thailand": "Thailand",
    "india": "India",
    "mexico": "Mexico",
    "canada": "Canada",
    "australia": "Australia",
    "britain": "Britain",
    "europe": "Europe",
    "asia": "Asia",
    "africa": "Africa",
    # Korean cities
    "seoul": "Seoul",
    "busan": "Busan",
    "incheon": "Incheon",
    "daegu": "Daegu",
    "gwangju": "Gwangju",
    "daejeon": "Daejeon",
    "ulsan": "Ulsan",
    "jeju": "Jeju",
    "pyongyang": "Pyongyang",
    # Other cities
    "tokyo": "Tokyo",
    "osaka": "Osaka",
    "beijing": "Beijing",
    "shanghai": "Shanghai",
    "paris": "Paris",
    "london": "London",
    # Short forms
    "uk": "UK",
    "usa": "USA",
}


def normalize_english_gloss(text: str) -> str:
    """Normalize a vocabulary meaning: lowercase gloss, restore proper-name caps."""
    gloss = normalize_english(text).lower()
    if not gloss:
        return gloss
    for lower, proper in sorted(PROPER_NAME_GLOSS_WORDS.items(), key=lambda item: -len(item[0])):
        gloss = re.sub(rf"\b{re.escape(lower)}\b", proper, gloss, flags=re.IGNORECASE)
    return gloss


def example_key(hangul: str, english: str) -> tuple[str, str]:
    return normalize_hangul(hangul), normalize_english(english)


def sense_key(hangul: str, english: str) -> tuple[str, str]:
    """Registry uniqueness: same hangul + same English meaning is one sense."""
    return normalize_hangul(hangul), normalize_english_gloss(english).casefold()


def has_hangul(text: str) -> bool:
    return bool(re.search(r"[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]", text))


def load_types(root: Path | None = None) -> list[dict]:
    data = load_yaml(content_root(root) / "registry" / "types.yaml")
    if not isinstance(data, dict):
        raise ValueError("content/registry/types.yaml must be a mapping.")
    types = data.get("types", [])
    if not isinstance(types, list):
        raise ValueError("content/registry/types.yaml types must be a list.")
    return types


def type_by_id(type_id: str, root: Path | None = None) -> dict | None:
    for entry in load_types(root):
        if entry["id"] == type_id:
            return entry
    return None


def type_by_slug(slug: str, root: Path | None = None) -> dict | None:
    for entry in load_types(root):
        if entry["slug"] == slug:
            return entry
    return None


def load_vocabulary(root: Path | None = None) -> list[dict]:
    path = content_root(root) / "registry" / "vocabulary.yaml"
    data = load_yaml(path) if path.exists() else []
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError("content/registry/vocabulary.yaml must be a list.")
    return data


def save_vocabulary(entries: list[dict], root: Path | None = None) -> None:
    path = content_root(root) / "registry" / "vocabulary.yaml"
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "registry_vocabulary.schema.json", root),
        entries,
    )


def vocabulary_by_id(root: Path | None = None) -> dict[str, dict]:
    return {entry["id"]: entry for entry in load_vocabulary(root)}


def vocabulary_by_hangul(root: Path | None = None) -> dict[str, dict]:
    """First registry entry per hangul (legacy lookup; not for dedup)."""
    return {normalize_hangul(entry["hangul"]): entry for entry in load_vocabulary(root)}


def build_sense_index(entries: list[dict]) -> dict[tuple[str, str], dict]:
    return {sense_key(entry["hangul"], entry["english"]): entry for entry in entries}


def vocabulary_by_sense(root: Path | None = None) -> dict[tuple[str, str], dict]:
    return build_sense_index(load_vocabulary(root))


def entries_for_hangul(entries: list[dict], hangul: str) -> list[dict]:
    key = normalize_hangul(hangul)
    return [entry for entry in entries if normalize_hangul(entry["hangul"]) == key]


def vocabulary_entries_for_hangul(hangul: str, root: Path | None = None) -> list[dict]:
    return entries_for_hangul(load_vocabulary(root), hangul)


def vocabulary_by_type(type_id: str, root: Path | None = None) -> list[dict]:
    return [entry for entry in load_vocabulary(root) if entry.get("type") == type_id]


def load_examples_store(root: Path | None = None) -> dict:
    path = content_root(root) / "registry" / "examples.yaml"
    data = load_yaml(path) if path.exists() else {}
    return data if isinstance(data, dict) else {}


def verb_examples_complete(
    forms: dict[str, dict[str, str]],
    examples: dict[str, Any],
) -> bool:
    for tense in EXAMPLE_TENSES:
        for variant in EXAMPLE_VARIANTS:
            if forms.get(tense, {}).get(variant) and not examples.get(tense, {}).get(variant):
                return False
    return True


def noun_entry_needs_fill(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return True
    default = entry.get("default")
    return not isinstance(default, list) or len(default) == 0


def verb_entry_needs_fill(forms: dict[str, dict[str, str]], entry: Any) -> bool:
    if not isinstance(entry, dict) or "default" in entry:
        return True
    return not verb_examples_complete(forms, entry)


def save_examples_store(data: dict, root: Path | None = None) -> None:
    path = content_root(root) / "registry" / "examples.yaml"
    write_examples_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "examples_vocabulary.schema.json", root),
        data,
    )


def load_type_table(type_id: str, root: Path | None = None) -> dict:
    base = content_root(root)
    if type_id == "verb":
        specialized = base / "verbs" / "table.yaml"
    else:
        specialized = base / type_id / "table.yaml"
    if specialized.is_file():
        return load_yaml(specialized)
    return load_yaml(base / "words" / "table.yaml")


def load_topic_table(topic_id: str, root: Path | None = None) -> dict:
    base = content_root(root) / "topics"
    override = base / topic_id / "table.yaml"
    if override.is_file():
        return load_yaml(override)
    return load_yaml(base / "table.yaml")


def load_topics_manifest(root: Path | None = None) -> dict:
    manifest = load_yaml(content_root(root) / "topics" / "manifest.yaml")
    if not isinstance(manifest, dict):
        raise ValueError("content/topics/manifest.yaml must be a mapping.")
    return manifest


def load_verb_manifest(root: Path | None = None) -> dict:
    manifest = load_yaml(content_root(root) / "verbs" / "manifest.yaml")
    if not isinstance(manifest, dict):
        raise ValueError("content/verbs/manifest.yaml must be a mapping.")
    return manifest


def verb_table_path(root: Path | None = None) -> Path:
    manifest = load_verb_manifest(root)
    return content_root(root) / "verbs" / manifest["table"]


def verb_forms_path(tense: str, root: Path | None = None) -> Path:
    manifest = load_verb_manifest(root)
    rel = manifest["forms"][tense]
    return content_root(root) / "verbs" / rel


def topic_path(topic_id: str, root: Path | None = None) -> Path:
    manifest = load_topics_manifest(root)
    topics = manifest.get("topics", {})
    if topic_id not in topics:
        raise KeyError(f"Unknown topic: {topic_id}")
    return content_root(root) / "topics" / topic_id / "topic.yaml"


def load_topic(topic_id: str, root: Path | None = None) -> dict:
    path = topic_path(topic_id, root)
    data = load_yaml(path) if path.exists() else {"sections": []}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping with sections.")
    data.setdefault("sections", [])
    return data


def save_topic(topic_id: str, data: dict, root: Path | None = None) -> None:
    path = topic_path(topic_id, root)
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "topics_topic.schema.json", root),
        data,
    )


def iter_topic_entries(topic: dict) -> list[dict]:
    entries: list[dict] = []
    for section in topic.get("sections", []):
        entries.extend(section.get("entries", []))
    return entries


def topic_has_ref(topic: dict, vocab_id: str) -> bool:
    for entry in iter_topic_entries(topic):
        if entry.get("ref") == vocab_id:
            return True
        if entry.get("id") == vocab_id:
            return True
    return False


def find_local_entry(topic: dict, hangul: str, english: str | None = None) -> dict | None:
    key = normalize_hangul(hangul)
    english_key = normalize_english(english).casefold() if english is not None else None
    for entry in iter_topic_entries(topic):
        if not entry.get("local"):
            continue
        if normalize_hangul(entry.get("hangul", "")) != key:
            continue
        if english_key is not None and normalize_english(entry.get("english", "")).casefold() != english_key:
            continue
        return entry
    return None


def find_section(topic: dict, section_id: str) -> dict | None:
    for section in topic.get("sections", []):
        if section.get("id") == section_id:
            return section
    return None


def merge_default_examples(
    vocab_id: str,
    new_examples: list[dict],
    root: Path | None = None,
    *,
    store: dict | None = None,
) -> int:
    own_store = store is None
    if own_store:
        store = load_examples_store(root)
    assert store is not None
    entry = store.setdefault(vocab_id, {})
    if "default" not in entry or not isinstance(entry["default"], list):
        entry["default"] = []
    existing = entry["default"]
    keys = {example_key(ex["hangul"], ex["english"]) for ex in existing}
    merged = 0
    for ex in new_examples:
        clean = {"hangul": ex["hangul"], "english": ex["english"]}
        key = example_key(clean["hangul"], clean["english"])
        if key in keys:
            continue
        existing.append(clean)
        keys.add(key)
        merged += 1
    if merged and own_store:
        save_examples_store(store, root)
    return merged


def merge_verb_examples(
    vocab_id: str,
    tense: str,
    variant: str,
    new_examples: list[dict],
    root: Path | None = None,
    *,
    store: dict | None = None,
) -> int:
    own_store = store is None
    if own_store:
        store = load_examples_store(root)
    assert store is not None
    entry = store.setdefault(vocab_id, {})
    tense_map = entry.setdefault(tense, {})
    if not isinstance(tense_map, dict):
        return 0
    variant_list = tense_map.setdefault(variant, [])
    if not isinstance(variant_list, list):
        return 0
    keys = {example_key(ex["hangul"], ex["english"]) for ex in variant_list}
    merged = 0
    for ex in new_examples:
        clean = {"hangul": ex["hangul"], "english": ex["english"]}
        key = example_key(clean["hangul"], clean["english"])
        if key in keys:
            continue
        variant_list.append(clean)
        keys.add(key)
        merged += 1
    if merged and own_store:
        save_examples_store(store, root)
    return merged


def iter_verb_columns(table: dict) -> list[tuple[str, dict]]:
    columns: list[tuple[str, dict]] = []
    for section in table.get("sections", []):
        section_id = section["id"]
        for column in section.get("columns", []):
            columns.append((section_id, column))
    return columns


def load_verb_forms_file(tense: str, root: Path | None = None) -> dict:
    path = verb_forms_path(tense, root)
    data = load_yaml(path) if path.exists() else {}
    return data if isinstance(data, dict) else {}


def load_all_verb_forms(root: Path | None = None) -> dict[str, dict]:
    """Load every tense forms file once. Keys are tense ids from the verb manifest."""
    manifest = load_verb_manifest(root)
    return {tense: load_verb_forms_file(tense, root) for tense in manifest.get("forms", {})}


def save_verb_forms_file(tense: str, data: dict, root: Path | None = None) -> None:
    path = verb_forms_path(tense, root)
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "verbs_forms.schema.json", root),
        data,
    )


def get_verb_examples(vocab_id: str, root: Path | None = None) -> dict:
    store = load_examples_store(root)
    entry = store.get(vocab_id, {})
    if not isinstance(entry, dict):
        return {}
    if "default" in entry:
        return {}
    return entry


def parse_import_line(line: str) -> tuple[str, str | None] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = IMPORT_LINE.match(stripped)
    if not match:
        return None
    entry = match.group("entry").strip()
    example = match.group("example")
    if example is not None:
        example = example.strip()
    if not entry:
        return None
    return entry, example or None


def glob_validate_targets(root: Path | None = None) -> dict[str, list[str]]:
    base = content_root(root)
    data = data_root(root)
    verb_manifest = load_verb_manifest(root)
    topics_manifest = load_topics_manifest(root)

    topic_files = [str(topic_path(topic_id, root)) for topic_id in sorted(topics_manifest.get("topics", {}))]

    topic_table_files = [str(base / "topics" / "table.yaml")]
    for topic_id in sorted(topics_manifest.get("topics", {})):
        override = base / "topics" / topic_id / "table.yaml"
        if override.is_file():
            topic_table_files.append(str(override))

    form_files = [str(base / "verbs" / rel) for rel in sorted(verb_manifest.get("forms", {}).values())]
    construction_files = [str(base / "verbs" / rel) for rel in sorted(verb_manifest.get("constructions", {}).values())]

    staging_exercises = sorted(str(p) for p in (data / "staging" / "exercises").glob("*.yaml"))
    staging_stories = sorted(str(p) for p in (data / "staging" / "stories").glob("*.yaml"))

    grammar_manifest_path = base / "grammar" / "manifest.yaml"
    grammar_pattern_files: list[str] = []
    if grammar_manifest_path.exists():
        grammar_manifest = load_yaml(grammar_manifest_path)
        if isinstance(grammar_manifest, dict):
            for meta in grammar_manifest.get("patterns", {}).values():
                if isinstance(meta, dict) and meta.get("path"):
                    grammar_pattern_files.append(str(base / "grammar" / meta["path"]))

    return {
        "registry-types": [str(base / "registry" / "types.yaml")],
        "registry-vocabulary": [str(base / "registry" / "vocabulary.yaml")],
        "examples-vocabulary": [str(base / "registry" / "examples.yaml")],
        "words-table": [str(base / "words" / "table.yaml")],
        "topics-manifest": [str(base / "topics" / "manifest.yaml")],
        "topics-table": topic_table_files,
        "topics-topics": topic_files,
        "verb-manifest": [str(base / "verbs" / "manifest.yaml")],
        "verb-table": [str(base / "verbs" / "table.yaml")],
        "verb-forms": form_files,
        "verb-constructions": construction_files,
        "grammar-manifest": [str(grammar_manifest_path)],
        "grammar-patterns": grammar_pattern_files,
        "staging-vocabulary": [str(data / "staging" / "vocabulary-candidates.yaml")],
        "staging-exercises": staging_exercises,
        "staging-stories": staging_stories,
    }
