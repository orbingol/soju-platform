Adding verbs
============

This walkthrough shows how a non-technical user can add a new **verb** with the ``soju``
command-line tool. Verbs need more than a meaning: you also supply common conjugations
(present, past, and future). You do **not** edit the vocabulary or verb files by hand —
``soju import`` does that for you.

How this differs from adding words
----------------------------------

- Use ``soju import verbs`` (not ``soju import words``).
- There is **no** ``--topic`` flag — verbs live in the shared verb list, not under a topic.
- Every verb record needs a ``forms`` block (conjugations). Words do not.
- You must use ``--stdin-json`` (a plain-text ``--file`` list is not supported for new verbs).
- Re-importing the **same** hangul + English meaning is **not** allowed (Soju returns an
  error). A different English gloss for the same hangul is fine (homonym).

Example goal
------------

Add the verb **웃다** (*to laugh*) with conjugations and one example sentence.

Before you start
----------------

1. Open a terminal in the project folder (same place as for :doc:`getting-started`).

   - **macOS / Linux:** Terminal
   - **Windows:** PowerShell or Command Prompt (open it *inside* the project folder)

2. Install `uv <https://docs.astral.sh/uv/>`_ if you do not have it yet.
3. One-time setup (downloads the Soju tools) — same on every OS:

   .. code-block:: bash

      uv sync

Step 1 — Write a small verb file
--------------------------------

Create a file named ``my-verb.json`` in the project folder (any text editor is fine).
Paste this content:

.. code-block:: json

   [
     {
       "hangul": "웃다",
       "romanization": "ut-da",
       "english": "to laugh",
       "forms": {
         "present": {
           "casual_polite": "웃어요",
           "formal_polite": "웃습니다"
         },
         "past": {
           "casual_polite": "웃었어요",
           "formal_polite": "웃었습니다"
         },
         "future": {
           "casual_polite": "웃을 거예요",
           "formal_polite": "웃겠습니다"
         }
       },
       "examples": {
         "present": {
           "casual_polite": [
             {
               "hangul": "친구와 웃어요.",
               "english": "I laugh with a friend."
             }
           ]
         }
       }
     }
   ]

What each field means:

- **hangul** — dictionary form (ends in 다), e.g. ``웃다``
- **romanization** — how it sounds in Latin letters
- **english** — meaning, usually starting with ``to …``
- **forms** — required conjugations for **present**, **past**, and **future**, each with:

  - **casual_polite** — 해요-style (e.g. ``웃어요``)
  - **formal_polite** — 합니다-style (e.g. ``웃습니다``)

- **examples** — optional; nest by tense → politeness → list of ``{hangul, english}``

You can list several verbs in the same ``[ ... ]`` array. Swap in your own verb and
forms when you are ready.

Step 2 — Preview (safe dry run)
-------------------------------

This checks the file **without** changing any data.

**macOS / Linux:**

.. code-block:: bash

   cat my-verb.json | uv run soju import verbs --stdin-json --dry-run

**Windows (PowerShell):**

.. code-block:: powershell

   Get-Content .\my-verb.json -Raw | uv run soju import verbs --stdin-json --dry-run

**Windows (Command Prompt):**

.. code-block:: bat

   type my-verb.json | uv run soju import verbs --stdin-json --dry-run

If something is wrong, the command prints an error. Fix ``my-verb.json`` and try again.

Step 3 — Import for real
------------------------

When the preview looks good, run the same command **without** ``--dry-run``.

**macOS / Linux:**

.. code-block:: bash

   cat my-verb.json | uv run soju import verbs --stdin-json

**Windows (PowerShell):**

.. code-block:: powershell

   Get-Content .\my-verb.json -Raw | uv run soju import verbs --stdin-json

**Windows (Command Prompt):**

.. code-block:: bat

   type my-verb.json | uv run soju import verbs --stdin-json

That writes the verb into Soju’s vocabulary and conjugation tables.

Step 4 — Validate
-----------------

Always check that the data is still consistent (same command on every OS):

.. code-block:: bash

   uv run poe validate

You want this to finish without errors before you rely on the new verb in the site.

Step 5 — See it in the browser
------------------------------

Start the site (if it is not already running) — same on every OS:

.. code-block:: bash

   docker compose up

Open http://localhost:8080, go to **Verbs**, and look for **웃다** / to laugh.

Tips
----

- Prefer ``soju import verbs`` over editing YAML under ``data/content/`` yourself.
- English meanings are unique **together with** the hangul.
- To assign a course level on import, add ``--level 1A`` (or another id from
  ``data/content/levels.yaml``). If you omit it, the verb stays unassigned until you
  tag it later with ``soju levels``.
- For full flags and advanced options, see :doc:`/cli/import`.
- To add ordinary words (nouns, adjectives, and so on), see :doc:`adding-vocabulary`.
