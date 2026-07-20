---
description: Import a word list into the common words topic via soju import
mode: subagent
---

# Import words (common topic)

Parse a plain-text word list, build JSON records, and import via **`soju import`**. Do **not** hand-edit `data/content/registry/` or `data/content/topics/` YAML.

## Input

- Word list: file path, `@`-mentioned file, or pasted lines
- Default topic: **`common`** (`data/content/topics/common/topic.yaml` via manifest)

One entry per line; optional example in parentheses. Ignore blank lines and `#` comments.

```
<entry> [(<example>)]
```

## Language detection (your job)

For each line, produce a full record with `hangul`, `romanization`, `english`, and optional `examples`.

| Line kind | Action |
|-----------|--------|
| Hangul entry | Derive romanization + English |
| English entry | Derive Hangul + romanization |
| Example in `(...)` | Fill both `hangul` and `english` on the example object |
| Ambiguous / romanization-only | Skip and report |

Romanization: Revised Romanization, lowercase, hyphenated (`hak-gyo`).

## JSON for soju import

Pipe a JSON **array** (or `{"records": [...]}`) to stdin:

```json
[
  {
    "hangul": "학교",
    "romanization": "hak-gyo",
    "english": "school",
    "examples": [
      { "hangul": "학교에 가요.", "english": "I go to school." }
    ]
  }
]
```

Omit `examples` when the line has no parenthesized example.

## Workflow

1. Parse all lines into JSON records (skip duplicates by **hangul + English meaning** against the registry when possible — query `data/content/registry/vocabulary.yaml` or run `soju import words --topic common --stdin-json --dry-run` first). Same hangul with a different English gloss is a new homonym entry.
2. Import (preview):

   ```bash
   cat records.json | uv run soju import words --topic common --stdin-json --dry-run
   ```

3. Import (write):

   ```bash
   cat records.json | uv run soju import words --topic common --stdin-json
   ```

4. Validate:

   ```bash
   uv run poe validate
   ```

   Or in Docker: `docker compose --profile validate run --rm validate`

5. Fix any errors before finishing.

## Merge-only shortcut (`--file`)

`soju import words --topic common --file words.txt` only merges **examples** for words **already in the registry**. It cannot add new words (missing romanization/english). For new vocabulary, always use **`--stdin-json`**.

## Output summary

- Input source and topic (`common`)
- Per line: added / merged examples / duplicate / skipped
- `soju import` report line
- Validation result

Do not edit `data/content/topics/manifest.yaml` unless the user asks — topics appear on the site via the manifest and SvelteKit routes.
