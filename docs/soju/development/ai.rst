AI practice & chat
==================

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

Pull both the chat model and the embedding model (defaults in ``docker-compose.yml``):

.. code-block:: bash

   ollama pull gemma4:e4b
   ollama pull nomic-embed-text

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
     - Chat / Practice generation model
   * - ``PUBLIC_AI_EMBED_MODEL``
     - model id (default ``nomic-embed-text``)
     - Browser-side theme embedding for Practice retrieval (must match ``soju embed-index``)
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

**Retrieve (dev-only API)**

Flow on **Generate session**:

1. Browser embeds the theme text via Ollama ``/api/embeddings`` (``PUBLIC_AI_EMBED_MODEL``).
2. Browser ``POST``\ s ``{ level, queryVector }`` to ``/api/practice/retrieve``.
3. The SvelteKit endpoint (dev server only) filters the cache by level, ranks by cosine
   similarity, and returns hangul + grammar snippets.
4. Browser calls the chat model with that RAG payload to produce JSON for the selected
   exercise type / count.

``/api/practice/retrieve`` is **dev-only** (same gate as ``/api/staging``): it runs under
``vite dev`` / ``docker compose up``, not in the static production build. Missing or
corrupt cache returns ``503`` with a hint to run ``poe embed-index``.

**UI controls**

Level → Theme (or Custom) → Exercise type (sentences / questions / fill-in-blank /
story / vocabulary candidates) → Count → Generate. Results show the active type; any
``vocabulary_candidates`` are listed as hangul — english (display only; no add-to-vocab).
