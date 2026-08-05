# SPDX-License-Identifier: BSD-3-Clause
"""Load the embedding cache and rank vocabulary/grammar for Practice."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from soju.core.config import data_root
from soju.levels import _included_level_ids, _matches_course_band
from soju.services.embeddings.cosine import cosine_similarity
from soju.services.embeddings.paths import grammar_jsonl_path, meta_json_path, vocab_jsonl_path

DEFAULT_VOCAB_K = 40
DEFAULT_GRAMMAR_M = 8
MAX_RESULT_COUNT = 200

EMBED_INDEX_HINT = "Run `uv run poe embed-index` (requires Ollama) to build data/cache/embeddings/."


class PracticeRetrieveError(Exception):
    """Retrieval failure with an HTTP-ish status for API routes."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class RetrievedGrammar:
    """Grammar pattern row returned to Practice generation."""

    id: str
    form: str
    english: str
    summary: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {"id": self.id, "form": self.form, "english": self.english}
        if self.summary:
            payload["summary"] = self.summary
        return payload


@dataclass(frozen=True)
class PracticeRetrieveResult:
    """Top-K hangul vocabulary and grammar for a theme query."""

    hangul: list[str]
    grammar: list[RetrievedGrammar]

    def as_dict(self) -> dict[str, Any]:
        return {
            "hangul": list(self.hangul),
            "grammar": [item.as_dict() for item in self.grammar],
        }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        row = json.loads(text)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def load_embeddings_cache(root: Path | None = None) -> dict[str, Any]:
    """Load ``meta.json`` + vocab/grammar JSONL from the embedding cache."""
    data = data_root(root)
    meta_path = meta_json_path(data)
    vocab_path = vocab_jsonl_path(data)
    grammar_path = grammar_jsonl_path(data)
    if not meta_path.is_file() or not vocab_path.is_file() or not grammar_path.is_file():
        raise PracticeRetrieveError(f"Embedding cache not found. {EMBED_INDEX_HINT}", 503)
    try:
        meta = _read_json(meta_path)
        if not isinstance(meta, dict):
            raise TypeError("meta.json must be an object")
        return {
            "meta": meta,
            "vocab": _read_jsonl(vocab_path),
            "grammar": _read_jsonl(grammar_path),
        }
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PracticeRetrieveError(f"Embedding cache is corrupt. Rebuild it: {EMBED_INDEX_HINT}", 503) from exc


def _clamp_count(value: int | None, fallback: int) -> int:
    if value is None or value <= 0:
        return fallback
    return min(int(value), MAX_RESULT_COUNT)


def _validate_query_vector(query_vector: list[float]) -> None:
    if not query_vector or not all(isinstance(value, (int, float)) and value == value for value in query_vector):
        raise PracticeRetrieveError("queryVector must be a non-empty array of numbers.", 400)


def retrieve_practice(
    *,
    query_vector: list[float],
    level: str | None = None,
    vocab_k: int | None = None,
    grammar_m: int | None = None,
    include_unassigned: bool = False,
    root: Path | None = None,
) -> PracticeRetrieveResult:
    """Rank cached vocabulary + grammar embeddings against a query vector."""
    _validate_query_vector(query_vector)
    cache = load_embeddings_cache(root)
    meta = cache["meta"]
    dimension = meta.get("dimension")
    if isinstance(dimension, int) and dimension > 0 and len(query_vector) != dimension:
        raise PracticeRetrieveError(
            f"Query embedding has dimension {len(query_vector)}, but the cached index has dimension {dimension} "
            f"(embed model {meta.get('embed_model')}). Re-embed the theme with that model, or rebuild the index: "
            f"{EMBED_INDEX_HINT}",
            400,
        )

    try:
        included_levels = _included_level_ids(level, root)
    except ValueError as exc:
        raise PracticeRetrieveError(str(exc), 400) from exc

    vocab_limit = _clamp_count(vocab_k, DEFAULT_VOCAB_K)
    grammar_limit = _clamp_count(grammar_m, DEFAULT_GRAMMAR_M)

    ranked_vocab: list[tuple[float, dict[str, Any]]] = []
    for entry in cache["vocab"]:
        if not _matches_course_band(entry.get("level"), included_levels, include_unassigned):
            continue
        embedding = entry.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != len(query_vector):
            continue
        ranked_vocab.append((cosine_similarity(query_vector, list(embedding)), entry))
    ranked_vocab.sort(key=lambda item: item[0], reverse=True)

    ranked_grammar: list[tuple[float, dict[str, Any]]] = []
    for entry in cache["grammar"]:
        if not _matches_course_band(entry.get("level"), included_levels, include_unassigned):
            continue
        embedding = entry.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != len(query_vector):
            continue
        ranked_grammar.append((cosine_similarity(query_vector, list(embedding)), entry))
    ranked_grammar.sort(key=lambda item: item[0], reverse=True)

    hangul = [str(entry.get("hangul", "")).strip() for _, entry in ranked_vocab[:vocab_limit] if str(entry.get("hangul", "")).strip()]
    grammar: list[RetrievedGrammar] = []
    for _, entry in ranked_grammar[:grammar_limit]:
        summary = str(entry.get("summary") or "").strip() or None
        grammar.append(
            RetrievedGrammar(
                id=str(entry.get("id", "")),
                form=str(entry.get("form", "")),
                english=str(entry.get("english", "")),
                summary=summary,
            )
        )
    return PracticeRetrieveResult(hangul=hangul, grammar=grammar)
