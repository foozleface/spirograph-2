#!/usr/bin/env python3
"""
Ring carrier
============

The nested-ring toy (reference/01): a fixed outer ring with teeth on its
inner surface; inside it a ring that rolls round, carrying a bore in which
the next thing rolls; and the bore need not be at the carrier's centre.

    ring 1   fixed, inner teeth            `fixed_teeth`
    ring 2   rolls inside ring 1           `rolling_teeth`, this module
    ring 3   nested in ring 2, sets how    `bore_offset`, `bore_angle`
             far off-centre the bore is
    ring 4   the rider in ring 3's bore    the arm before this step

Rings 2 and 3 are a pair of eccentric annuli that mesh tooth to tooth;
turning one in the other adds their offsets or cancels them. That setting
is held by the teeth while drawing, so here it is one number: how far the
bore's centre is from the carrier's, and in which direction in the
carrier's own frame.

This is a *carriage*: it carries everything drawn before it. Whatever
rides in the bore -- a gear, an ellipse, another carrier -- is turned with
the carrier's own spin, moved out to the bore, and carried round ring 1.
Nest as deep as you like: a carrier before a carrier is a ring in a ring
in a ring.

With the carrier's orbit angle θ(t) and its spin φ(t):

    pen = C(θ) + e^(iφ) · (bore + rider)

    C(θ)   = (R ∓ r) e^(iθ)         the carrier's centre, round ring 1
    φ(θ)   = ∓ ((R ∓ r) / r) θ      rolling without slipping (inside: −)
    bore   = bore_offset e^(i·bore_angle)
    rider  = what the earlier steps drew, in the carrier's frame

R and r from the teeth: radius = teeth × tooth_pitch / 2π, as the gear.

How fast the rider goes round its bore against how fast the carrier goes
round ring 1 is not fixed by any teeth -- on the toy it is set by how the
hand pushes -- so each is given its own `cycles`.
"""
import numpy as np
from fractions import Fraction
from math import pi, gcd

from main import TransformModule


class RingCarrierModule(TransformModule):
    """A ring rolling inside (or around) a fixed ring, carrying an
    off-centre bore in which the steps before it ride.

    Configuration:
        fixed_teeth:     teeth on the fixed ring (ring 1)
        rolling_teeth:   teeth on the carrier's outside (ring 2)
        tooth_pitch:     length per tooth; sets the size
        bore_offset:     how far the bore's centre sits from the carrier's
        end_bore_offset: the same at the end of the draw (a drift)
        bore_angle:      which way the bore is offset, degrees, in the
                         carrier's own frame
        inside:          roll inside ring 1 (hypo) or round its outside (epi)
        cycles:          trips round ring 1 over the draw (one trip = until
                         the carrier closes, `rotations` orbits)
        rotations:       orbits per trip; 0 = until the teeth line up again
    """

    is_generator = True            # a carriage: adds where the bore is

    @property
    def follow(self):
        """Always on: the carrier turns what it carries. (The base class
        reads a `follow` key for the curved paths; a ring has no choice.)"""
        return True

    @follow.setter
    def follow(self, _value):
        pass

    def _load_config(self):
        self.fixed_teeth = self._getint('fixed_teeth', 180)
        self.rolling_teeth = self._getint('rolling_teeth', 144)
        self.tooth_pitch = self._getfloat('tooth_pitch', 1.0)
        self.bore_offset = self._getfloat('bore_offset', 6.0)
        self.end_bore_offset = self._getfloat('end_bore_offset', self.bore_offset)
        self.bore_angle = self._getfloat('bore_angle', 0.0)
        self.inside = self._getboolean('inside', True)
        self.cycles = self._getfloat('cycles', 1.0)
        self.rotations = self._getint('rotations', 0)

        self.R = self.fixed_teeth * self.tooth_pitch / (2 * pi)
        self.r = self.rolling_teeth * self.tooth_pitch / (2 * pi)
        if self.rotations <= 0:
            g = gcd(self.fixed_teeth, self.rolling_teeth)
            self.rotations = self.rolling_teeth // g
        if self.inside:
            self.center_radius = self.R - self.r
            self.spin_ratio = -(self.R - self.r) / self.r
        else:
            self.center_radius = self.R + self.r
            self.spin_ratio = (self.R + self.r) / self.r

    # -- the kinematics ------------------------------------------------------------ #

    def _t_norm(self, t):
        period = float(self._pipeline_period)
        return t / period if period > 0 else t

    def _orbit(self, t):
        """The carrier's orbit angle round ring 1 at each t."""
        t_norm = self._t_norm(np.asarray(t, dtype=float))
        t_frac = (t_norm * self.cycles) % 1.0
        return t_frac * self.rotations * 2 * pi

    def heading(self, t):
        """The carrier's own spin: what the runner turns the load by. The
        orbit angle is taken modulo a trip, but a trip is a whole number of
        spins (that is what closing means), so the turn is continuous."""
        return self.spin_ratio * self._orbit(t)

    def transform(self, z, t):
        """z arrives already turned by heading(t); add the carrier's
        centre and the bore, the bore turned the same way."""
        theta = self._orbit(t)
        spin = self.spin_ratio * theta
        t_norm = self._t_norm(np.asarray(t, dtype=float))
        offset = self._interpolate(self.bore_offset, self.end_bore_offset,
                                   t_norm, 'bore_offset')
        bore = offset * np.exp(1j * (self.bore_angle * pi / 180 + spin))
        return z + self.center_radius * np.exp(1j * theta) + bore

    @property
    def natural_period(self) -> Fraction:
        return Fraction(self.cycles).limit_denominator(1000)

    def __repr__(self):
        where = "inside" if self.inside else "around"
        return (f"RingCarrierModule({self.rolling_teeth}T {where} {self.fixed_teeth}T, "
                f"bore {self.bore_offset:g} off, cycles={self.cycles})")
