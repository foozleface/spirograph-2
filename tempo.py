#!/usr/bin/env python3
"""
Tempo Module
============
Re-clocks everything after it. A clock, not an arm and not a table move:
it changes the *time* the later modules see, so a pattern that ran forward
runs backward, or there and back, or in steps with dwells, or several times
over, or with a phase shift — whatever the modules after it are.

    reverse    t' = T - t                 the draw runs backwards
    pingpong   there and back             out to the end, then home again
    stutter    n steps with dwells        stop, jump, stop — a Geneva feel
                                          for any pattern
    speed      t' = rate · t (mod T)      everything after repeats `rate`
                                          times over the draw
    offset     t' = t + phase · T         start part-way round
    ease       ease_in / ease_out / …     the whole draw accelerates or
                                          settles

Placed first it re-clocks the whole machine; placed after two arms it
re-clocks only the arms that follow — the arms before it keep their own
time. That is the composition that a per-module `easing` cannot do.
"""

import numpy as np
from fractions import Fraction
from main import TransformModule, apply_easing


class TempoModule(TransformModule):
    """
    A clock for the modules after it.

    Configuration:
        mode: reverse | pingpong | stutter | speed | offset | ease
        rate: for speed — how many times the later modules run (default 2)
        steps: for stutter — how many stops over the draw (default 8)
        dwell: for stutter — fraction of each step spent stopped (default 0.5)
        phase: for offset — fraction of the draw to start ahead (default 0.25)
        curve: for ease — the easing curve applied to the whole draw
    """

    is_clock = True                 # the runner threads t through retime()

    def _load_config(self):
        self.mode = self._get('mode', 'pingpong').strip().lower()
        self.rate = self._getfloat('rate', 2.0)
        self.steps = max(1, self._getint('steps', 8))
        self.dwell = min(max(self._getfloat('dwell', 0.5), 0.0), 0.95)
        self.phase = self._getfloat('phase', 0.25)
        self.curve = self._get('curve', 'ease_in_out').strip().lower()

    def retime(self, t):
        """The time the modules after this one will see."""
        T = float(self._pipeline_period)
        t = np.asarray(t, dtype=float)
        u = t / T                                # position in the draw, 0..1+
        if self.mode == 'reverse':
            v = 1.0 - u
        elif self.mode == 'pingpong':
            v = 1.0 - np.abs((2.0 * u) % 2.0 - 1.0)
        elif self.mode == 'stutter':
            n = self.steps
            k = np.floor(u * n)                  # which step we are in
            f = u * n - k                        # how far through it
            move = np.clip((f - self.dwell) / max(1.0 - self.dwell, 1e-9), 0.0, 1.0)
            move = move * move * (3 - 2 * move)  # smoothstep into the next stop
            v = (k + move) / n
        elif self.mode == 'speed':
            v = (u * self.rate) % 1.0
        elif self.mode == 'offset':
            v = (u + self.phase) % 1.0
        elif self.mode == 'ease':
            v = apply_easing(np.clip(u, 0.0, 1.0), self.curve)
        else:
            raise ValueError("tempo: unknown mode %r" % self.mode)
        # Never hand back exactly T: every generator folds t = T onto t = 0,
        # so a reversed draw would start with one point from the wrong end.
        return np.minimum(v, 1.0 - 1e-12) * T

    def transform(self, z, t):
        """A clock leaves the pen where it is."""
        return z

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    def __repr__(self):
        return f"TempoModule({self.mode})"
