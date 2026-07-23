# SPDX-License-Identifier: BSD-3-Clause
"""Vocabulary + grammar documents prepared for embedding.

Kept separate from :mod:`soju.services.embeddings.build` so index-building tests can
exercise document preparation without mocking Ollama calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from soju.core.config import content_root
from soju.core.yaml_io import load_yaml
from soju.registry.vocabulary import load_vocabulary


@dataclass(frozen=True)
class VocabDoc:
    """A vocabulary entry prepared for embedding.

    ``level`` mirrors the registry's optional ``level`` field: ``None`` means the
    entry is unassigned (not tagged to a course level; see ``soju.levels``).
    """

    id: str
    hangul: str
    romanization: str
    english: str
    type: str
    level: str | None
    text: str


@dataclass(frozen=True)
class GrammarDoc:
    """A grammar pattern prepared for embedding."""

    id: str
    form: str
    english: str
    category: str
    summary: str
    text: str


def _vocab_doc(entry: dict) -> VocabDoc:
    hangul = str(entry.get("hangul", ""))
    english = str(entry.get("english", ""))
    text = f"{english} ({hangul})" if hangul else english
    level = entry.get("level")
    return VocabDoc(
        id=str(entry["id"]),
        hangul=hangul,
        romanization=str(entry.get("romanization", "")),
        english=english,
        type=str(entry.get("type", "noun")),
        level=str(level) if level else None,
        text=text,
    )


def load_vocab_docs(root: Path | None = None) -> list[VocabDoc]:
    """Return embeddable documents for every registry vocabulary entry.

    Includes every type and visibility (Practice/chat already use the full
    registry, including hidden grammar phrases) — no theme filtering.

    Args:
        root: Optional data-root override.
    """
    return [_vocab_doc(entry) for entry in load_vocabulary(root)]


def _grammar_doc(pattern_id: str, meta: dict) -> GrammarDoc:
    form = str(meta.get("form", ""))
    english = str(meta.get("english", ""))
    summary = str(meta.get("description", "")).strip()
    text = f"{form}: {english}. {summary}".strip()
    return GrammarDoc(
        id=pattern_id,
        form=form,
        english=english,
        category=str(meta.get("category", "")),
        summary=summary,
        text=text,
    )


def load_grammar_docs(root: Path | None = None) -> list[GrammarDoc]:
    """Return embeddable documents for every grammar pattern in the manifest.

    Args:
        root: Optional data-root override.

    Returns:
        Documents sorted by pattern id; empty when the manifest is missing.
    """
    manifest_path = content_root(root) / "grammar" / "manifest.yaml"
    if not manifest_path.is_file():
        return []
    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        return []
    patterns = manifest.get("patterns", {})
    if not isinstance(patterns, dict):
        return []
    return [_grammar_doc(pattern_id, meta) for pattern_id, meta in sorted(patterns.items()) if isinstance(meta, dict)]
