#!/usr/bin/env python3
"""
Geneva Module
=============
Simulates a Geneva (Maltese cross) mechanism — converts continuous rotation
into intermittent stepped rotation with dwells.

Can work as:
- GENERATOR: traces the position of a point on the driven wheel.
  In a group with another generator, positions it at each dwell point.
- TRANSFORM: remaps the input position through the Geneva motion profile.
  Points cluster at dwell positions with quick transitions between them.

A Geneva mechanism with n slots:
- The driven wheel advances 360°/n per engagement
- During each driving wheel revolution, it engages once per slot
- The motion profile during advancement has smooth acceleration/deceleration
- Between engagements, the driven wheel is locked (dwell)

Parameters:
    slots: Number of positions/slots (3-8, default 4)
    radius: Size of the driven wheel (default 80)
    pin_radius: Distance of tracing point from driven center (default 0.7 * radius)
    cycles: Number of complete driving wheel revolutions
"""

import numpy as np
from fractions import Fraction
from math import pi, sin, cos, atan2, sqrt, floor
from main import TransformModule


class GenevaModule(TransformModule):
    """
    Geneva mechanism: intermittent rotation from continuous input.
    """

    def _load_config(self):
        self.slots = self._getint('slots', 4)
        self.radius = self._getfloat('radius', 80.0)
        self.pin_ratio = self._getfloat('pin_ratio', 0.7)  # tracing point as fraction of radius
        self.cycles = self._getfloat('cycles', 1.0)

        # Geneva geometry
        # Center distance: for proper Geneva, d = r / sin(π/n)
        # where r is the driven wheel radius
        n = self.slots
        self.half_slot_angle = pi / n  # half the angular width of one slot
        self.step_angle = 2 * pi / n   # angle the driven wheel advances per step
        # In a real Geneva, the driving pin engages for an arc of 2*asin(1/d_ratio)
        # d_ratio = 1/sin(π/n) is center distance / driven radius
        self.d_ratio = 1.0 / sin(pi / n)
        # Engagement half-angle on the driving wheel
        self.engage_half = pi / n  # simplified: pin engages for 2π/n of driving rotation

    def _geneva_angle(self, drive_angle):
        """Compute driven wheel angle from driving wheel angle.

        Returns the driven wheel's cumulative angle.
        """
        n = self.slots
        step = self.step_angle

        # Which slot cycle are we in?
        cycle_angle = drive_angle % (2 * pi)
        slot_idx = int(floor(drive_angle / (2 * pi))) * n

        # Within one driving revolution, the pin engages n times
        # Each engagement is centered at 2πk/n for k=0..n-1
        # Engagement window: ±engage_half around each center

        # Simpler model: divide each revolution into n equal sectors
        sector = cycle_angle / (2 * pi) * n
        sector_idx = int(floor(sector))
        sector_frac = sector - sector_idx

        # Within each sector: first half is dwell, second half is advance
        # Use a smooth step function for the advance
        dwell_frac = 0.5  # half the sector time is dwell

        base_angle = (slot_idx + sector_idx) * step

        if sector_frac < dwell_frac:
            # Dwell phase: driven wheel stationary
            return base_angle
        else:
            # Advance phase: smooth acceleration/deceleration
            # Map [dwell_frac, 1.0] to [0, 1] then apply smoothstep
            t = (sector_frac - dwell_frac) / (1.0 - dwell_frac)
            # Smoothstep: 3t² - 2t³ (zero velocity at start and end)
            smooth = t * t * (3 - 2 * t)
            return base_angle + smooth * step

    def transform(self, z: complex, t: float) -> complex:
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t

        # Driving wheel angle
        drive_angle = t_norm * 2 * pi * self.slots * self.cycles

        # Get driven wheel angle
        driven_angle = self._geneva_angle(drive_angle)

        # Point on driven wheel
        r = self.radius * self.pin_ratio
        point = r * complex(cos(driven_angle), sin(driven_angle))

        return z + point

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    @property
    def is_generator(self) -> bool:
        return True

    def __repr__(self):
        return f"GenevaModule(slots={self.slots}, radius={self.radius})"
