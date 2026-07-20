# AGENTS.md

Essential context for human contributors and AI coding agents (Cursor, Copilot, Claude Code, OpenCode, and similar) working on the **Soju (소주)** Korean language learning platform.

## Local instructions (optional)

If an `AGENTS.local.md` file exists at the repository root, agents **should also read** it as supplementary guidance.

- `AGENTS.local.md` is **additive only**. It must not override, weaken, or contradict the rules in `AGENTS.md`. If a conflict appears, `AGENTS.md` wins.
- Treat it as personal or machine-local notes (shortcuts, environment quirks, in-flight context).
- If the file is absent, ignore it silently—do not ask the user to create one.
- A starter template is committed at [`AGENTS.local.md-example`](AGENTS.local.md-example); copy it to `AGENTS.local.md` and edit as needed (`cp AGENTS.local.md-example AGENTS.local.md`).

## Requirements

Use **uv** for Python and **poe-the-poet** for repo tasks (`uv run poe <task>`).

- Install deps: `uv sync`
- If `.venv` is missing or imports fail, ask the user to run that first.
- If **`uv` is not installed** (command not found), ask the user to install it. Do **not** attempt to install uv yourself. Point users to [uv](https://docs.astral.sh/uv/).

**Node / SvelteKit:** run the web app in Docker only. Do **not** run `npm install` on the host — use the `web_node_modules` compose volume. If `apps/web/node_modules/` exists locally, delete it.

## Quick commands

Assume Python commands run as `uv run …` or `uv run poe …` unless the venv is already active.

| Goal | Command |
|------|---------|
| Validate all data | `uv run poe validate` |
| Lint / pre-commit | `uv run poe lint` / `uv run poe pre-commit` |
| Web format (Docker) | `docker compose run --rm --no-deps web npm run format` |
| Validate in Docker | `docker compose --profile validate run --rm validate` / `uv run poe validate-docker` |
| Web dev | `docker compose up` → http://localhost:5173 |
| Import words (JSON) | `cat records.json \| uv run soju import words --topic <id> --stdin-json` |
| Import verbs (JSON) | `cat verbs.json \| uv run soju import verbs --stdin-json` |
| Promote local words | `uv run soju promote --topic <id>` |
| CLI help | `uv run soju --help` · `uv run soju <subcommand> --help` |
| Python tests | `uv run poe test` (unit + offline system; skips LLM) |
| System / LLM / coverage | `uv run poe test-system` · `uv run poe test-llm` · `uv run poe test-all` · `uv run poe coverage` |
| Build embedding cache | `uv run poe embed-index` (requires Ollama + embed model) |
| Build / serve docs | `uv run poe docs` · `uv run poe docs-serve` |

Docker Compose **project name:** `soju` (`name: soju` in `docker-compose.yml`). Containers use the `soju-` prefix; named volumes use `soju_`.

## Python CLI

One console entry is installed by `uv sync`: **`soju`**. Invoke as `uv run soju <subcommand> …`. Details: `docs/soju/cli/` (Sphinx: `uv run poe docs-serve`).

| Subcommand | Role |
|------------|------|
| **`import words` / `import verbs`** | **Only write path** for registry words/verbs (examples, topic refs, verb forms) |
| **`promote`** | Promote `local: true` topic entries into the registry |
| **`validate-schemas`** | JSON Schema check over data files (in `poe validate`) |
| **`align`** | Verb forms ↔ registry alignment (in `poe validate`) |
| **`registry`** | UUID / refs / **sense uniqueness** (hangul+english; homonyms OK) (in `poe validate`) |
| **`translate-words`** | Plain-text list → import JSON via Ollama (`poe translate-words`) |
| **`fill-examples`** | Generate missing noun/verb examples (Ollama or `--local`) |
| **`fill-verbs`** | Fill missing verb conjugation forms |
| **`embed-index`** | Build Ollama embedding cache for Practice retrieval (`data/cache/embeddings/`) |

**Poe shortcuts:** `validate`, `validate-schemas`, `validate-align`, `validate-registry`, `validate-docker`, `test`, `pre-commit`, `lint`, `import-words`, `import-verbs`, `translate-words`, `embed-index`, `docs`, `docs-serve`.

## Documentation

- [README.md](README.md) — project overview (non-technical)
- `docs/soju/` — Sphinx user guide (Furo, `.rst`): `development/` + `cli/`; `uv run poe docs` / `docs-serve`
- `.ai/commands/` — slash-command workflows that parse input and call `soju import` / `soju promote` / `soju embed-index` / `soju translate-words`

## Default workflow

### Boundaries

- Keep diffs focused: change only what the task requires; match existing patterns in the touched area.
- **Never hand-edit** canonical vocabulary under `data/content/registry/`, `data/content/topics/*/topic.yaml` (entry lists), `data/content/verbs/forms/`, or examples. Use **`soju import`** (and **`soju promote`** when promoting locals) instead.
- Topics: `data/content/topics/manifest.yaml` (files at `topics/<id>/topic.yaml`). Grammar: `data/content/grammar/` (manifest + `patterns/`). Web app: `apps/web/`.
- Registry uniqueness is **hangul + English meaning** (homonyms allowed). Optional `visibility: hidden` + `type: phrase` hides practice sentences from Word types/Flashcards; Practice/chat still see them.
- If a request is ambiguous or would require broad refactors, **stop and ask** rather than guessing.

### Steps

1. **Environment:** `uv sync` before running Python CLIs or validation.
2. **Vocabulary changes:** follow [Vocabulary writes](#vocabulary-writes)—always end with `uv run poe validate` (or Docker validate).
3. **Web UI:** place app code under `apps/web/`; data from `DATA_DIR` (`./data` on host, `/data` in Docker).
4. **Python tooling:** place CLI code under `src/soju/cli/`; services under `src/soju/services/`.
5. **Before finishing:** `uv run poe validate` after any `data/` change; run web tests in Docker when touching `apps/web/src/lib/`.

## Vocabulary writes

**`soju import` is the only supported write path** for canonical vocabulary. It updates the registry, examples store, and topic/verb files atomically.

### What agents must not do

- Edit `data/content/registry/vocabulary.yaml`, `data/content/registry/examples.yaml`, topic entry lists under `data/content/topics/`, or `data/content/verbs/forms/` by hand.
- Change `data/content/topics/manifest.yaml` or `data/content/grammar/manifest.yaml` unless the user asks (or the task clearly requires a new topic/pattern).
- Skip validation after an import.

### Words (`soju import words`)

| Mode | When to use | Command |
|------|-------------|---------|
| **New words** | Full records with hangul, romanization, english | `cat records.json \| uv run soju import words --topic <id> --stdin-json` |
| **Preview** | Before writing | add `--dry-run` |
| **Merge examples only** | Plain-text file; word **must already exist** | `uv run soju import words --topic <id> --file scratch/words.txt` |
| **From staging** | Reviewed staging YAML | `uv run soju import words --from-staging data/staging/vocabulary-candidates.yaml --topic <id>` |

- **`--topic`** — id from `data/content/topics/manifest.yaml` (e.g. `common`, `family`).
- **`--section`** — required when the topic has multiple sections.
- **`--stdin-json`** — JSON array or `{"records": [...]}`. Required for **new** words.
- Optional record fields: `type`, `examples`, `visibility` (`hidden`), `grammar_pattern`.

**Record shape:** `hangul`, `romanization`, `english`; optional `examples` as `[{ "hangul", "english" }]`. Romanization: Revised Romanization, lowercase, hyphenated (`hak-gyo`).

### Verbs (`soju import verbs`)

```bash
cat verbs.json | uv run soju import verbs --stdin-json
```

Each record needs `hangul`, `romanization`, `english`, `forms` (present/past/future × casual_polite/formal_polite); optional nested `examples`. Always use **`--stdin-json`**.

### Promote local entries (`soju promote`)

```bash
uv run soju promote --topic <id>
uv run soju promote --topic <id> --dry-run
```

### Required follow-up

```bash
uv run poe validate
```

Or: `docker compose --profile validate run --rm validate`

### AI slash commands (`.ai/commands/`)

| Command | CLI |
|---------|-----|
| `import-words` | `soju import words --topic common --stdin-json` |
| `import-words-to` | `soju import words --topic <id> --stdin-json` |
| `import-verbs` | `soju import verbs --stdin-json` |
| `import-staging` | `soju import words --from-staging …` |
| `promote-local` | `soju promote --topic <id>` |
| `translate-words` | `soju translate-words --file …` → `soju import words … --stdin-json` |
| `embed-index` | `soju embed-index` |

Read the matching `.ai/commands/*.md` file before running.

## Tasks common to all workflows

- Run `uv run poe validate` after any change under `data/`.
- Web unit tests: `apps/web/src/lib/` (`*.test.ts`); run in Docker: `docker compose exec web npm test` (or `docker compose run --rm web npm test`).
- Python unit tests: `uv run poe test`.
- Prefer the catalog above; expand flags/options from `docs/soju/cli/` or `uv run soju <subcommand> --help`.
