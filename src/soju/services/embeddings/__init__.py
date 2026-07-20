# SPDX-License-Identifier: BSD-3-Clause
"""Ollama embedding index for Practice retrieval (cache under ``data/cache/embeddings/``)."""

from __future__ import annotations

from soju.services.embeddings.build import (
    DEFAULT_EMBED_MODEL,
    EmbedFn,
    EmbedIndexResult,
    build_embedding_index,
    make_ollama_embed_fn,
)
from soju.services.embeddings.cosine import cosine_similarity
from soju.services.embeddings.documents import (
    GrammarDoc,
    VocabDoc,
    load_grammar_docs,
    load_vocab_docs,
)
from soju.services.embeddings.paths import (
    embeddings_cache_dir,
    grammar_jsonl_path,
    meta_json_path,
    vocab_jsonl_path,
)

__all__ = [
    "DEFAULT_EMBED_MODEL",
    "EmbedFn",
    "EmbedIndexResult",
    "GrammarDoc",
    "VocabDoc",
    "build_embedding_index",
    "cosine_similarity",
    "embeddings_cache_dir",
    "grammar_jsonl_path",
    "load_grammar_docs",
    "load_vocab_docs",
    "make_ollama_embed_fn",
    "meta_json_path",
    "vocab_jsonl_path",
]
