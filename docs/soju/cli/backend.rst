``soju backend``
================

**Purpose:** Run the FastAPI Soju API (OpenAI-compatible chat/embeddings proxy + local TTS).

Requires the optional backend dependency group:

.. code-block:: bash

   uv sync --group backend

Config search order: ``--config`` path → ``~/.config/soju/backend.yaml`` (if present) →
packaged defaults under ``src/soju/backend/config/files/``. Compose mounts
``docker/soju/backend.yaml`` into the backend container.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - Packaged ``default_config.yaml``, optional user/Compose YAML override
   * - **Serves**
     - ``/health``, ``/v1/models``, ``/v1/chat/completions``, ``/v1/embeddings``,
       ``/v1/audio/speech``, ``/v1/soju/client-config``
   * - **Exit codes**
     - ``0`` running until stopped · ``1`` missing deps / bad config

.. typer:: soju.backend.cli.app
   :prog: soju backend
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju backend --help
   uv run soju backend --config docker/soju/backend.yaml
   uv run soju backend --host 127.0.0.1 --port 14322

With ``uv run poe up``, the UI is on ``http://localhost:14321``, the API on
``http://localhost:14322``, and docs on ``http://localhost:14323``.
With ``uv run poe up-prod`` / ``docker compose up``, only nginx is public:
``http://localhost:8080/`` (UI), ``/api/`` (FastAPI), ``/docs/`` (Sphinx).
See :doc:`/development/ai` and :doc:`/development/tts`.
