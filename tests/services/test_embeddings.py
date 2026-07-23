# SPDX-License-Identifier: BSD-3-Clause
"""Embedding index build/cosine/path helpers (mocked vectors, no live Ollama)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soju.services.embeddings.build import (
    build_embedding_index,
    make_ollama_embed_fn,
)
from soju.services.embeddings.cosine import cosine_similarity
from soju.services.embeddings.paths import (
    embeddings_cache_dir,
    grammar_jsonl_path,
    meta_json_path,
    vocab_jsonl_path,
)
from soju.services.embeddings.documents import (
    load_grammar_docs,
    load_vocab_docs,
)
from tests.constants import VERB_ID, WORD_ID


def test_cache_paths_resolve_under_data_cache_embeddings(data_root: Path) -> None:
    root = data_root
    expected_dir = root / "cache" / "embeddings"
    assert embeddings_cache_dir(root) == expected_dir
    assert meta_json_path(root) == expected_dir / "meta.json"
    assert vocab_jsonl_path(root) == expected_dir / "vocab.jsonl"
    assert grammar_jsonl_path(root) == expected_dir / "grammar.jsonl"


def test_cosine_similarity_known_values() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_zero_vector_is_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_cosine_similarity_length_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="length mismatch"):
        cosine_similarity([1.0], [1.0, 2.0])


def test_load_vocab_docs_includes_hangul_and_english(data_root: Path) -> None:
    docs = load_vocab_docs(data_root)
    ids = {doc.id for doc in docs}
    assert {WORD_ID, VERB_ID} <= ids
    school = next(doc for doc in docs if doc.id == WORD_ID)
    assert school.hangul == "학교"
    assert "school" in school.text
    assert "학교" in school.text
    assert school.level == "1A"


def test_load_grammar_docs_uses_manifest_description(data_root: Path) -> None:
    docs = load_grammar_docs(data_root)
    assert len(docs) == 1
    do_doc = docs[0]
    assert do_doc.id == "do"
    assert do_doc.form == "-도"
    assert "Additive particle" in do_doc.summary
    assert do_doc.form in do_doc.text
    assert do_doc.level == "1A"


def test_load_grammar_docs_empty_without_manifest(tmp_path: Path) -> None:
    assert load_grammar_docs(tmp_path) == []


def _fake_embed(dimension: int = 3):
    def embed_fn(texts):
        return [[float(i)] * dimension for i, _ in enumerate(texts, start=1)]

    return embed_fn


def test_build_embedding_index_writes_cache_files(data_root: Path) -> None:
    result = build_embedding_index(embed_fn=_fake_embed(), embed_model="mock-model", root=data_root)

    assert result.vocab_count == len(load_vocab_docs(data_root))
    assert result.grammar_count == len(load_grammar_docs(data_root))
    assert result.dimension == 3
    assert result.embed_model == "mock-model"

    meta = json.loads(meta_json_path(data_root).read_text(encoding="utf-8"))
    assert meta == {
        "embed_model": "mock-model",
        "dimension": 3,
        "vocab_count": result.vocab_count,
        "grammar_count": result.grammar_count,
    }

    vocab_lines = vocab_jsonl_path(data_root).read_text(encoding="utf-8").strip().splitlines()
    assert len(vocab_lines) == result.vocab_count
    first_vocab = json.loads(vocab_lines[0])
    assert set(first_vocab) == {"id", "hangul", "romanization", "english", "type", "level", "embedding"}
    assert len(first_vocab["embedding"]) == 3

    grammar_lines = grammar_jsonl_path(data_root).read_text(encoding="utf-8").strip().splitlines()
    assert len(grammar_lines) == result.grammar_count
    first_grammar = json.loads(grammar_lines[0])
    assert set(first_grammar) == {"id", "form", "english", "category", "summary", "level", "embedding"}


def test_build_embedding_index_dimension_mismatch_raises(data_root: Path) -> None:
    def bad_embed_fn(texts):
        return [[0.1, 0.2] if i == 0 else [0.1, 0.2, 0.3] for i, _ in enumerate(texts)]

    with pytest.raises(ValueError, match="Inconsistent embedding dimensions"):
        build_embedding_index(embed_fn=bad_embed_fn, embed_model="mock-model", root=data_root)


def test_make_ollama_embed_fn_chunks_and_reports_progress() -> None:
    calls: list[list[str]] = []

    class FakeClient:
        def embed_batch(self, texts):
            calls.append(list(texts))
            return [[1.0] for _ in texts]

    progress: list[tuple[int, int]] = []
    embed_fn = make_ollama_embed_fn(FakeClient(), batch_size=2, on_progress=lambda done, total: progress.append((done, total)))

    vectors = embed_fn(["a", "b", "c"])

    assert vectors == [[1.0], [1.0], [1.0]]
    assert calls == [["a", "b"], ["c"]]
    assert progress == [(2, 3), (3, 3)]


def test_make_ollama_embed_fn_handles_empty_input() -> None:
    class FakeClient:
        def embed_batch(self, texts):
            raise AssertionError("should not be called for empty input")

    embed_fn = make_ollama_embed_fn(FakeClient(), batch_size=4)
    assert embed_fn([]) == []
