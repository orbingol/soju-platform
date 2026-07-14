# SPDX-License-Identifier: BSD-3-Clause
"""Shared vocabulary context strings for AI prompts."""

from __future__ import annotations

from soju.korean_levels import KoreanLevel, vocabulary_for_level


def build_vocabulary_context(
    root=None,
    *,
    compact: bool = False,
    level: KoreanLevel | str | None = None,
) -> str:
    from soju.korean_levels import get_korean_level

    if isinstance(level, str) or level is None:
        level_obj = get_korean_level(level, root)
    else:
        level_obj = level

    vocabulary = vocabulary_for_level(level_obj.id, root)
    header = f"{level_obj.label} vocabulary (use mainly these words in examples):"

    if compact:
        lines = [f"{entry['hangul']}: {entry['english']}" for entry in vocabulary]
        return f"{header}\n" + "\n".join(lines)

    words = [entry for entry in vocabulary if entry.get("type") != "verb"]
    verbs = [entry for entry in vocabulary if entry.get("type") == "verb"]

    word_lines = [f"- {entry['hangul']} ({entry['romanization']}): {entry['english']}" for entry in words]
    verb_lines = [f"- {entry['hangul']} ({entry['romanization']}): {entry['english']}" for entry in verbs]

    return f"{header}\n" + "\n".join(word_lines) + "\n\nVerbs:\n" + "\n".join(verb_lines)
