Getting started
===============

You only need `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_ installed
(macOS, Windows, or Linux).

1. Open a terminal in this project folder.

   - **macOS / Linux:** Terminal
   - **Windows:** PowerShell or Command Prompt

2. Start Soju (same command on every OS):

   .. code-block:: bash

      docker compose up

3. In your browser, open http://localhost:8080.

To stop, press ``Ctrl+C`` in the terminal (or quit Docker Desktop).

Browsing words, grammar, and flashcards works right away. Practice and Chat are optional
and need a local AI model:

1. Install `Ollama <https://ollama.com/download>`_.
2. Download the default models (same command on every OS):

   .. code-block:: bash

      ollama pull gemma4:e4b
      ollama pull nomic-embed-text

3. Start Soju again with ``docker compose up``. With Ollama running on your computer,
   Practice and Chat work in the browser at http://localhost:8080.

Next steps: :doc:`adding-vocabulary` · :doc:`adding-verbs`
