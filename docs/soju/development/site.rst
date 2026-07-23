Run the site
============

**Docker only for Node** — do not run ``npm install`` on the host.

.. code-block:: bash

   uv run poe up
   # or: docker compose -f docker-compose.yml -f docker-compose.dev.yml up

Open http://localhost:5173 (dev). For prod (nginx :8080), use ``uv run poe up-prod`` —
see :doc:`docker`.

- **Education** — Word types, Grammar, Topics, Flashcards, Practice, Chat (AI features when enabled)
- Data is bind-mounted from ``./data`` at ``/data`` in the container

**Web unit tests** (Vitest) — run inside the web container; do not ``npm install`` on the host:

.. code-block:: bash

   docker compose exec web npm test

If the web service is not already up:

.. code-block:: bash

   docker compose run --rm web npm test

**Python tests** (host via uv):

.. code-block:: bash

   uv run poe test
   uv run poe test-system
   uv run poe test-all
   uv run poe coverage

``poe test`` runs unit and offline system tests (skips ``@pytest.mark.llm``).
``poe test-all`` also runs LLM tests (needs a reachable Ollama).
Optional LLM-only suite: ``uv run poe test-llm``.

Rebuild after Dockerfile changes:

.. code-block:: bash

   docker compose up --build web

Docker Compose project name: ``soju`` (containers use the ``soju-`` prefix).
