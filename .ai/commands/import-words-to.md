---
description: Import a word list into a named words topic via soju import
mode: subagent
---

# Import words to a topic

Same parsing rules as **import-words**. Read `.ai/commands/import-words.md` for line format, language detection, and JSON record shape.

## Required: topic id

The user **must** provide an input source and a **topic id** (manifest key, not a file path).

```
/import-words-to <input> <topic>
```

Examples:

- `/import-words-to notes/travel.txt travel` → `--topic travel`
- Topic `family` → `data/content/topics/family/topic.yaml` (per `data/content/topics/manifest.yaml`)

Do **not** default to `common`.

## New topics

The topic id must exist in **`data/content/topics/manifest.yaml`**. Topic files are always `data/content/topics/<id>/topic.yaml` (derive-by-id). If the user requests a new topic:

1. Add a manifest entry (`label`, optional `description`)
2. Create `data/content/topics/<id>/topic.yaml` with `sections: []` (or empty sections) and the words_topic schema comment
3. Run import
4. Validate

Do not edit `data/content/topics/manifest.yaml` unless the user asks — topics appear on the site via the manifest and SvelteKit routes.

## Workflow

1. Resolve topic id from user input.
2. Parse lines → JSON array (see `import-words.md`).
3. Dry run:

   ```bash
   cat records.json | uv run soju import words --topic <topic> --stdin-json --dry-run
   ```

4. Write:

   ```bash
   cat records.json | uv run soju import words --topic <topic> --stdin-json
   # optional batch level:
   # cat records.json | uv run soju import words --topic <topic> --stdin-json --level 1A
   ```

5. `uv run poe validate` (or Docker validate profile).

Optional course `level`: see `import-words.md` (per-record `"level"` or CLI `--level`; omit = unassigned).

## Output summary

- Topic id and resolved topic path
- Import report and validation result
