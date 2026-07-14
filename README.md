# Soju (소주) Platform

## Introduction

An **experimental** Korean language learning platform: vocabulary, grammar, and light practice in one place.

### Important Note

Soju Platform is a personal study project: curated word and verb lists, example sentences, and simple tools to review and practice.
**It is not a finished product**; features and content change as the project evolves.

## Features

- **Browse verbs** — dictionary forms, common conjugations, and example sentences
- **Browse words** — vocabulary by word type and by topic (common, family, time, place, and more)
- **Grammar** — particles, patterns, connectors, and question words with short explanations and example conversations
- **Flashcards** — flip cards to review vocabulary; mark what you know and what to revisit
- **Listen** — text-to-speech for Korean on supported browsers
- **Practice** — generated exercises from your vocabulary (when AI features are enabled locally)
- **Chat** — ask questions and practice with an AI tutor (when enabled locally)

## For Developers

Technical setup, Docker, validation, and CLI tools:

```bash
uv sync
uv run poe docs-serve
```

- Sphinx user guide (Furo): `docs/soju/` — build with `uv run poe docs`, preview with `uv run poe docs-serve`
- [AGENTS.md](AGENTS.md) — notes for AI coding agents working in this repo

## License

- **Code** (`src/`, `apps/`, tooling): [BSD 3-Clause](LICENSE)
- **Content & data** (`data/content/`): [CC BY 4.0](data/content/LICENSE)

## Author(s)

- Onur R. Bingol, Ph.D. ([@orbingol](https://github.com/orbingol))
