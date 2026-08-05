# SPDX-License-Identifier: BSD-3-Clause
"""Simple ``{{placeholder}}`` template rendering for prompt YAML."""

from __future__ import annotations


def render(template: str, **values: object) -> str:
    """Replace ``{{name}}`` placeholders; unknown placeholders are left unchanged."""
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out
