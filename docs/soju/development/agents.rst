Agent notes
===========

Rules for AI coding agents (Cursor, Copilot, Claude Code, OpenCode, and similar) live in
``AGENTS.md`` at the repository root — read it before making changes with an agent. It
covers, among other things:

- Required tools (``uv``, ``poe``) and the quick-command table.
- Write-path boundaries: canonical vocabulary, topic entry lists, verb forms, and
  examples must go through ``soju-import``/``soju-promote`` (see :doc:`import`), never
  hand-edited.
- Where app code, CLI code, and services live (``apps/web/``, ``src/soju/cli/``,
  ``src/soju/services/``).
- The default workflow: sync the environment, make focused changes, validate after any
  ``data/`` change, run web tests in Docker when touching ``apps/web/src/lib/``.

Local overrides
-----------------

If ``AGENTS.local.md`` exists at the repo root, agents should also read it as
supplementary, personal/machine-local guidance (shortcuts, environment quirks, in-flight
context). It is **additive only** — it must never override or contradict
``AGENTS.md``. Copy the committed template to get started:

.. code-block:: bash

   cp AGENTS.local.md-example AGENTS.local.md

If neither file exists or applies, agents should proceed without asking the user to
create one.
