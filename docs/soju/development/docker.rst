Docker
======

Compose services run the web app, FastAPI backend, Sphinx docs, and (in prod) nginx.
The Compose **project name** is ``soju``: containers use the ``soju-`` prefix,
named volumes use ``soju_``. Services share the internal ``soju`` bridge network.

Prod vs dev
-----------

**Dev (default via poe)** — Vite, FastAPI, and docs published on the host; nginx is not
started. Live-reload Sphinx via ``sphinx-autobuild``.

.. code-block:: bash

   uv run poe up
   # or
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up

**Prod** — only nginx is published (``:8080``). Backend, Vite, and docs stay on the
Compose network.

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
     - ``14321`` (UI), ``14322`` (API), ``14323`` (docs)
     - ``PUBLIC_AI_BASE_URL=http://localhost:14322``; config ``docker/soju/backend.dev.yaml``
   * - Prod
     - ``8080`` (nginx only)
     - ``/`` UI · ``/api/`` FastAPI · ``/docs/`` Sphinx; ``PUBLIC_AI_BASE_URL=/api``;
       config ``docker/soju/backend.yaml`` (``root_path: /api``)
   * - Internal
     - (listen ports)
     - ``web:14321`` · ``backend:14322`` · ``docs:14323`` on network ``soju``

Host Ollama (desktop app) is reached from the backend via ``host.docker.internal:11434``
(see ``docker/soju/backend.yaml``).

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
