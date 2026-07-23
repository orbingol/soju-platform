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
2. Start Soju:

   ```bash
   docker compose up
   ```

3. In your browser, open [http://localhost:8080](http://localhost:8080).

To stop, press `Ctrl+C` in the terminal (or quit Docker Desktop).

Browsing words, grammar, and flashcards works out of the box. Practice and Chat need a local AI model (optional):

1. Install [Ollama](https://ollama.com/download).
2. Pull the default models:

   ```bash
   ollama pull gemma4:e4b
   ollama pull nomic-embed-text
   ```

3. Start Soju with `docker compose up`. With Ollama running on the host, Practice and Chat work in the browser at [http://localhost:8080](http://localhost:8080).

## For Power Users and Developers

Requires [uv](https://docs.astral.sh/uv/) and Docker. From the repo root:

```bash
uv sync
uv run poe up        # Vite :5173 + API :8000
uv run poe up-prod   # nginx :8080 (same as docker compose up)
```

Validation, tests, docs, and the rest of the tooling live in the Sphinx guide:

```bash
uv run poe docs-serve
```

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
