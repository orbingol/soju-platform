# SPDX-License-Identifier: BSD-3-Clause
"""Pluggable target-language seam for script, conjugation, and prompts."""

from soju.languages.contracts import LanguagePlugin
from soju.languages.plugins import active_language, get_language, register

__all__ = ["LanguagePlugin", "active_language", "get_language", "register"]
