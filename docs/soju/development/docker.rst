Docker
======

Compose services run the web app, FastAPI backend, and (by default) nginx.
The Compose **project name** is ``soju``: containers use the ``soju-`` prefix,
named volumes use ``soju_``.

Prod vs dev
-----------

**Dev (default via poe)** — Vite and FastAPI on the host; nginx is not started.

.. code-block:: bash

   uv run poe up
   # or
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up

**Prod** — only nginx is published. UI and API share ``http://localhost:8080``.

.. code-block:: bash

   uv run poe up-prod
   # or
   docker compose up

.. list-table::
   :header-rows: 1
   :widths: 18 28 54

   * - Mode
     - Host ports
     - Notes
   * - Dev
     - ``5173`` (Vite), ``8000`` (API)
     - ``PUBLIC_AI_BASE_URL=http://localhost:8000``
   * - Prod
     - ``8080`` (nginx)
     - nginx → ``web:5173`` + ``backend:8000``

Do not revive the old ``docker/piper`` TTS image — speech is served by the Soju backend.

Other commands
--------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Web unit tests
     - ``docker compose exec web npm test``
   * - Validate (canonical image)
     - ``docker compose --profile validate run --rm validate``
   * - Static web build
     - ``scripts/docker-build-web.sh`` (see :doc:`static-build`)

Optional profiles
------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Ollama (AI features, containerized)
     - ``docker compose --profile ollama up ollama ollama-pull``

See :doc:`ai` for Practice/Chat setup and :doc:`tts` for local speech.

Python CLIs on Docker
----------------------

Python CLIs (``soju import``, etc.) normally run on the host via ``uv run`` with
``./data`` bind-mounted paths — see :doc:`/cli/index`. They also work inside any
container with the repo mounted at ``/workspace`` and ``uv sync`` run once.

**Node / npm:** never run ``npm install`` on the host — use the ``web_node_modules``
Compose volume. If ``apps/web/node_modules/`` exists locally, delete it.
