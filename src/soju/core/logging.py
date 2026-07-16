# SPDX-License-Identifier: BSD-3-Clause
"""Configurable logging for Soju tooling (environment variables / optional ``.env``).

Environment variables (set in the shell, Docker Compose, or a ``.env`` file when
``python-dotenv`` is installed — it is a *dev* dependency):

* ``SOJU_LOG_ENABLED`` — ``true``/``1``/``yes``/``on`` to enable; default off.
* ``SOJU_LOG_DESTINATION`` — ``file``, ``stderr``, or ``stdout`` (default ``file`` when enabled).
* ``SOJU_LOG_DIR`` — directory for log files when destination is ``file``.
  If unset, the log file is created in the current working directory as
  ``soju-log-<timestamp>.log``.
* ``SOJU_LOG_LEVEL`` — ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, or ``CRITICAL``
  (default ``DEBUG`` when enabled).
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ENV_ENABLED = "SOJU_LOG_ENABLED"
ENV_DESTINATION = "SOJU_LOG_DESTINATION"
ENV_DIR = "SOJU_LOG_DIR"
ENV_LEVEL = "SOJU_LOG_LEVEL"

_LOGGER_NAME = "soju"
_CONFIGURED = False
_LOG_PATH: Path | None = None

_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _truthy(value: str | None) -> bool:
    """Return True when ``value`` looks like a truthy env flag."""
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv() -> None:
    """Load ``.env`` from cwd then repo root when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - optional (dev dependency)
        return
    # Cwd first (typical CLI invocation), then repo root next to pyproject.toml.
    load_dotenv(Path.cwd() / ".env", override=False)
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env", override=False)


def _parse_level(raw: str | None) -> int:
    """Map an env level name to a :mod:`logging` level (default DEBUG)."""
    name = (raw or "DEBUG").strip().upper()
    level = logging.getLevelNamesMapping().get(name)
    if level is None:
        return logging.DEBUG
    return level


def resolve_log_path(*, log_dir: str | None = None, when: datetime | None = None) -> Path:
    """Return the log file path for destination ``file``.

    If ``log_dir`` (or ``SOJU_LOG_DIR``) is set, the file is placed in that
    directory; otherwise it is created in the current working directory.
    """
    stamp = (when or datetime.now()).strftime("%Y%m%d-%H%M%S")
    filename = f"soju-log-{stamp}.log"
    directory = (log_dir if log_dir is not None else os.environ.get(ENV_DIR) or "").strip()
    if directory:
        return Path(directory).expanduser().resolve() / filename
    return Path.cwd() / filename


def configure_logging(*, force: bool = False) -> logging.Logger:
    """Configure the ``soju`` logger from the environment. Idempotent unless ``force``."""
    global _CONFIGURED, _LOG_PATH
    if _CONFIGURED and not force:
        return logging.getLogger(_LOGGER_NAME)

    _load_dotenv()

    logger = logging.getLogger(_LOGGER_NAME)
    logger.handlers.clear()
    logger.propagate = False
    _LOG_PATH = None

    if not _truthy(os.environ.get(ENV_ENABLED)):
        logger.setLevel(logging.WARNING)
        logger.addHandler(logging.NullHandler())
        _CONFIGURED = True
        return logger

    level = _parse_level(os.environ.get(ENV_LEVEL))
    logger.setLevel(level)

    destination = (os.environ.get(ENV_DESTINATION) or "file").strip().lower()
    handler: logging.Handler
    if destination == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    elif destination == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    elif destination == "file":
        path = resolve_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
        _LOG_PATH = path
    else:
        handler = logging.StreamHandler(sys.stderr)
        logger.warning("Unknown %s=%r; falling back to stderr", ENV_DESTINATION, destination)

    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    handler.setLevel(level)
    logger.addHandler(handler)
    _CONFIGURED = True

    if _LOG_PATH is not None:
        logger.debug("Logging to %s", _LOG_PATH)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under ``soju``, configuring logging on first use."""
    configure_logging()
    if name is None or name == _LOGGER_NAME:
        return logging.getLogger(_LOGGER_NAME)
    if name.startswith(f"{_LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")


def log_path() -> Path | None:
    """Path of the active file handler, if any."""
    configure_logging()
    return _LOG_PATH


def reset_logging() -> None:
    """Clear configuration state (for tests)."""
    global _CONFIGURED, _LOG_PATH
    logger = logging.getLogger(_LOGGER_NAME)
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    _CONFIGURED = False
    _LOG_PATH = None
