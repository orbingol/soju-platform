# SPDX-License-Identifier: BSD-3-Clause
"""Pluggable base-language (known-language) seam shared across target languages."""

from soju.base.contract import BaseLanguage
from soju.base.plugins import get_base_language, register

__all__ = ["BaseLanguage", "get_base_language", "register"]
