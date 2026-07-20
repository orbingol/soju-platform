# SPDX-License-Identifier: BSD-3-Clause
"""Cosine similarity for embedding vectors."""

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Return the cosine similarity of two equal-length vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        A value in ``[-1, 1]``; ``0.0`` when either vector has zero magnitude.

    Raises:
        ValueError: If ``a`` and ``b`` have different lengths.
    """
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} != {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
