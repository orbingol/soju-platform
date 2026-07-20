---
description: Translate a word list to import JSON via soju translate-words (Ollama)
mode: subagent
---

# Translate words (list → JSON)

Turn a plain-text word list into **`soju import` JSON** using Ollama, then
(usually) pipe into **`soju import words`**. Do **not** hand-edit
`data/content/registry/` or topic YAML.

This is the **Ollama** list → JSON path. For the same line format with the
**agent** filling hangul/romanization/english, use `/import-words` or
`/import-words-to` instead.

## Input

- Word list file path (preferred) or pasted lines written to a temp file
- Optional **topic id** for the follow-up import (default **`common`**)

One entry per line; optional example in parentheses. Ignore blank lines and `#` comments.

```
<entry> [(<example>)]
```

Same shape as `/import-words` (Hangul or English entry; example in `(...)`).

## Workflow

1. Ensure Ollama is reachable (unless `--dry-run` only).

2. Dry run (parse summary, no Ollama):

   ```bash
   uv run soju translate-words --file words.txt --dry-run
   ```

3. Translate to JSON:

   ```bash
   uv run soju translate-words --file words.txt -o records.json
   ```

   Or stdout:

   ```bash
   uv run soju translate-words --file words.txt > records.json
   ```

   Useful flags:

   - `--skip-existing` — omit entries already in the registry
   - `--level 1A` — course level for glosses (default `SOJU_LANGUAGE_LEVEL` or `1A`)
   - `--model …` / `--base-url …` — Ollama overrides

4. Preview import:

   ```bash
   cat records.json | uv run soju import words --topic <topic> --stdin-json --dry-run
   ```

5. Import:

   ```bash
   cat records.json | uv run soju import words --topic <topic> --stdin-json
   ```

6. Validate:

   ```bash
   uv run poe validate
   ```

## Notes

- `poe translate-words --file words.txt` only runs the translate step (stdout JSON).
- Romanization in the JSON is still required for new words on import; the translate CLI is expected to supply it.
- After large vocabulary changes that Practice should retrieve, consider `/embed-index`.

## Output summary

- Input file and topic id
- Translate dry-run / record count
- Import report and validation result
