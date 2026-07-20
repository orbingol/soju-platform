---
description: Build the Practice embedding cache via soju embed-index
mode: subagent
---

# Embed index (Practice retrieval)

Rebuild the Ollama embedding cache used by Practice theme retrieval
(`data/cache/embeddings/`). Run this after vocabulary, grammar, or level/theme
content changes that should affect Practice RAG — or when Practice retrieve
fails because the cache is missing/stale.

Do **not** hand-edit files under `data/cache/embeddings/`.

## When to use

- New or updated registry words / grammar patterns that Practice should retrieve
- Missing `data/cache/embeddings/{meta.json,vocab.jsonl,grammar.jsonl}`
- Embed model changed (must match web `PUBLIC_AI_EMBED_MODEL` / `SOJU_EMBED_MODEL`)

## Prerequisites

- Reachable Ollama (host or `docker compose --profile ollama up ollama ollama-pull`)
- Embedding model pulled (default **`nomic-embed-text`**)

## Workflow

1. Dry run (count docs, no Ollama call):

   ```bash
   uv run soju embed-index --dry-run
   ```

   Or: `uv run poe embed-index` only for the real build — prefer the CLI for `--dry-run`.

2. Build:

   ```bash
   uv run soju embed-index
   ```

   Optional:

   ```bash
   uv run soju embed-index --embed-model nomic-embed-text --base-url http://localhost:11434
   ```

3. Confirm outputs exist:

   - `data/cache/embeddings/meta.json`
   - `data/cache/embeddings/vocab.jsonl`
   - `data/cache/embeddings/grammar.jsonl`

4. Reminder: web Practice must use the **same** embed model (`PUBLIC_AI_EMBED_MODEL` in Compose / `.env`).

## Notes

- Cache is gitignored; each machine/container needs its own build.
- This does **not** replace `poe validate` after data edits — run validate separately when registry/grammar YAML changed.
- Does not import vocabulary; use `/import-words` (or translate-words → import) for that.

## Output summary

- Dry-run counts (if run)
- Embed report (vocab count, grammar count, dimension)
- Model name and whether cache files were written
