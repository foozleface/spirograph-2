#!/usr/bin/env python3
"""
Tile
====
A finishing pass: the finished drawing repeated in a grid, rows by columns,
each copy shifted by (dx, dy). Every other row may be staggered by half a
column, which is how a brick pattern or a hexagonal packing is laid.

Not a pipeline module — it acts on finished point arrays, after symmetry
and before clipping, the same way symmetry does. The copies share one
bounding box downstream, so the grid keeps its spacing when the whole thing
is fitted to the paper.
"""

import numpy as np
from typing import List


def apply_tile(points: np.ndarray, rows: int = 1, cols: int = 1,
               dx: float = 0.0, dy: float = 0.0,
               stagger: bool = False) -> List[np.ndarray]:
    """
    Repeat a point array in a grid.

    Args:
        points: Complex array (one path)
        rows, cols: How many copies down and across (1 x 1 = unchanged)
        dx, dy: Step between copies, in the drawing's own units
        stagger: Shift odd rows by half a column

    Returns:
        List of point arrays, the original first, row-major after it
    """
    rows, cols = max(int(rows), 1), max(int(cols), 1)
    out = []
    for r in range(rows):
        shift = 0.5 * dx if (stagger and r % 2 == 1) else 0.0
        for c in range(cols):
            offset = complex(c * dx + shift, r * dy)
            out.append(points + offset)
    return out
