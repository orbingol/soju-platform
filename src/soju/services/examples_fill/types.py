# SPDX-License-Identifier: BSD-3-Clause
"""Shared types for examples-fill progress reporting."""

from __future__ import annotations

from collections.abc import Callable

ProgressFn = Callable[[str], None]


def noop_progress(_msg: str) -> None:
    """Default progress sink (no I/O)."""
    return None
