``soju translate-words``
========================

**Purpose:** Turn a plain-text word list into ``soju import`` JSON via Ollama (romanization,
English gloss, optional examples). Pipe stdout into ``soju import``, or write with ``--output``.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - Plain-text ``--file``; registry (for ``--skip-existing``)
   * - **Writes**
     - Nothing (stdout or ``--output`` JSON only)
   * - **Exit codes**
     - ``0`` success · non-zero on error

.. typer:: soju.cli.translate.app
   :prog: soju translate-words
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju translate-words --file words.txt | uv run soju import words --topic common --stdin-json
   uv run poe translate-words --file words.txt
   uv run soju translate-words --file words.txt --dry-run
   uv run soju translate-words --file words.txt --skip-existing -o records.json

Requires a reachable Ollama (or compatible) server unless ``--dry-run``. Level defaults to ``SOJU_LANGUAGE_LEVEL`` or ``1A``.
