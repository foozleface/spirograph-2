#!/usr/bin/env python3
"""
Scale Module
============
Scales the entire pattern over time — growing or shrinking as it draws.

This is a TRANSFORMER module - it takes input coordinates and scales them
relative to a specified center point based on the time parameter.

Combined with rotation, this creates the classic "spiraling outward" effect.
Unlike per-generator end_radius parameters, this works universally with any
upstream module.

The scaling is applied as:
    z' = center + (z - center) * scale(t)

Where scale(t) interpolates linearly from start_scale to end_scale
as t goes from 0 to 1.
"""

import numpy as np
from fractions import Fraction
from main import TransformModule


class ScaleModule(TransformModule):
    """
    Time-varying scale: scales input coordinates around a center point.

    This is a TRANSFORMER module - it modifies input z based on time t.

    Configuration:
        start_scale: Scale factor at the start of drawing (default 1.0)
        end_scale: Scale factor at the end of drawing (default 1.0)
        origin_x, origin_y: Center of scaling (default 0,0)
        normalize: If true (default), normalize t to [0,1] regardless of pipeline period
    """

    def _load_config(self):
        """Load scale configuration."""
        self.start_scale = self._getfloat('start_scale', 1.0)
        self.end_scale = self._getfloat('end_scale', 1.0)
        self.origin_x = self._getfloat('origin_x', 0.0)
        self.origin_y = self._getfloat('origin_y', 0.0)
        self.normalize = self._getboolean('normalize', True)

        # Scale center as complex number
        self.origin = self.origin_x + 1j * self.origin_y

    def transform(self, z: complex, t: float) -> complex:
        """
        Scale input coordinates around the origin point.

        Args:
            z: Input position to transform
            t: Time parameter in [0, 1] or [0, period]

        Returns:
            Scaled position
        """
        t_use = self._normalize_t(t)

        # Current scale factor (linear interpolation)
        scale = self.start_scale + (self.end_scale - self.start_scale) * t_use

        # Scale around origin: z' = origin + (z - origin) * scale
        relative = z - self.origin
        scaled = relative * scale
        result = self.origin + scaled

        return result

    @property
    def natural_period(self) -> Fraction:
        """Scale doesn't affect pattern closure."""
        return Fraction(1, 1)

    @property
    def is_generator(self) -> bool:
        """This module transforms coordinates, not generates."""
        return False

    def __repr__(self):
        if self.origin_x == 0 and self.origin_y == 0:
            return f"ScaleModule({self.start_scale} -> {self.end_scale})"
        return f"ScaleModule({self.start_scale} -> {self.end_scale} around ({self.origin_x}, {self.origin_y}))"
