#!/usr/bin/env python3
"""
Clip
====
A finishing pass: keep only what falls inside a circle or a rectangle. The
pen lifts wherever the line leaves the shape and lands again where it comes
back, so a clipped path becomes several strokes — a drawing cut to a
window, or to a plate, or to whatever the sheet can take.

Not a pipeline module — it acts on finished point arrays, last of all, so
the window is cut into the whole composition including its copies.
"""

import numpy as np
from typing import List


def apply_clip(points: np.ndarray, shape: str = 'circle',
               radius: float = 100.0, width: float = 200.0, height: float = 200.0,
               center_x: float = 0.0, center_y: float = 0.0,
               invert: bool = False) -> List[np.ndarray]:
    """
    Cut a path to a shape.

    Args:
        points: Complex array (one path)
        shape: 'circle' (radius) or 'rect' (width x height), about the centre
        invert: Keep what is outside instead

    Returns:
        List of point arrays, one per continuous run inside the shape
    """
    rel = points - complex(center_x, center_y)
    if shape == 'rect':
        inside = (np.abs(rel.real) <= width / 2) & (np.abs(rel.imag) <= height / 2)
    elif shape == 'circle':
        inside = np.abs(rel) <= radius
    else:
        raise ValueError("clip: unknown shape %r" % shape)
    if invert:
        inside = ~inside
    if not inside.any():
        return []
    # Runs of consecutive inside points.
    edges = np.flatnonzero(np.diff(inside.astype(np.int8)))
    starts = np.concatenate(([0], edges + 1))
    ends = np.concatenate((edges + 1, [len(points)]))
    return [points[s:e] for s, e in zip(starts, ends) if inside[s] and e - s >= 2]
