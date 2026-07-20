# SPDX-License-Identifier: BSD-3-Clause
"""Cache paths for the Ollama embedding index (``data/cache/embeddings/``)."""

from __future__ import annotations

from pathlib import Path

from soju.core.config import data_root


def embeddings_cache_dir(root: Path | None = None) -> Path:
    """Return ``<data_root>/cache/embeddings``.

    Args:
        root: Optional data-root override.
    """
    return data_root(root) / "cache" / "embeddings"


def meta_json_path(root: Path | None = None) -> Path:
    """Return the cache metadata file path (embed model + vector dimension)."""
    return embeddings_cache_dir(root) / "meta.json"


def vocab_jsonl_path(root: Path | None = None) -> Path:
    """Return the vocabulary embeddings JSONL cache path."""
    return embeddings_cache_dir(root) / "vocab.jsonl"


def grammar_jsonl_path(root: Path | None = None) -> Path:
    """Return the grammar-pattern embeddings JSONL cache path."""
    return embeddings_cache_dir(root) / "grammar.jsonl"
