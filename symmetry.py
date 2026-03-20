#!/usr/bin/env python3
"""
Symmetry Module
===============
Applies n-fold rotational symmetry and optional mirror reflections to a
finished point array. This is a post-processing step, not a pipeline module.

Given a single path, produces N rotated copies (and optionally their mirrors)
so the final drawing has rotational symmetry.
"""

import numpy as np
from math import pi
from typing import List


def apply_symmetry(points: np.ndarray, n_fold: int = 1,
                   mirror: bool = False,
                   center_x: float = 0.0,
                   center_y: float = 0.0) -> List[np.ndarray]:
    """
    Apply n-fold rotational symmetry to a point array.

    Args:
        points: Complex array of points (the base pattern)
        n_fold: Number of rotational copies (1 = no symmetry)
        mirror: If True, also add mirror reflections (doubles the count)
        center_x, center_y: Center of symmetry (in raw coordinates,
                            before normalization)

    Returns:
        List of point arrays: [original, rotated_1, ..., rotated_n-1]
        plus mirrors if requested. First element is always the original.
    """
    if n_fold < 1:
        n_fold = 1

    center = center_x + 1j * center_y
    result = []

    for i in range(n_fold):
        angle = 2 * pi * i / n_fold
        rotation = np.exp(1j * angle)
        rotated = center + (points - center) * rotation
        result.append(rotated)

        if mirror:
            # Mirror across the axis at this rotation angle
            # Reflect relative to center, then conjugate, then rotate
            relative = points - center
            mirrored = relative.conj() * np.exp(2j * angle)
            result.append(center + mirrored)

    return result
