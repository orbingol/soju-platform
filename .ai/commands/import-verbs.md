---
description: Import verbs via soju-import (JSON with conjugations)
mode: subagent
---

# Import verbs

Parse a plain-text verb list, build JSON with **full conjugations**, and import via **`soju-import verbs --stdin-json`**. Do **not** hand-edit `data/content/registry/vocabulary.yaml`, `data/content/verbs/forms/`, or `data/content/registry/examples.yaml`.

## Input

One dictionary-form verb per line; optional example in parentheses. Ignore blank lines and `#` comments.

```
<entry> [(<example>)]
```

## Language detection (your job)

| Line kind | Action |
|-----------|--------|
| Hangul (사전형, `…다`) | Derive english, romanization, all forms |
| English (`to …`) | Derive Hangul dictionary form and conjugations |
| Conjugated Hangul without clear dictionary form | Skip and report |

Read `data/content/verbs/table.yaml` for required tense groups and variants (`present` / `past`, `casual_polite` / `formal_polite`).

## JSON for soju-import

```json
[
  {
    "hangul": "가다",
    "romanization": "ga-da",
    "english": "to go",
    "forms": {
      "present": {
        "casual_polite": "가요",
        "formal_polite": "갑니다"
      },
      "past": {
        "casual_polite": "갔어요",
        "formal_polite": "갔습니다"
      }
    },
    "examples": {
      "present": {
        "casual_polite": [
          { "hangul": "저는 학교에 가요.", "english": "I go to school." }
        ]
      }
    }
  }
]
```

- **`forms`** — required; keys must match `data/content/verbs/manifest.yaml` form files
- **`examples`** — optional; nest by tense → variant → array of `{hangul, english}`
- Place each parenthesized example under the tense/variant it demonstrates (default `present.casual_polite` when unclear)

## Workflow

1. Read `data/content/verbs/table.yaml` and existing `data/content/registry/vocabulary.yaml` (skip duplicate **hangul + English meaning**; same hangul with a different gloss is a homonym).
2. Build JSON records for new verbs only.
3. Dry run:

   ```bash
   cat records.json | uv run soju-import verbs --stdin-json --dry-run
   ```

4. Write:

   ```bash
   cat records.json | uv run soju-import verbs --stdin-json
   ```

5. Validate:

   ```bash
   uv run poe validate
   ```

6. Fix schema, alignment, or registry errors before finishing.

## Output summary

- Per line: added / duplicate / skipped
- `soju-import` report
- Validation and alignment result

Verb file import (`--file`) is **not** supported for new verbs — use **`--stdin-json`** only.
