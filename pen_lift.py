#!/usr/bin/env python3
"""
Pen Lift Module
===============
Post-processing that breaks a continuous path into segments with gaps.
The pen lifts off the paper at specified intervals, creating discontinuous
patterns (radial lines, dotted loops, segmented arcs).

This is NOT a pipeline TransformModule — it operates on the final point
array after generation and resampling.

Modes:
    periodic:  Draw N points, skip M points, repeat
    threshold: Lift when consecutive point distance exceeds a threshold
    angular:   Lift based on angular position relative to center
"""

import numpy as np
from math import atan2, pi
from typing import List
import configparser


def apply_pen_lift(points: np.ndarray,
                   config: configparser.ConfigParser) -> List[np.ndarray]:
    """
    Split a point array into sub-paths based on pen lift rules.

    Args:
        points: Complex array of points (single continuous path)
        config: Parsed INI config with [pen_lift] section

    Returns:
        List of point sub-arrays, each a continuous drawn segment
    """
    mode = config.get('pen_lift', 'mode', fallback='periodic')

    if mode == 'periodic':
        return _periodic_lift(points, config)
    elif mode == 'threshold':
        return _threshold_lift(points, config)
    elif mode == 'angular':
        return _angular_lift(points, config)
    else:
        raise ValueError(f"Unknown pen_lift mode: {mode}")


def _periodic_lift(points: np.ndarray,
                   config: configparser.ConfigParser) -> List[np.ndarray]:
    """Draw N points, skip M points, repeat."""
    draw_length = config.getint('pen_lift', 'draw_length', fallback=100)
    skip_length = config.getint('pen_lift', 'skip_length', fallback=50)
    cycle = draw_length + skip_length

    segments = []
    current = []

    for i, pt in enumerate(points):
        pos_in_cycle = i % cycle
        if pos_in_cycle < draw_length:
            current.append(pt)
        else:
            if current:
                segments.append(np.array(current))
                current = []

    if current:
        segments.append(np.array(current))

    return segments


def _threshold_lift(points: np.ndarray,
                    config: configparser.ConfigParser) -> List[np.ndarray]:
    """Lift when distance between consecutive points exceeds threshold."""
    threshold = config.getfloat('pen_lift', 'threshold', fallback=20.0)

    segments = []
    current = [points[0]]

    for i in range(1, len(points)):
        dist = abs(points[i] - points[i - 1])
        if dist > threshold:
            if current:
                segments.append(np.array(current))
            current = [points[i]]
        else:
            current.append(points[i])

    if current:
        segments.append(np.array(current))

    return segments


def _angular_lift(points: np.ndarray,
                  config: configparser.ConfigParser) -> List[np.ndarray]:
    """Lift based on angular position relative to center."""
    angle_draw = config.getfloat('pen_lift', 'angle_draw', fallback=30.0)
    angle_skip = config.getfloat('pen_lift', 'angle_skip', fallback=10.0)
    center_x = config.getfloat('pen_lift', 'center_x', fallback=0.0)
    center_y = config.getfloat('pen_lift', 'center_y', fallback=0.0)
    center = center_x + 1j * center_y
    cycle = angle_draw + angle_skip

    segments = []
    current = []

    for pt in points:
        rel = pt - center
        angle = atan2(rel.imag, rel.real) * 180 / pi
        # Map to [0, 360)
        angle = angle % 360
        pos_in_cycle = angle % cycle
        if pos_in_cycle < angle_draw:
            current.append(pt)
        else:
            if current:
                segments.append(np.array(current))
                current = []

    if current:
        segments.append(np.array(current))

    return segments
