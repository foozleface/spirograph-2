#!/usr/bin/env python3
"""
Pintograph Module
=================
The two-disc linkage that James Nolan Gandy's gear-and-pulley machines are:
two cranks turning at their own rates, a rod hinged on each, and the pen
where the two rods meet.

        crank 1 ●─────────╮                  ╭─────────● crank 2
        (spacing apart)   ╲ arm_1    arm_2  ╱
                           ╲               ╱
                            ●── the pen ──●   (one point: the elbow)

Each crank is a disc of radius `radius_n` turning `turns_n` times over the
draw from phase `phase_n`. The pen sits at the intersection of two circles —
radius arm_1 about crank 1's pin, radius arm_2 about crank 2's pin — and
`elbow` picks which of the two intersections (up or down). A small change
in the ratio turns_1 : turns_2 is a completely different drawing, which is
the whole game with these machines.

Gandy's cranks are "two stage eccentrically rotating disks": the pin is not
on the disc but on a second, smaller disc carried on the first, turning at
its own rate -- a planet on a carrier. `eccentric_n` is that second disc's
throw and `eccentric_turns_n` its turns over the draw (negative for the
other way), so the pin goes round a circle whose centre goes round a
circle. When the two stages run at nearly the same rate the crank's reach
breathes slowly between their difference and their sum; when the planet is
fast and the carrier slow the loops march round the carrier's circle.

A belt swapped while the machine is running (`switch_turns_1 = 0.5 9`:
from half-way, nine turns per draw) steps the rate and nothing else: the
shaft is where it was, it just turns faster or slower from then on.

If the arms are too short to meet, the pen is put at the midpoint of the
closest approach; the drawing shows a flat where that happened, which is
also what a real machine does when its rods bind.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class PintographModule(TransformModule):
    """
    Two cranks, two rods, a pen at the elbow.

    Configuration:
        spacing:  distance between the crank centres (default 200)
        radius_1, radius_2: crank radii — the pin's distance from its centre
        turns_1, turns_2:   how many times each crank goes round over the draw
                            (integers close; a ratio like 7:5 gives 7-fold
                            structure — the near-integer detunes make moiré)
        phase_1, phase_2:   starting angle of each crank, degrees
        eccentric_1, eccentric_2: the second stage's throw on each crank
                            (default 0, a plain crank)
        eccentric_turns_1, eccentric_turns_2: the second stage's turns over
                            the draw (default 0: a fixed offset)
        eccentric_phase_1, eccentric_phase_2: its starting angle, degrees
        arm_1, arm_2:       rod lengths from pin to pen
        elbow:              1 for the pen above the line of the pins, -1 below
        cycles:             repetitions of the whole draw
    """

    is_generator = True            # an arm: adds a vector to where the pen is

    def _load_config(self):
        self.spacing = self._getfloat('spacing', 200.0)
        self.radius_1 = self._getfloat('radius_1', 60.0)
        self.radius_2 = self._getfloat('radius_2', 45.0)
        self.end_radius_1 = self._getfloat('end_radius_1', self.radius_1)
        self.end_radius_2 = self._getfloat('end_radius_2', self.radius_2)
        self.turns_1 = self._getfloat('turns_1', 7.0)
        self.turns_2 = self._getfloat('turns_2', 5.0)
        self.phase_1 = self._getfloat('phase_1', 0.0) * pi / 180
        self.phase_2 = self._getfloat('phase_2', 90.0) * pi / 180
        self.eccentric_1 = self._getfloat('eccentric_1', 0.0)
        self.eccentric_2 = self._getfloat('eccentric_2', 0.0)
        self.end_eccentric_1 = self._getfloat('end_eccentric_1', self.eccentric_1)
        self.end_eccentric_2 = self._getfloat('end_eccentric_2', self.eccentric_2)
        self.eccentric_turns_1 = self._getfloat('eccentric_turns_1', 0.0)
        self.eccentric_turns_2 = self._getfloat('eccentric_turns_2', 0.0)
        self.eccentric_phase_1 = self._getfloat('eccentric_phase_1', 0.0) * pi / 180
        self.eccentric_phase_2 = self._getfloat('eccentric_phase_2', 0.0) * pi / 180
        self.arm_1 = self._getfloat('arm_1', 180.0)
        self.arm_2 = self._getfloat('arm_2', 180.0)
        self.elbow = 1.0 if self._getfloat('elbow', 1.0) >= 0 else -1.0
        # The pen on rod 1 past the elbow: a long rod's tip swings in wide,
        # smooth arcs where the elbow itself turns sharp corners. 0 is at
        # the elbow, as before.
        self.pen_extend = self._getfloat('pen_extend', 0.0)
        self.end_pen_extend = self._getfloat('end_pen_extend', self.pen_extend)
        self.cycles = self._getfloat('cycles', 1.0)

    def transform(self, z, t):
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        # Where in the draw the cranks are, in draws: the turns are
        # integrated from here (see _turned), so a rate stepped part-way
        # keeps the shaft where it was.
        t_run = t_norm * self.cycles

        r1 = self._interpolate(self.radius_1, self.end_radius_1, t_norm, 'radius_1')
        r2 = self._interpolate(self.radius_2, self.end_radius_2, t_norm, 'radius_2')

        # The two pins, each on its crank -- and, with an eccentric stage,
        # on a second disc carried round by the first.
        c1 = complex(-self.spacing / 2, 0.0)
        c2 = complex(self.spacing / 2, 0.0)
        p1 = c1 + r1 * np.exp(1j * (self.phase_1 + 2 * pi * self._turned(self.turns_1, t_run, 'turns_1')))
        p2 = c2 + r2 * np.exp(1j * (self.phase_2 + 2 * pi * self._turned(self.turns_2, t_run, 'turns_2')))
        if self.eccentric_1 or self.end_eccentric_1:
            e1 = self._interpolate(self.eccentric_1, self.end_eccentric_1, t_norm, 'eccentric_1')
            p1 = p1 + e1 * np.exp(1j * (self.eccentric_phase_1 + 2 * pi * self._turned(
                self.eccentric_turns_1, t_run, 'eccentric_turns_1')))
        if self.eccentric_2 or self.end_eccentric_2:
            e2 = self._interpolate(self.eccentric_2, self.end_eccentric_2, t_norm, 'eccentric_2')
            p2 = p2 + e2 * np.exp(1j * (self.eccentric_phase_2 + 2 * pi * self._turned(
                self.eccentric_turns_2, t_run, 'eccentric_turns_2')))

        # Where two circles meet: radius arm_1 about p1, arm_2 about p2.
        d = np.abs(p2 - p1)
        d = np.where(d < 1e-9, 1e-9, d)
        u = (p2 - p1) / d                                  # unit, pin to pin
        arm_1 = self._interpolate(self.arm_1, self.arm_1, t_norm, 'arm_1')
        arm_2 = self._interpolate(self.arm_2, self.arm_2, t_norm, 'arm_2')
        a = (arm_1 ** 2 - arm_2 ** 2 + d ** 2) / (2 * d)
        h = np.sqrt(np.maximum(arm_1 ** 2 - a ** 2, 0.0))
        pen = p1 + a * u + self.elbow * h * (1j * u)
        extend = self._interpolate(self.pen_extend, self.end_pen_extend, t_norm, 'pen_extend')
        if np.any(extend != 0):
            pen = pen + extend * (pen - p1) / arm_1

        # Centre the drawing on the pen's rest position so it composes like
        # the other arms: the mechanism's frame, not the paper's corner.
        return z + pen

    @property
    def natural_period(self) -> Fraction:
        return Fraction(self.cycles).limit_denominator(1000)

    def __repr__(self):
        ecc = ""
        if self.eccentric_1 or self.eccentric_2:
            ecc = (f", eccentric={self.eccentric_1:g}@{self.eccentric_turns_1:g}"
                   f"/{self.eccentric_2:g}@{self.eccentric_turns_2:g}")
        return (f"PintographModule({self.turns_1:g}:{self.turns_2:g}, "
                f"r={self.radius_1:g}/{self.radius_2:g}, arms={self.arm_1:g}/{self.arm_2:g}{ecc})")
