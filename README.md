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

## For Users

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.

1. Open a terminal in this project folder.
2. Start Soju:

   ```bash
   docker compose up
   ```

3. In your browser, open [http://localhost:5173](http://localhost:5173).

To stop, press `Ctrl+C` in the terminal (or quit Docker Desktop).

Browsing words, grammar, and flashcards works out of the box. Practice and Chat need a local AI model (optional) — see the docs under **For Developers** if you want those.

## For Developers

Requires [uv](https://docs.astral.sh/uv/). From the repo root:

```bash
uv sync
uv run poe docs-serve   # Documentation
uv run poe validate     # Data checks
uv run poe test         # Python tests
```

* Web app still runs via Docker: `docker compose up`
* Agent rules: `AGENTS.md`

## License

- **Code** (`src/`, `apps/`, tooling): [BSD 3-Clause](LICENSE)
- **Content & data** (`data/content/`): [CC BY 4.0](data/content/LICENSE)

## Author(s)

- Onur R. Bingol, Ph.D. ([@orbingol](https://github.com/orbingol))
