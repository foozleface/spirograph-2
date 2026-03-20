#!/usr/bin/env python3
"""
Circle Module
=============
Draws a simple circle, optionally growing or shrinking over time.

This is a basic shape generator useful as a starting point
or for combining with other transformations.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class CircleModule(TransformModule):
    """
    Simple circle generator.
    
    Configuration:
        radius: Circle radius (or starting radius if growing)
        end_radius: Ending radius (for grow/shrink, default = radius)
        cycles: Number of times around the circle
        start_x, start_y: Center offset
    """
    
    def _load_config(self):
        """Load circle configuration."""
        self.radius = self._getfloat('radius', 50.0)
        self.end_radius = self._getfloat('end_radius', self.radius)
        self.cycles = self._getfloat('cycles', 1.0)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on circle at time t.
        
        With cycles > 1, draws the circle multiple times.
        Combined with transforms, creates moiré effects.
        """
        # Normalize t to [0,1] for global interpolation
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Interpolate radius based on overall progress
        current_radius = self.radius + t_norm * (self.end_radius - self.radius)
        
        # Angle for this single circle (one full revolution per cycle)
        angle = t_frac * 2 * pi
        
        # Point on circle
        point = current_radius * np.exp(1j * angle)
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        if self.radius == self.end_radius:
            return f"CircleModule(r={self.radius}, cycles={self.cycles})"
        return f"CircleModule(r={self.radius}→{self.end_radius}, cycles={self.cycles})"
