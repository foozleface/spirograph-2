#!/usr/bin/env python3
"""
Crank and rod
=============
The linkage most real drawing machines are built from: a crank turning on a
fixed axle, a rod from the crank's pin to a slider that runs on a straight
track, and the pen fixed somewhere along the rod -- or off to one side of it.

The crank pin goes round a circle; the slider only goes back and forth; a
point on the rod between them traces neither. It draws an egg, a teardrop,
a kidney, a figure of eight with one fat lobe, depending on how long the rod
is against the crank and where along it the pen sits. That pointed-at-one-
end, fat-at-the-other shape is what an ellipse cannot draw, and what a real
machine's petals look like.

Geometry, with the crank's axle at the centre and the track through the
axle at ``track_angle``:

    pin     P = r · e^(iθ)
    slider  S on the track with |S − P| = L
    pen     P + along · (S − P) + aside · i(S − P)/L

``along`` is 0 at the pin and 1 at the slider (past 1 overhangs the slider);
``aside`` is millimetres off the rod's line, to its left.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class CrankRodModule(TransformModule):
    """An arm: a crank, a rod sliding on a track, and the pen on the rod."""

    is_generator = True            # an arm: adds a vector to where the pen is

    def _load_config(self):
        self.crank = self._getfloat('crank_radius', 40.0)
        self.end_crank = self._getfloat('end_crank_radius', self.crank)
        self.rod = self._getfloat('rod_length', 55.0)
        self.end_rod = self._getfloat('end_rod_length', self.rod)
        self.along = self._getfloat('pen_along', 0.3)
        self.end_along = self._getfloat('end_pen_along', self.along)
        self.aside = self._getfloat('pen_aside', 30.0)
        self.end_aside = self._getfloat('end_pen_aside', self.aside)
        self.track_deg = self._getfloat('track_angle', 0.0)
        self.cycles = self._getfloat('cycles', 1.0)
        self.center = self._getfloat('center_x', 0.0) + 1j * self._getfloat('center_y', 0.0)

    def transform(self, z, t):
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        theta = 2 * pi * (t_norm * self.cycles % 1.0)

        r = self._interpolate(self.crank, self.end_crank, t_norm, 'crank_radius')
        rod = self._interpolate(self.rod, self.end_rod, t_norm, 'rod_length')
        along = self._interpolate(self.along, self.end_along, t_norm, 'pen_along')
        aside = self._interpolate(self.aside, self.end_aside, t_norm, 'pen_aside')
        # A rod shorter than the crank cannot reach the track at the top of
        # the stroke; real ones are always longer, so it is held there.
        rod = np.maximum(rod, np.abs(r) * 1.001)

        track = np.exp(1j * self.track_deg * pi / 180)
        pin = r * np.exp(1j * theta) / track            # in the track's frame
        a, b = pin.real, pin.imag
        slider = a + np.sqrt(np.maximum(rod * rod - b * b, 0.0))   # on the x axis
        rod_vec = slider - pin
        pen = pin + along * rod_vec + aside * 1j * rod_vec / rod
        return z + self.center + pen * track

    @property
    def natural_period(self) -> Fraction:
        return Fraction(self.cycles).limit_denominator(1000)

    def __repr__(self):
        return (f"CrankRodModule(r={self.crank}, L={self.rod}, "
                f"along={self.along}, aside={self.aside})")
