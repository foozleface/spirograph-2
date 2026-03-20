#!/usr/bin/env python3
"""
Guilloche Module
================
Generates guilloche (engine-turning) patterns — the intricate interlocking
curves found on banknotes, certificates, and watch cases.

A guilloche pattern is created by tracing a point whose radius oscillates
between an inner and outer envelope as it sweeps around a circle. The
envelopes themselves can oscillate, creating complex interference.

The core formula:
    r0(t) = inner + sin(t * n0) * h0          # inner boundary
    r1(t) = outer + sin(t * n1) * h1          # outer boundary
    range = (r1 - r0) / 2
    mid = r0 + range
    radius(t) = mid + sin(t * nodes / div) * range
    x = cos(t) * radius
    y = sin(t) * radius

where t goes from 0 to 2π * div.

Critical constraint: nodes and div must NOT be evenly divisible.
Using a prime number for div guarantees this for most node values.

Based on research from bit-101 Coding Curves and Wolfram MathWorld.
"""

import numpy as np
from fractions import Fraction
from math import pi, sin, cos, gcd
from main import TransformModule


class GuillocheModule(TransformModule):
    """
    Guilloche pattern generator.

    Configuration:
        inner: Inner envelope base radius (default 60)
        outer: Outer envelope base radius (default 180)
        nodes: Number of oscillations in the main wave (default 120)
        div: Overlap factor — MUST be prime for best results (default 37)
        n0: Inner envelope oscillation count (default 6)
        h0: Inner envelope amplitude (default 10)
        n1: Outer envelope oscillation count (default 12)
        h1: Outer envelope amplitude (default 15)
        end_inner/end_outer: Drift for envelopes
        end_nodes: Drift for node count (creates evolving density)
    """

    def _load_config(self):
        self.inner = self._getfloat('inner', 60.0)
        self.outer = self._getfloat('outer', 180.0)
        self.end_inner = self._getfloat('end_inner', self.inner)
        self.end_outer = self._getfloat('end_outer', self.outer)
        self.nodes = self._getfloat('nodes', 120.0)
        self.end_nodes = self._getfloat('end_nodes', self.nodes)
        self.div = self._getint('div', 37)
        self.n0 = self._getfloat('n0', 6.0)
        self.h0 = self._getfloat('h0', 10.0)
        self.n1 = self._getfloat('n1', 12.0)
        self.h1 = self._getfloat('h1', 15.0)
        self.cycles = self._getfloat('cycles', 1.0)

    def transform(self, z: complex, t: float) -> complex:
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t

        # Drift interpolation
        inner = self.inner + t_norm * (self.end_inner - self.inner)
        outer = self.outer + t_norm * (self.end_outer - self.outer)
        nodes = self.nodes + t_norm * (self.end_nodes - self.nodes)

        # Map t to angle: full sweep is 2π * div * cycles
        angle = t_norm * 2 * pi * self.div * self.cycles

        # Inner and outer envelope boundaries
        r0 = inner + sin(angle * self.n0) * self.h0
        r1 = outer + sin(angle * self.n1) * self.h1

        # Main oscillation between boundaries
        half_range = (r1 - r0) * 0.5
        mid = r0 + half_range
        radius = mid + sin(angle * nodes / self.div) * half_range

        # Convert to complex point
        x = cos(angle) * radius
        y = sin(angle) * radius

        return z + complex(x, y)

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    @property
    def is_generator(self) -> bool:
        return True

    def __repr__(self):
        return f"GuillocheModule(inner={self.inner}, outer={self.outer}, nodes={self.nodes}, div={self.div})"
