---
description: Promote local topic entries into the word registry via soju promote
mode: subagent
---

# Promote local topic entries

Move **`local: true`** word entries from a topic file into **`data/content/registry/vocabulary.yaml`**, replacing locals with registry refs. Use **`soju promote`** — do not hand-edit YAML.

## When to use

Topic files may contain inline entries (with `local: true`) before they are promoted to the global registry. After review, promote them so other topics can reference the same word by UUID.

## Input

User provides a **topic id** (e.g. `family`).

## Workflow

1. Inspect `data/content/topics/<topic>/topic.yaml` for entries with `local: true`.
2. Dry run:

   ```bash
   uv run soju promote --topic <topic> --dry-run
   ```

3. Promote:

   ```bash
   uv run soju promote --topic <topic>
   ```

4. Validate:

   ```bash
   uv run poe validate
   ```

## Behavior

- Each local entry is appended to `data/content/registry/vocabulary.yaml` (unless `hangul` already exists — then the topic ref points at the existing registry row).
- The topic entry becomes `{ ref: <uuid> }`.
- Local-only fields are not left behind after promotion.

## Output summary

- Topic id
- Count promoted / skipped
- Validation result
