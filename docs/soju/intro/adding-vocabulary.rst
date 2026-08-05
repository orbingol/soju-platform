Adding vocabulary
=================

This walkthrough shows how a non-technical user can add a new word with the ``soju``
command-line tool. You do **not** edit the big vocabulary files by hand — ``soju import``
does that for you.

Example goal
------------

Add the word **딸기** (*strawberry*) to the **common** topic, with one example sentence.

Before you start
----------------

1. Open a terminal in the project folder (same place as for :doc:`getting-started`).

   - **macOS / Linux:** Terminal
   - **Windows:** PowerShell or Command Prompt (open it *inside* the project folder)

2. Install `uv <https://docs.astral.sh/uv/>`_ if you do not have it yet.
3. One-time setup (downloads the Soju tools) — same on every OS:

   .. code-block:: bash

      uv sync

Step 1 — Write a small word list file
-------------------------------------

Create a file named ``my-word.json`` in the project folder (any text editor is fine).
Paste this content:

.. code-block:: json

   [
     {
       "hangul": "딸기",
       "romanization": "ttal-gi",
       "english": "strawberry",
       "examples": [
         {
           "hangul": "딸기를 먹어요.",
           "english": "I eat a strawberry."
         }
       ]
     }
   ]

What each field means:

- **hangul** — the Korean spelling
- **romanization** — how it sounds in Latin letters (optional; Soju can fill this in)
- **english** — the meaning in English (usually lowercase, e.g. ``strawberry``)
- **examples** — optional sample sentences (Korean + English)

You can list several words in the same ``[ ... ]`` array. Swap in your own hangul,
romanization, English, and examples when you are ready.

Step 2 — Preview (safe dry run)
-------------------------------

This checks the file **without** changing any data.

**macOS / Linux:**

.. code-block:: bash

   cat my-word.json | uv run soju import words --topic common --stdin-json --dry-run

**Windows (PowerShell):**

.. code-block:: powershell

   Get-Content .\my-word.json -Raw | uv run soju import words --topic common --stdin-json --dry-run

**Windows (Command Prompt):**

.. code-block:: bat

   type my-word.json | uv run soju import words --topic common --stdin-json --dry-run

If something is wrong, the command prints an error. Fix ``my-word.json`` and try again.
If the word already exists with the same English meaning, Soju will merge rather than
create a duplicate.

Step 3 — Import for real
------------------------

When the preview looks good, run the same command **without** ``--dry-run``.

**macOS / Linux:**

.. code-block:: bash

   cat my-word.json | uv run soju import words --topic common --stdin-json

**Windows (PowerShell):**

.. code-block:: powershell

   Get-Content .\my-word.json -Raw | uv run soju import words --topic common --stdin-json

**Windows (Command Prompt):**

.. code-block:: bat

   type my-word.json | uv run soju import words --topic common --stdin-json

That writes the word into Soju’s vocabulary and attaches it to the **common** topic.

Other topic ids you can use instead of ``common`` include ``family``, ``time``,
``numbers``, and ``place`` (see ``data/content/topics/manifest.yaml``).

Step 4 — Validate
-----------------

Always check that the data is still consistent (same command on every OS):

.. code-block:: bash

   uv run poe validate

You want this to finish without errors before you rely on the new word in the site.

Step 5 — See it in the browser
------------------------------

Start the site (if it is not already running) — same on every OS:

.. code-block:: bash

   docker compose up

Open http://localhost:8080, go to **Topics → Common** (or Word types), and look for
**딸기** / strawberry.

Tips
----

- Prefer ``soju import`` over editing YAML under ``data/content/`` yourself.
- English meanings are unique **together with** the hangul. The same hangul with a
  different meaning (a homonym) is allowed as a separate entry.
- To assign a course level on import, add ``--level 1A`` (or another id from
  ``data/content/levels.yaml``). If you omit it, the word stays unassigned until you
  tag it later with ``soju levels``.
- For full flags and advanced options, see :doc:`/cli/import`.
- To add verbs (dictionary form + conjugations), see :doc:`adding-verbs`.
