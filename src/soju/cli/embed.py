# SPDX-License-Identifier: BSD-3-Clause
"""``soju embed-index`` command."""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from soju.cli._common import flag, make_app
from soju.cli._ollama import require_ollama_client
from soju.llm.base import LlmError
from soju.llm.ollama import DEFAULT_BASE_URL
from soju.services.embeddings.build import (
    DEFAULT_EMBED_MODEL,
    build_embedding_index,
    make_ollama_embed_fn,
)
from soju.services.embeddings.documents import (
    load_grammar_docs,
    load_vocab_docs,
)

app = make_app()


@app.command()
def build(
    base_url: Annotated[str, typer.Option("--base-url", help="Ollama base URL")] = DEFAULT_BASE_URL,
    embed_model: Annotated[
        str,
        typer.Option("--embed-model", help="Ollama embedding model (default: SOJU_EMBED_MODEL or nomic-embed-text)"),
    ] = DEFAULT_EMBED_MODEL,
    batch_size: Annotated[
        int,
        typer.Option("--batch-size", help="Documents per Ollama /api/embed batch request"),
    ] = 32,
    dry_run: Annotated[
        bool,
        flag("--dry-run", help="Count documents to embed without calling Ollama"),
    ] = False,
) -> None:
    """Build the Ollama embedding cache for Practice retrieval (data/cache/embeddings/)."""
    if batch_size < 1:
        print("Error: --batch-size must be at least 1.", file=sys.stderr)
        raise typer.Exit(2)

    if dry_run:
        vocab_docs = load_vocab_docs()
        grammar_docs = load_grammar_docs()
        print(
            f"Would embed {len(vocab_docs)} vocabulary entries and {len(grammar_docs)} grammar patterns using model {embed_model!r} at {base_url}.",
            file=sys.stderr,
        )
        return

    client = require_ollama_client(model=embed_model, base_url=base_url)

    def on_progress(done: int, total: int) -> None:
        print(f"Embedded {done}/{total}…", file=sys.stderr, flush=True)

    embed_fn = make_ollama_embed_fn(client, batch_size=batch_size, on_progress=on_progress)

    try:
        result = build_embedding_index(embed_fn=embed_fn, embed_model=embed_model)
    except (LlmError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    print(
        f"Embedded {result.vocab_count} vocabulary entries and {result.grammar_count} grammar patterns (dimension={result.dimension}) into data/cache/embeddings/.",
        file=sys.stderr,
    )
