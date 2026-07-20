``soju embed-index``
====================

**Purpose:** Build the Ollama embedding cache used by Practice retrieval
(``data/cache/embeddings/``). Embeds every registry vocabulary entry and every
grammar pattern from the grammar manifest.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/grammar/manifest.yaml``
   * - **Writes**
     - ``data/cache/embeddings/{meta.json,vocab.jsonl,grammar.jsonl}`` (gitignored)
   * - **Exit codes**
     - ``0`` success · ``1`` Ollama / embed failure · ``2`` invalid flags

.. typer:: soju.cli.embed.app
   :prog: soju embed-index
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju embed-index --dry-run
   uv run poe embed-index
   uv run soju embed-index --embed-model nomic-embed-text --batch-size 32

Requires a reachable Ollama server with the embedding model pulled (default
``nomic-embed-text``, or ``SOJU_EMBED_MODEL`` / ``--embed-model``). The browser
Practice UI embeds the theme with the same model via ``PUBLIC_AI_EMBED_MODEL`` —
keep those in sync. See :doc:`/development/ai` for the full Practice flow.
