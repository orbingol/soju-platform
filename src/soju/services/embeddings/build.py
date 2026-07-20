# SPDX-License-Identifier: BSD-3-Clause
"""Build the Ollama embedding cache used by Practice retrieval."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from soju.services.embeddings.documents import load_grammar_docs, load_vocab_docs
from soju.services.embeddings.paths import (
    embeddings_cache_dir,
    grammar_jsonl_path,
    meta_json_path,
    vocab_jsonl_path,
)

if TYPE_CHECKING:
    from soju.llm.ollama import OllamaClient

DEFAULT_EMBED_MODEL = os.environ.get("SOJU_EMBED_MODEL", "nomic-embed-text")

EmbedFn = Callable[[Sequence[str]], list[list[float]]]


@dataclass(frozen=True)
class EmbedIndexResult:
    """Summary of a completed embedding index build."""

    vocab_count: int
    grammar_count: int
    dimension: int | None
    embed_model: str


def make_ollama_embed_fn(
    client: OllamaClient,
    *,
    batch_size: int = 32,
    on_progress: Callable[[int, int], None] | None = None,
) -> EmbedFn:
    """Build a batch :data:`EmbedFn` backed by ``client``, chunking requests.

    Args:
        client: An :class:`~soju.llm.ollama.OllamaClient` bound to the embed model/base URL.
        batch_size: Maximum documents per ``/api/embed`` request.
        on_progress: Optional callback invoked as ``(embedded_so_far, total)`` after each chunk.

    Returns:
        A callable taking ordered texts and returning their embedding vectors, in order.
    """

    def embed_fn(texts: Sequence[str]) -> list[list[float]]:
        ordered = list(texts)
        vectors: list[list[float]] = []
        for start in range(0, len(ordered), batch_size):
            chunk = ordered[start : start + batch_size]
            vectors.extend(client.embed_batch(chunk))
            if on_progress is not None:
                on_progress(len(vectors), len(ordered))
        return vectors

    return embed_fn


def build_embedding_index(
    *,
    embed_fn: EmbedFn,
    embed_model: str,
    root: Path | None = None,
) -> EmbedIndexResult:
    """Embed vocabulary + grammar documents and write the cache under ``data/cache/embeddings/``.

    Args:
        embed_fn: Batch embedding callable; injected so tests can supply deterministic mock
            vectors without a live Ollama server (see :func:`make_ollama_embed_fn` for the
            real implementation).
        embed_model: Embedding model name recorded in ``meta.json`` for mismatch detection.
        root: Optional data-root override.

    Returns:
        Counts and vector dimension for the written cache.

    Raises:
        ValueError: If the embedded vectors have inconsistent dimensions.
    """
    vocab_docs = load_vocab_docs(root)
    grammar_docs = load_grammar_docs(root)

    vocab_vectors = embed_fn([doc.text for doc in vocab_docs]) if vocab_docs else []
    grammar_vectors = embed_fn([doc.text for doc in grammar_docs]) if grammar_docs else []

    dimension = _check_dimension(vocab_vectors, grammar_vectors)

    cache_dir = embeddings_cache_dir(root)
    cache_dir.mkdir(parents=True, exist_ok=True)

    _write_jsonl(
        vocab_jsonl_path(root),
        (
            {
                "id": doc.id,
                "hangul": doc.hangul,
                "romanization": doc.romanization,
                "english": doc.english,
                "type": doc.type,
                "level": doc.level,
                "embedding": vector,
            }
            for doc, vector in zip(vocab_docs, vocab_vectors)
        ),
    )
    _write_jsonl(
        grammar_jsonl_path(root),
        (
            {
                "id": doc.id,
                "form": doc.form,
                "english": doc.english,
                "category": doc.category,
                "summary": doc.summary,
                "embedding": vector,
            }
            for doc, vector in zip(grammar_docs, grammar_vectors)
        ),
    )
    meta_json_path(root).write_text(
        json.dumps(
            {
                "embed_model": embed_model,
                "dimension": dimension,
                "vocab_count": len(vocab_docs),
                "grammar_count": len(grammar_docs),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return EmbedIndexResult(
        vocab_count=len(vocab_docs),
        grammar_count=len(grammar_docs),
        dimension=dimension,
        embed_model=embed_model,
    )


def _check_dimension(*vector_groups: list[list[float]]) -> int | None:
    dimension: int | None = None
    for vectors in vector_groups:
        for vector in vectors:
            if dimension is None:
                dimension = len(vector)
            elif len(vector) != dimension:
                raise ValueError(f"Inconsistent embedding dimensions: {len(vector)} != {dimension}")
    return dimension


def _write_jsonl(path: Path, records: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
