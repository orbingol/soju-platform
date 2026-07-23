# Soju (소주) Platform

## Introduction

An **experimental** Korean language learning platform: vocabulary, grammar, and practice in one place.

![Education](/docs/_static/soju-education.png?raw=true "Soju Education")

## Features

- **Browse verbs** — dictionary forms, common conjugations, and example sentences
- **Browse words** — vocabulary by word type and by topic (common, family, time, place, and more)
- **Grammar** — particles, patterns, connectors, and question words with short explanations and example conversations
- **Flashcards** — flip cards to review vocabulary; mark what you know and what to revisit
- **Listen** — text-to-speech for Korean on supported browsers
- **Practice** — generated exercises from your vocabulary (when AI features are enabled locally)
- **Chat** — ask questions and practice with an AI tutor (when enabled locally)

## For Regular Users

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.

1. Open a terminal in this project folder.
2. Start Soju in prod mode:

   ```bash
   docker compose up
   # or: uv run poe up-prod
   ```

   For Vite + FastAPI on the host (dev): `uv run poe up` or
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`.

3. In your browser, open [http://localhost:8080](http://localhost:8080) (prod) or
   [http://localhost:5173](http://localhost:5173) (dev).

To stop, press `Ctrl+C` in the terminal (or quit Docker Desktop).

Browsing words, grammar, and flashcards works out of the box. Practice and Chat need a local AI model (optional):

1. Install [Ollama](https://ollama.com/download).
2. Pull the default models:

   ```bash
   ollama pull gemma4:e4b
   ollama pull nomic-embed-text
   ```

3. Start Soju in prod mode with `docker compose up` / `uv run poe up-prod` (app + API at [http://localhost:8080](http://localhost:8080) via nginx). With Ollama running on the host, Practice and Chat work in the browser. For Vite/HMR on :5173 and API on :8000, use `uv run poe up`.

## For Power Users and Developers

Requires [uv](https://docs.astral.sh/uv/). From the repo root:

```bash
uv sync
uv sync --group backend   # optional: soju backend / FastAPI
uv run poe docs-serve   # Documentation
uv run poe validate     # Data checks
uv run poe test         # Python tests
```

* Web + API via Docker: `uv run poe up` → Vite :5173 + API :8000 · or `uv run poe up-prod` → http://localhost:8080
* Agent rules: `AGENTS.md`

## License

- **Code** (`src/`, `apps/`, tooling): [BSD 3-Clause](LICENSE)
- **Content & data** (`data/content/`): [CC BY 4.0](data/content/LICENSE)

## Author(s)

- Onur R. Bingol, Ph.D. ([@orbingol](https://github.com/orbingol))

### Note from the Author

Hi there! 👋

I built Soju Platform as a personal practice companion while taking Korean classes.
It helps me review vocabulary, grammar, and small exercises between lessons.
It is **not** a full e-learning course, and it is not trying to be one.

Things are still experimental: content and features come and go as my studies do.
Please keep expectations light and enjoy poking around if anything here is useful to you too.

Have fun! ✨🍶
