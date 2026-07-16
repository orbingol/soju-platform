# SPDX-License-Identifier: BSD-3-Clause
"""Korean hangul normalization helpers."""

from __future__ import annotations

from soju.languages.korean.text import has_hangul, normalize_hangul


def test_normalize_hangul_nfc_and_whitespace() -> None:
    assert normalize_hangul("  학교  ") == "학교"


def test_has_hangul() -> None:
    assert has_hangul("학교")
    assert not has_hangul("school")
