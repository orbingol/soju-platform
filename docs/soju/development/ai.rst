AI practice & chat
==================

Practice and Chat talk to the **Soju backend** (OpenAI-compatible API behind nginx),
not directly to Ollama. ``docker compose up`` starts ``web``, ``backend``, and ``nginx``.
Set ``PUBLIC_AI_ENABLED=true`` (default in Compose).

**Host Ollama (desktop app)** — usual setup:

.. code-block:: bash

   docker compose up

Pull models on the host (defaults match backend YAML / ``ollama-pull``):

.. code-block:: bash

   ollama pull gemma4:e4b
   ollama pull nomic-embed-text

The backend reaches host Ollama at ``http://host.docker.internal:11434``
(see ``config/backend.yaml``). The **browser** calls ``PUBLIC_AI_BASE_URL``
(default ``http://localhost:8080``).

**Ollama in Docker Compose:**

.. code-block:: bash

   docker compose --profile ollama up ollama ollama-pull web

The ``ollama`` services mount your host Ollama cache (default ``~/.ollama``).
Override with ``OLLAMA_DATA_DIR`` if needed.

Browser env (Compose)
---------------------

.. list-table::
   :header-rows: 1
   :widths: 28 32 40

   * - Variable
     - Values
     - Purpose
   * - ``PUBLIC_AI_ENABLED``
     - ``true`` / ``false``
     - Show Practice & Chat
   * - ``PUBLIC_AI_BASE_URL``
     - e.g. ``http://localhost:8080``
     - Soju API root (nginx → FastAPI)
   * - ``PUBLIC_TTS_ENGINE``
     - ``local`` (default) / ``browser``
     - Default speech engine (Settings can override)

Chat model, embed model, tutor name/prompt, and TTS voice are loaded at runtime from
``GET /v1/soju/client-config`` (backend YAML). Legacy ``PUBLIC_OLLAMA_*`` / older
``PUBLIC_AI_MODEL`` names remain as fallbacks when set.

Backend config (YAML)
---------------------

Edit packaged defaults or overrides:

- Packaged: ``src/soju/backend/config/files/default_config.yaml``
- User: ``~/.config/soju/backend.yaml``
- Compose: ``config/backend.yaml`` (``llm.base_url`` for Docker)

Typical keys: ``llm.chat_model``, ``llm.embed_model``, ``llm.base_url``,
``client.system_prompt``, ``client.tutor_name``, ``tts.engine`` (``edge`` / ``piper``),
``tts.voice``.

Run the API on the host (optional):

.. code-block:: bash

   uv sync --group backend
   uv run soju backend --config config/backend.yaml

See :doc:`/cli/backend`.

Practice generation
-------------------

Practice builds a **level- and theme-grounded** session (one exercise type at a time)
instead of dumping the full registry into the prompt.

**Content**

- Levels come from ``data/content/levels.yaml`` (guidance + optional ``grammar_summary``).
- Themes come from ``data/content/practice/themes.yaml`` (café, directions, family, daily
  routine, shopping). The UI also accepts a custom free-text theme.

**Embedding index (offline CLI)**

Before Generate can retrieve vocabulary, build the cache once (and again after large
registry/grammar changes):

.. code-block:: bash

   uv run poe embed-index

This writes ``data/cache/embeddings/`` (gitignored). See :doc:`/cli/embed-index`.
Python uses ``OLLAMA_HOST`` + ``SOJU_EMBED_MODEL`` (default ``nomic-embed-text``).
Keep that model in sync with backend ``llm.embed_model`` / client-config.

**Retrieve (dev-only API)**

Flow on **Generate session**:

1. Browser embeds the theme via Soju ``/v1/embeddings``.
2. Browser ``POST``\ s ``{ level, queryVector }`` to ``/api/practice/retrieve``.
3. The SvelteKit endpoint (dev server only) filters the cache by level, ranks by cosine
   similarity, and returns hangul + grammar snippets.
4. Browser calls chat completions through the Soju API with that RAG payload.

``/api/practice/retrieve`` is **dev-only** (same gate as ``/api/staging``): it runs under
``vite dev`` / ``docker compose up``, not in the static production build. Missing or
corrupt cache returns ``503`` with a hint to run ``poe embed-index``.

**UI controls**

Level → Theme (or Custom) → Exercise type (sentences / questions / fill-in-blank /
story / vocabulary candidates) → Count → Generate. Results show the active type; any
``vocabulary_candidates`` are listed as hangul — english (display only; no add-to-vocab).
