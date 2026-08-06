# SPDX-License-Identifier: BSD-3-Clause
"""``soju backend`` — run the FastAPI Soju API server."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Optional

import typer

from soju.cli._common import make_app

if TYPE_CHECKING:
    from soju.backend.config.settings import BackendSettings

app = make_app()

# Keep help text free of runtime server imports so ``sphinxcontrib-typer`` and
# ``soju --help`` stay light (uvicorn / FastAPI load only when starting the server).
_USER_CONFIG_HELP = (
    "YAML override path (default: ~/.config/soju/backend.yaml if present, else packaged defaults)"
)


def _apply_server_overrides(
    settings: BackendSettings,
    *,
    host: str | None,
    port: int | None,
) -> BackendSettings:
    server = settings.server
    updates: dict[str, object] = {}
    if host is not None:
        updates["host"] = host
    if port is not None:
        updates["port"] = port
    if not updates:
        return settings
    return settings.model_copy(update={"server": server.model_copy(update=updates)})


def backend(
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help=_USER_CONFIG_HELP,
            exists=False,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    host: Annotated[
        Optional[str],
        typer.Option("--host", help="Bind host (overrides YAML server.host)"),
    ] = None,
    port: Annotated[
        Optional[int],
        typer.Option("--port", help="Bind port (overrides YAML server.port)", min=1, max=65535),
    ] = None,
) -> None:
    """Run the Soju FastAPI backend (LLM + TTS OpenAI-compatible API)."""
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        typer.echo(
            "Error: backend dependencies are not installed. Run: uv sync",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    try:
        from soju.backend.app import create_app
        from soju.backend.config.loader import load_settings
    except ModuleNotFoundError as exc:
        typer.echo(
            "Error: backend dependencies are not installed. Run: uv sync",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    try:
        settings = load_settings(config)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001 - surface config/validation errors to the CLI
        typer.echo(f"Error loading backend config: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    settings = _apply_server_overrides(settings, host=host, port=port)
    fastapi_app = create_app(settings)
    uvicorn.run(fastapi_app, host=settings.server.host, port=settings.server.port)


app.command()(backend)
