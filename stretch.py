#!/usr/bin/env python3
"""
Stretch Module
==============
Non-uniform scaling — stretch the pattern along X and Y axes independently.

This is a TRANSFORMER module. Unlike scale (which scales uniformly),
stretch lets you elongate or compress along each axis separately.

With drift (end_scale_x, end_scale_y), the stretch can change over time —
a circle becomes an ellipse that keeps elongating as it draws.

The stretch is applied as:
    x' = origin_x + (x - origin_x) * scale_x(t)
    y' = origin_y + (y - origin_y) * scale_y(t)
"""

from fractions import Fraction
from main import TransformModule


class StretchModule(TransformModule):
    """
    Non-uniform X/Y scaling around a center point.

    Configuration:
        scale_x: X scale factor at start (default 1.0)
        scale_y: Y scale factor at start (default 1.0)
        end_scale_x: X scale factor at end (default = scale_x, no drift)
        end_scale_y: Y scale factor at end (default = scale_y, no drift)
        origin_x, origin_y: Center of stretch (default 0,0)
        normalize: If true (default), normalize t to [0,1]
    """

    def _load_config(self):
        self.scale_x = self._getfloat('scale_x', 1.0)
        self.scale_y = self._getfloat('scale_y', 1.0)
        self.end_scale_x = self._getfloat('end_scale_x', self.scale_x)
        self.end_scale_y = self._getfloat('end_scale_y', self.scale_y)
        self.origin_x = self._getfloat('origin_x', 0.0)
        self.origin_y = self._getfloat('origin_y', 0.0)
        self.normalize = self._getboolean('normalize', True)
        self.origin = self.origin_x + 1j * self.origin_y

    def transform(self, z: complex, t: float) -> complex:
        t_use = self._normalize_t(t)
        sx = self._interpolate(self.scale_x, self.end_scale_x, t_use, 'scale_x')
        sy = self._interpolate(self.scale_y, self.end_scale_y, t_use, 'scale_y')
        rel = z - self.origin
        return self.origin + complex(rel.real * sx, rel.imag * sy)

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    @property
    def is_generator(self) -> bool:
        return False

    def __repr__(self):
        return f"StretchModule(x:{self.scale_x}->{self.end_scale_x}, y:{self.scale_y}->{self.end_scale_y})"
