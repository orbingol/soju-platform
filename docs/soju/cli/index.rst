:orphan:

CLI reference
=============

Console tools live under ``src/soju/cli/`` and install with ``uv sync``. Run from the
repo root unless noted. Option lists are generated from the live Typer apps
(``sphinxcontrib-typer``).

**Validate after any data change:** ``uv run poe validate`` or
``docker compose --profile validate run --rm validate``

- :doc:`validate-schemas`
- :doc:`align`
- :doc:`registry`
- :doc:`import`
- :doc:`promote`
- :doc:`translate-words`
- :doc:`fill-examples`
- :doc:`fill-verbs`
- :doc:`soju`

See :doc:`/development/poe` for shortcut tasks and :doc:`/development/docker` for
Compose services that wrap these tools.
