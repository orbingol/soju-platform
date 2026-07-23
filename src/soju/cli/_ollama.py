# SPDX-License-Identifier: BSD-3-Clause
"""Shared Ollama CLI bootstrap helpers."""

from __future__ import annotations

import sys

import typer

from soju.llm import OllamaClient


def require_ollama_client(*, model: str, base_url: str) -> OllamaClient:
    """Build an :class:`OllamaClient` or exit if Ollama is unreachable."""
    client = OllamaClient(model=model, base_url=base_url)
    if not client.check_available():
        print(
            f"Error: Ollama is not reachable at {base_url}. "
            "Start Ollama or run: docker compose --profile ollama up ollama ollama-pull",
            file=sys.stderr,
        )
        raise typer.Exit(1)
    return client
