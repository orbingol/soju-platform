# SPDX-License-Identifier: BSD-3-Clause
"""Verb manifest, forms files, and conjugation-table helpers."""

from __future__ import annotations

from pathlib import Path

from soju.core.config import content_root, schema_rel_for
from soju.core.models import EXAMPLE_TENSES, EXAMPLE_VARIANTS
from soju.core.yaml_io import load_yaml, write_yaml_with_schema_comment


def load_verb_manifest(root: Path | None = None) -> dict:
    """Load ``content/verbs/manifest.yaml``.

    Raises:
        ValueError: If the manifest is not a mapping.
    """
    manifest = load_yaml(content_root(root) / "verbs" / "manifest.yaml")
    if not isinstance(manifest, dict):
        raise ValueError("content/verbs/manifest.yaml must be a mapping.")
    return manifest


def verb_table_path(root: Path | None = None) -> Path:
    """Return the path to the verb table YAML from the manifest."""
    manifest = load_verb_manifest(root)
    return content_root(root) / "verbs" / manifest["table"]


def verb_forms_path(tense: str, root: Path | None = None) -> Path:
    """Return the path to a tense forms YAML from the manifest."""
    manifest = load_verb_manifest(root)
    rel = manifest["forms"][tense]
    return content_root(root) / "verbs" / rel


def iter_verb_columns(table: dict) -> list[tuple[str, dict]]:
    """Yield ``(section_id, column)`` pairs from a verb table document."""
    columns: list[tuple[str, dict]] = []
    for section in table.get("sections", []):
        section_id = section["id"]
        for column in section.get("columns", []):
            columns.append((section_id, column))
    return columns


def load_verb_forms_file(tense: str, root: Path | None = None) -> dict:
    """Load one tense forms file as a mapping (empty dict if missing)."""
    path = verb_forms_path(tense, root)
    data = load_yaml(path) if path.exists() else {}
    return data if isinstance(data, dict) else {}


def load_all_verb_forms(root: Path | None = None) -> dict[str, dict]:
    """Load every tense forms file once. Keys are tense ids from the verb manifest."""
    manifest = load_verb_manifest(root)
    return {tense: load_verb_forms_file(tense, root) for tense in manifest.get("forms", {})}


def load_verb_forms_cache(root: Path | None = None) -> dict[str, dict]:
    """Cache of tense → forms file contents (present/past/future)."""
    return {tense: load_verb_forms_file(tense, root) for tense in EXAMPLE_TENSES}


def load_verb_forms(
    verb_id: str,
    root: Path | None = None,
    *,
    cache: dict[str, dict] | None = None,
) -> dict[str, dict[str, str]]:
    """Return ``{tense: {variant: form}}`` for one verb id."""
    forms_by_tense = cache if cache is not None else load_verb_forms_cache(root)
    forms: dict[str, dict[str, str]] = {}
    for tense in EXAMPLE_TENSES:
        tense_forms = forms_by_tense.get(tense, {}).get(verb_id, {})
        if isinstance(tense_forms, dict):
            forms[tense] = {variant: str(tense_forms[variant]) for variant in EXAMPLE_VARIANTS if variant in tense_forms}
    return forms


def save_verb_forms_file(tense: str, data: dict, root: Path | None = None) -> None:
    """Persist a tense forms file with a schema comment."""
    path = verb_forms_path(tense, root)
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "verbs_forms.schema.json", root),
        data,
    )
