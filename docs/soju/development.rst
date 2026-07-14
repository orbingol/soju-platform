Development guide
=================

Technical setup for running and contributing to the Soju platform.

Run the site
------------

**Docker only for Node** — do not run ``npm install`` on the host.

.. code-block:: bash

   docker compose up

Open http://localhost:5173 (``web`` is the default service).

- **Education** — Word types, Grammar, Topics, Flashcards, Practice, Chat (AI features when enabled)
- Data is bind-mounted from ``./data`` at ``/data`` in the container

**Web unit tests** (Vitest) — run inside the web container; do not ``npm install`` on the host:

.. code-block:: bash

   docker compose exec web npm test

If the web service is not already up:

.. code-block:: bash

   docker compose run --rm web npm test

**Python unit tests** (host via uv):

.. code-block:: bash

   uv run poe test

Rebuild after Dockerfile changes:

.. code-block:: bash

   docker compose up --build web

Docker Compose project name: **``soju``** (containers use the ``soju-`` prefix).

Optional — AI practice & chat
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires a local OpenAI-compatible language model service and ``PUBLIC_AI_ENABLED=true`` in ``docker-compose.yml``.

**Host Ollama (desktop app)** — default setup:

.. code-block:: bash

   docker compose up web

Set ``PUBLIC_AI_BASE_URL`` to ``http://localhost:11434`` (the **browser** calls the API, not the web container). Allow CORS from the dev site — restart Ollama after setting:

.. code-block:: bash

   OLLAMA_ORIGINS=http://localhost:5173 ollama serve

On macOS with the Ollama app, quit Ollama and relaunch from a terminal:

.. code-block:: bash

   OLLAMA_ORIGINS="http://localhost:5173" open -a Ollama

**Ollama in Docker Compose:**

.. code-block:: bash

   docker compose --profile ollama up ollama ollama-pull web

The ``ollama`` services mount your host Ollama cache (default ``~/.ollama``) into the container. Downloads persist across restarts; ``ollama pull`` only fetches missing layers or updates. Override the path with ``OLLAMA_DATA_DIR`` if needed. The browser still uses ``http://localhost:11434`` because port ``11434`` is published to the host.

Model, API mode, and prompts are configured in ``docker-compose.yml`` under ``x-soju-web-environment``.

.. list-table::
   :header-rows: 1
   :widths: 28 32 40

   * - Variable
     - Values
     - Purpose
   * - ``PUBLIC_AI_ENABLED``
     - ``true`` / ``false``
     - Show Practice & Chat; call the model at runtime
   * - ``PUBLIC_AI_API_MODE``
     - ``chat-completions`` (default), ``conversations``
     - API adapter (``/v1/chat/completions`` vs ``/v1/conversations`` + ``/v1/responses``)
   * - ``PUBLIC_AI_BASE_URL``
     - e.g. ``http://localhost:11434``
     - OpenAI-compatible server root (**browser-reachable** URL)
   * - ``PUBLIC_AI_MODEL``
     - model id
     - Sent on each request
   * - ``PUBLIC_AI_SYSTEM_PROMPT``
     - text (supports ``{{tutor_name}}``)
     - Chat tutor system prompt; ``{{tutor_name}}`` is replaced with ``PUBLIC_AI_TUTOR_NAME``
   * - ``PUBLIC_AI_TUTOR_NAME``
     - e.g. ``Hee-jae (희재)``
     - Chat dock tutor display name (also fills ``{{tutor_name}}`` in the system prompt)
   * - ``PUBLIC_AI_CHAT_SUMMARY_TRIGGER``
     - positive integer (default ``10``)
     - Summarize older chat turns when message count exceeds this
   * - ``PUBLIC_AI_CHAT_KEEP_RECENT``
     - positive integer (default ``6``)
     - Recent turns kept verbatim after summarization
   * - ``PUBLIC_TTS_ENGINE``
     - ``piper`` (default) / ``browser``
     - Default speech engine (Settings can override)
   * - ``PUBLIC_TTS_PIPER_BASE_URL``
     - e.g. ``http://localhost:5500``
     - Piper TTS HTTP root (**browser-reachable**)
   * - ``PUBLIC_TTS_PIPER_VOICE``
     - e.g. ``ko-KR-SunHiNeural``
     - Edge neural voice id sent to local TTS ``/v1/audio/speech``

Legacy ``PUBLIC_OLLAMA_*`` names are still read as fallbacks.

Piper TTS (local speech)
~~~~~~~~~~~~~~~~~~~~~~~~

``docker compose up`` starts a ``piper`` service on port ``5500`` exposing ``/v1/audio/speech``.

**Korean note:** upstream Piper has no official Korean neural voice that works with stock ``piper-tts``.
The Soju TTS container therefore uses **edge-tts** with ``ko-KR-SunHiNeural`` (natural Korean; needs
network). Override the voice with ``PUBLIC_TTS_PIPER_VOICE`` (e.g. ``ko-KR-InJoonNeural``). Switch engines
under **Controls → Speech** (``piper`` local service, or ``browser`` Web Speech). If the local service
is down, the app falls back to the browser.

Static build (GitHub Pages)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   docker compose --profile build build web-build

The ``web-build`` target sets ``PUBLIC_AI_ENABLED=false``. Practice and Chat **routes are
included** in the build but **hidden from navigation** and show an inert gate if visited
directly — no model calls are made. This is intentional for public hosting.

Validate data
-------------

.. code-block:: bash

   uv run poe validate

Or in Docker:

.. code-block:: bash

   docker compose --profile validate run --rm validate

Runs JSON Schema checks (``soju-validate-schemas``), verb alignment (``soju-align``), and registry checks (``soju-registry``).

See :doc:`cli` for all CLI tools and import workflows.

Import vocabulary
-----------------

**Do not hand-edit** ``data/content/registry/``, topic entry lists, verb forms, or examples. Use **``soju-import``**:

.. code-block:: bash

   cat records.json | uv run soju-import words --topic common --stdin-json
   cat verbs.json   | uv run soju-import verbs --stdin-json
   uv run poe validate

AI slash commands in ``.ai/commands/`` parse input → call ``soju-import`` / ``soju-promote`` → validate.

Grammar lesson YAML under ``data/content/grammar/`` is authored directly (schemas apply); vocabulary still goes through ``soju-import``.

Local Python setup
------------------

.. code-block:: bash

   uv sync
   uv run poe validate

Build these docs
----------------

.. code-block:: bash

   uv run poe docs          # HTML → docs/_build/html/
   uv run poe docs-serve    # live-reload preview
   make -C docs html        # same as poe docs (Makefile)
   # Windows: docs\make.bat html

Editor support
--------------

With the `YAML extension <https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml>`_, ``.vscode/settings.json`` maps schemas to:

- ``data/content/registry/*.yaml``
- ``data/content/topics/manifest.yaml``, ``table.yaml``, and ``topics/<id>/topic.yaml``
- ``data/content/verbs/manifest.yaml``, ``table.yaml``, ``forms/*.yaml``, ``constructions/*.yaml``
- ``data/content/grammar/manifest.yaml``, ``patterns/*.yaml``
- ``data/content/words/table.yaml``
- ``data/staging/**/*.yaml``

Agent notes
-----------

See ``AGENTS.md`` at the repository root.

Data layout (overview)
----------------------

Canonical language data lives under ``data/content/``. Staging stays at ``data/staging/``. ``DATA_DIR`` remains ``./data`` (host) / ``/data`` (Docker).

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Area
     - Path
   * - Word & verb registry + examples
     - ``data/content/registry/`` (``vocabulary.yaml``, ``examples.yaml``, ``types.yaml``)
   * - Word topics
     - ``data/content/topics/<id>/topic.yaml`` (listed in ``manifest.yaml``)
   * - Verb forms
     - ``data/content/verbs/forms/`` (manifest + table in ``data/content/verbs/``)
   * - Grammar lessons
     - ``data/content/grammar/`` (``manifest.yaml`` + ``patterns/``)
   * - Staging (review before import)
     - ``data/staging/``

Schemas live in ``data/schemas/``. The web app reads YAML via ``DATA_DIR``.
