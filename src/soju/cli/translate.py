# SPDX-License-Identifier: BSD-3-Clause
"""``soju translate-words`` command."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from soju.cli._common import flag, make_app
from soju.levels import get_language_level
from soju.llm import LlmError, OllamaClient
from soju.llm.ollama import DEFAULT_BASE_URL, DEFAULT_MODEL
from soju.services.translate import parse_word_list_lines, translate_words

app = make_app()


@app.command()
def translate(
    file: Annotated[Path, typer.Option("--file", "-f", help="Plain-text word list file")],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Write JSON to this file instead of stdout"),
    ] = None,
    model: Annotated[str, typer.Option("--model", help="Ollama model name")] = DEFAULT_MODEL,
    base_url: Annotated[str, typer.Option("--base-url", help="Ollama base URL")] = DEFAULT_BASE_URL,
    batch_size: Annotated[int, typer.Option("--batch-size", help="Lines per Ollama request")] = 8,
    temperature: Annotated[float, typer.Option("--temperature", help="Sampling temperature")] = 0.3,
    skip_existing: Annotated[
        bool,
        flag("--skip-existing", help="Omit entries already in the registry"),
    ] = False,
    level: Annotated[
        Optional[str],
        typer.Option(
            "--level",
            help="Course level (default: SOJU_LANGUAGE_LEVEL or 1A; see data/content/levels.yaml)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        flag("--dry-run", help="Parse input and print summary without calling Ollama"),
    ] = False,
) -> None:
    """Translate a plain-text word list into soju import JSON via Ollama."""
    if not file.is_file():
        print(f"Error: file not found: {file}", file=sys.stderr)
        raise typer.Exit(2)

    lines = file.read_text(encoding="utf-8").splitlines()
    hints = parse_word_list_lines(lines)

    if dry_run:
        course_level = get_language_level(level)
        print(f"Language level: {course_level.label} ({course_level.id})", file=sys.stderr)
        print(f"Parsed {len(hints)} translatable lines from {file}.", file=sys.stderr)
        for hint in hints:
            parts = [hint.entry]
            if hint.hint_english:
                parts.append(f"en={hint.hint_english}")
            if hint.hint_example:
                parts.append(f"ex={hint.hint_example}")
            print("  " + " | ".join(parts), file=sys.stderr)
        return

    llm = OllamaClient(model=model, base_url=base_url)
    if not llm.check_available():
        print(
            f"Error: Ollama is not reachable at {base_url}. Start Ollama or run: docker compose --profile ollama up ollama ollama-pull",
            file=sys.stderr,
        )
        raise typer.Exit(1)

    try:
        records, warnings = translate_words(
            lines,
            llm=llm,
            batch_size=max(1, batch_size),
            temperature=temperature,
            skip_existing=skip_existing,
            level_id=level,
        )
    except (LlmError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    payload = {"records": records}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)

    if output is not None:
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {len(records)} records to {output}.", file=sys.stderr)
    else:
        print(rendered)
