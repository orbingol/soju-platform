# SPDX-License-Identifier: BSD-3-Clause
"""Korean target-language plugin.

Keep this package init lightweight: ``soju.core.text`` imports
:mod:`soju.languages.korean.text` and must not pull conjugation / examples /
registry via a heavy ``__init__``.
"""
