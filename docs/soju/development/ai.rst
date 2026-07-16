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
