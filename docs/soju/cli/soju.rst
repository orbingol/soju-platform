``soju`` (unified entry)
========================

Single console entry for all Soju CLI tools. Install with ``uv sync``, then run
``uv run soju <subcommand> …``.

Global options (before the subcommand): ``--language`` / ``-L``, ``--verbose``.

.. typer:: soju.cli.app.app
   :prog: soju
   :show-nested:
   :make-sections:
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju --help
   uv run soju import words --topic common --stdin-json --dry-run < records.json
   uv run soju promote --topic family --dry-run
   uv run soju validate-schemas
   uv run soju embed-index --dry-run

See the individual pages under :doc:`index` for purpose notes and longer examples.
