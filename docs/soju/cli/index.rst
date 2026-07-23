:orphan:

CLI reference
=============

The unified ``soju`` console entry lives under ``src/soju/cli/`` and installs with
``uv sync``. Run from the repo root unless noted. Option lists are generated from
the live Typer apps (``sphinxcontrib-typer``).

.. code-block:: bash

   uv run soju --help
   uv run soju <subcommand> --help

**Validate after any data change:** ``uv run poe validate`` or
``docker compose --profile validate run --rm validate``

- :doc:`soju` (unified entry — all subcommands)
- :doc:`import`
- :doc:`promote`
- :doc:`validate-schemas`
- :doc:`align`
- :doc:`registry`
- :doc:`translate-words`
- :doc:`fill-examples`
- :doc:`fill-verbs`
- :doc:`embed-index`
- :doc:`backend`

See :doc:`/development/poe` for shortcut tasks and :doc:`/development/docker` for
Compose services that wrap these tools.
