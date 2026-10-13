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
    motor      switched on, spins up,     a real drive: it takes a while to
               maybe switched off again   reach speed, and if it is switched
                                          off before the end it coasts to a
                                          stop -- the table still while the
                                          pen draws its first (or last) loops

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
        on_at:  for motor — when it is switched on, as a fraction of the
                draw (default 0, the start)
        creep:  for motor — the speed, as a fraction of full speed, that
                what it drives is turned by hand before switch-on (default 0,
                still)
        nudges: for motor — turned by hand in this many separate nudges
                rather than smoothly, each position held as long as the
                others (default 0, smoothly)
        spinup: for motor — how long the drive takes to reach speed, as a
                fraction of the draw (0 is instant; default 0.1)
        off_at: for motor — when it is switched off, as a fraction of the
                draw (1, the default, is never)
        coast:  for motor — how long it takes to coast to a stop after being
                switched off, as a fraction of the draw (default 0.05)
        ripple: in any mode — the drive's speed pulses by this fraction of
                itself (default 0, none): a round belt's joint going over
                the pulley, a worm with a high spot
        ripple_per: how many pulses over the draw (default 100)
        unsteady: in any mode — the drive's speed wanders at random by up to
                this fraction of itself (default 0, steady): a hand on the
                crank, a motor under a varying load
        unsteady_wanders: how many slow swings the wandering makes over the
                draw (default 6)
    """

    is_clock = True                 # the runner threads t through retime()

    def _load_config(self):
        self.mode = self._get('mode', 'pingpong').strip().lower()
        self.rate = self._getfloat('rate', 2.0)
        self.steps = max(1, self._getint('steps', 8))
        self.dwell = min(max(self._getfloat('dwell', 0.5), 0.0), 0.95)
        self.phase = self._getfloat('phase', 0.25)
        self.curve = self._get('curve', 'ease_in_out').strip().lower()
        self.on_at = min(max(self._getfloat('on_at', 0.0), 0.0), 1.0)
        self.creep = max(self._getfloat('creep', 0.0), 0.0)
        self.nudges = max(self._getint('nudges', 0), 0)
        self.spinup = max(self._getfloat('spinup', 0.1), 0.0)
        self.off_at = min(max(self._getfloat('off_at', 1.0), 0.0), 1.0)
        self.coast = max(self._getfloat('coast', 0.05), 0.0)
        self.ripple = min(max(self._getfloat('ripple', 0.0), 0.0), 0.95)
        self.ripple_per = max(self._getfloat('ripple_per', 100.0), 0.0)
        self.unsteady = min(max(self._getfloat('unsteady', 0.0), 0.0), 0.5)
        self.unsteady_wanders = max(self._getfloat('unsteady_wanders', 6.0), 0.25)

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
        elif self.mode == 'motor':
            v = self._motor(np.clip(u, 0.0, 1.0)) / self._motor(1.0)
        else:
            raise ValueError("tempo: unknown mode %r" % self.mode)
        if self.unsteady:
            # Speed 1 + unsteady * (noise - its mean), integrated over the
            # draw: it wanders, but it arrives on time.
            from main import smooth_noise
            grid = np.linspace(0.0, 1.0, 2001)
            noise = smooth_noise(grid, self.unsteady_wanders, self.section + "/unsteady")
            gone = np.concatenate([[0.0], np.cumsum((noise[1:] + noise[:-1]) / 2 * np.diff(grid))])
            gone = gone - grid * gone[-1]
            v = v + self.unsteady * np.interp(np.clip(v, 0.0, 1.0), grid, gone)
        if self.ripple and self.ripple_per:
            # Speed 1 + ripple cos(2 pi n v), integrated: v gains a sine
            # that is 0 at both ends, so the draw still arrives on time.
            w = 2 * np.pi * self.ripple_per
            v = v + self.ripple / w * np.sin(w * v)
        # Never hand back exactly T: every generator folds t = T onto t = 0,
        # so a reversed draw would start with one point from the wrong end.
        return np.minimum(v, 1.0 - 1e-12) * T

    def _motor(self, u):
        """How far a drive has turned by u (0..1 of the draw), unnormalised.

        Before switch-on it is turned by hand at `creep` of full speed, if
        at all. From switch-on its speed rises towards full as
        1 - e^(-s/spinup), and once switched off it falls as
        e^(-s/coast): a motor against friction and the inertia of what it
        drives."""
        u = np.asarray(u, dtype=float)
        tau, creep = self.spinup, self.creep
        # By hand, before switch-on: smoothly, or in nudges with a pause
        # between them.
        hand = np.minimum(u, self.on_at)
        if self.nudges and self.on_at > 0:
            # n nudges make n + 1 held positions, each held as long as the
            # others; the nudge comes at the end of each hold but the last.
            n, pause = self.nudges, 0.5
            f = hand / self.on_at * (n + 1)
            k = np.minimum(np.floor(f), n)
            move = np.clip((f - k - pause) / (1.0 - pause), 0.0, 1.0)
            move = move * move * (3 - 2 * move)
            hand = np.minimum(k + move, n) / n * self.on_at
        turned = creep * hand
        # Running: from on_at until off_at.
        s = np.clip(u, self.on_at, max(self.off_at, self.on_at)) - self.on_at
        if tau > 0:
            turned = turned + creep * s + (1.0 - creep) * (s - tau * (1.0 - np.exp(-s / tau)))
        else:
            turned = turned + s
        # Switched off: coasting down from the speed it had.
        if self.off_at < 1.0:
            ran = max(self.off_at - self.on_at, 0.0)
            speed_off = (creep + (1.0 - creep) * (1.0 - np.exp(-ran / tau))) if tau > 0 else 1.0
            after = np.maximum(u - self.off_at, 0.0)
            if self.coast > 0:
                turned = turned + speed_off * self.coast * (1.0 - np.exp(-after / self.coast))
        return turned

    def transform(self, z, t):
        """A clock leaves the pen where it is."""
        return z

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    def __repr__(self):
        return f"TempoModule({self.mode})"
