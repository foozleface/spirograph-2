#!/usr/bin/env python3
"""
Geneva Module
=============
Simulates a Geneva (Maltese cross) mechanism — converts continuous rotation
into intermittent stepped rotation with dwells.

The driven wheel dwells at N equally-spaced positions, then snaps to the
next position along an arc that dips inward (like the real pin-in-slot
engagement path). This creates a flower/gear-like path with lobes at the
dwell points and cusps during transitions.

Parameters:
    slots: Number of positions/slots (3-8, default 4)
    radius: Size of the driven wheel (default 80)
    pin_ratio: Tracing point distance as fraction of radius (default 0.7)
    dwell: Fraction of time spent at each stop (0-0.9, default 0.5)
    depth: How far inward the transition arc dips (0-1, default 0.4)
    cycles: Number of complete revolutions of the driving wheel
"""

import numpy as np
from fractions import Fraction
from math import pi, sin, cos, floor
from main import TransformModule


class GenevaModule(TransformModule):
    """
    Geneva mechanism: intermittent rotation with characteristic transition arcs.
    """

    def _load_config(self):
        self.slots = self._getint('slots', 4)
        self.radius = self._getfloat('radius', 80.0)
        self.pin_ratio = self._getfloat('pin_ratio', 0.7)
        self.dwell = self._getfloat('dwell', 0.5)
        self.depth = self._getfloat('depth', 0.4)
        self.cycles = self._getfloat('cycles', 1.0)

    def transform(self, z: complex, t: float) -> complex:
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t

        n = self.slots
        step_angle = 2 * pi / n
        r = self.radius * self.pin_ratio

        # Total angular progress through the Geneva mechanism
        total_progress = t_norm * n * self.cycles
        sector_idx = int(floor(total_progress))
        sector_frac = total_progress - sector_idx

        # Angle of current dwell position
        dwell_angle = sector_idx * step_angle

        dwell_frac = max(0.05, min(0.95, self.dwell))

        if sector_frac < dwell_frac:
            # DWELL: point stays at the current slot position
            # Small circular motion during dwell (like the locking disc arc)
            dwell_t = sector_frac / dwell_frac
            # Gentle oscillation during dwell — traces a small loop at the dwell point
            micro_angle = dwell_t * 2 * pi
            micro_r = r * 0.02  # tiny wobble during dwell
            x = r * cos(dwell_angle) + micro_r * cos(micro_angle)
            y = r * sin(dwell_angle) + micro_r * sin(micro_angle)
        else:
            # ADVANCE: snap to next position along an arc that dips inward
            advance_t = (sector_frac - dwell_frac) / (1.0 - dwell_frac)
            # Smoothstep for acceleration/deceleration
            smooth = advance_t * advance_t * (3 - 2 * advance_t)

            # Angle interpolation from current to next dwell
            next_angle = dwell_angle + step_angle
            angle = dwell_angle + smooth * step_angle

            # Radial dip: the pin traces an arc that goes inward during transition
            # Peak dip at the midpoint of the advance
            dip = sin(advance_t * pi) * self.depth * r
            current_r = r - dip

            x = current_r * cos(angle)
            y = current_r * sin(angle)

        return z + complex(x, y)

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    @property
    def is_generator(self) -> bool:
        return True

    def __repr__(self):
        return f"GenevaModule(slots={self.slots}, radius={self.radius})"
