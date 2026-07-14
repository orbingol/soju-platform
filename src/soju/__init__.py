# SPDX-License-Identifier: BSD-3-Clause
"""Soju (소주) platform development tools."""

try:
    from soju._version import version as __version__
except ImportError:  # pragma: no cover - missing until editable/build install
    __version__ = "0.0.0"
