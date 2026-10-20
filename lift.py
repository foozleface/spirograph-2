#!/usr/bin/env python3
"""
Lift Module
===========
The pen comes up, the table is moved on by hand, the pen goes down.

A clock, like `tempo`, for everything after it: the later modules see
time stand still through each of `steps` runs and jump to the next run's
position between one sample and the next. Unlike `tempo` in `stutter`
mode, which is a drive (a Geneva, a ratchet) that moves the table while
the pen stays on the paper, this is an operator's move: the pen is off the
paper while the table is turned, so the line is cut there. The runner
reads :meth:`lift_at` and breaks the curve at every jump -- no threshold
pen lift, no guessing from the length of a segment.

    [ti]
    type = lift
    steps = 13

    [s6]
    type = rotation
    total_degrees = 282

Thirteen runs; between them the table is turned 282 / 13 degrees with the
pen up. Put a `scale` with `scope = 1` oscillating `steps` times before
it for each run to swell small, large, small.
"""

import numpy as np
from fractions import Fraction
from main import TransformModule


class LiftModule(TransformModule):
    """
    The pen lifted and the later steps moved on by hand, `steps` times.

    Configuration:
        steps: how many runs the draw is made of; the pen comes up between
               one run and the next (default 8)
    """

    is_clock = True                 # the runner threads t through retime()

    def _load_config(self):
        self.steps = max(1, self._getint('steps', 8))

    def _run_index(self, t):
        T = float(self._pipeline_period)
        u = np.asarray(t, dtype=float) / T
        return np.floor(u * self.steps)

    def retime(self, t):
        """The time the modules after this one see: frozen through each run."""
        T = float(self._pipeline_period)
        v = self._run_index(t) / self.steps
        # Never hand back exactly T: every generator folds t = T onto t = 0.
        return np.minimum(v, 1.0 - 1e-12) * T

    def lift_at(self, t):
        """True at every sample that starts a new run: the pen came up after
        the sample before it and landed here."""
        k = self._run_index(t)
        up = np.zeros(k.shape, dtype=bool)
        if k.ndim and len(k) > 1:
            up[1:] = k[1:] != k[:-1]
        return up

    def transform(self, z, t):
        """A clock leaves the pen where it is."""
        return z

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    def __repr__(self):
        return f"LiftModule({self.steps})"
