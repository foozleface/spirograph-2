#!/usr/bin/env python3
"""
Damping Module
==============
Universal exponential amplitude decay — pattern shrinks toward a center
point over time, like a harmonograph losing energy.

The existing harmonograph module has per-pendulum decay that resets each
cycle. This module applies a global decay envelope to ANY pipeline,
making it universally composable.

The damping is applied as:
    z' = origin + (z - origin) * exp(-decay_rate * t * duration)

At t=0 the pattern is full-size. As t increases, points collapse
toward the origin exponentially.
"""

import numpy as np
from fractions import Fraction
from main import TransformModule


class DampingModule(TransformModule):
    """
    Exponential decay: shrinks pattern toward origin over time.

    This is a TRANSFORMER module - it modifies input z based on time t.

    Configuration:
        decay_rate: Exponential decay constant (default 0.02)
        duration: Time scale — higher = slower decay (default 60.0)
        origin_x, origin_y: Point to decay toward (default 0,0)
        normalize: If true (default), normalize t to [0,1]
    """

    def _load_config(self):
        self.decay_rate = self._getfloat('decay_rate', 0.02)
        self.end_decay_rate = self._getfloat('end_decay_rate', self.decay_rate)
        self.duration = self._getfloat('duration', 60.0)
        self.origin_x = self._getfloat('origin_x', 0.0)
        self.origin_y = self._getfloat('origin_y', 0.0)
        self.normalize = self._getboolean('normalize', True)

        self.origin = self.origin_x + 1j * self.origin_y

    def transform(self, z: complex, t: float) -> complex:
        t_use = self._normalize_t(t)
        rate = self._interpolate(self.decay_rate, self.end_decay_rate, t_use, 'decay_rate')
        factor = np.exp(-rate * t_use * self.duration)
        return self.origin + (z - self.origin) * factor

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    @property
    def is_generator(self) -> bool:
        return False

    def __repr__(self):
        return f"DampingModule(rate={self.decay_rate}, dur={self.duration})"
