---
description: Promote reviewed staging vocabulary into a topic via soju import
mode: subagent
---

# Import from staging

Merge reviewed vocabulary from **`data/staging/`** into canonical data using **`soju import`**. Do not hand-edit registry or topic YAML.

## Input

User provides:

- **Staging file** — e.g. `data/staging/vocabulary-candidates.yaml` or a file under `data/staging/`
- **Topic id** — manifest key (e.g. `common`, `family`)

Staging files must match `data/schemas/staging_vocabulary.schema.json`:

```yaml
staging: true
entries:
  - id: <uuid>
    hangul: ...
    romanization: ...
    english: ...
    examples: [...]  # optional
```

## Workflow

1. Read the staging file and confirm `staging: true` and valid entries.
2. Dry run:

   ```bash
   uv run soju import words --from-staging data/staging/vocabulary-candidates.yaml --topic <topic> --dry-run
   ```

3. Write:

   ```bash
   uv run soju import words --from-staging data/staging/vocabulary-candidates.yaml --topic <topic>
   ```

4. Validate:

   ```bash
   uv run poe validate
   ```

5. Summarize what was added, merged, or skipped. Optionally note that the user may clear or archive the staging file after review.

## Notes

- Staging entries with UUIDs are merged into `data/content/registry/vocabulary.yaml` and referenced from the topic.
- Duplicate `hangul` in registry merges examples or adds a ref, per `soju import` rules.
- Exercise/story staging files (`data/staging/exercises/`, `data/staging/stories/`) are not imported by this command — only vocabulary staging.

## Output summary

- Staging path and topic id
- `soju import` report
- Validation result
