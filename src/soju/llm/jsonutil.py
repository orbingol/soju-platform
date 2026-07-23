# SPDX-License-Identifier: BSD-3-Clause
"""Parse LLM JSON payloads (optional markdown fences)."""

from __future__ import annotations

import json
import re
from typing import Any

JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_content(content: str) -> Any:
    """Strip optional markdown fences and ``json.loads`` the remainder."""
    stripped = JSON_FENCE.sub("", content.strip())
    return json.loads(stripped)
