#!/usr/bin/env python3
"""
Spiral Module
=============
Draws Archimedean spirals: r = a + b*θ

The spiral grows outward (or inward) as it rotates.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class SpiralShapeModule(TransformModule):
    """
    Archimedean spiral generator.
    
    Configuration:
        start_radius: Starting radius
        end_radius: Ending radius
        turns: Number of spiral turns
        direction: 1 for outward, -1 for inward
        cycles: Number of times to draw the spiral (for moiré with transforms)
    """
    
    def _load_config(self):
        """Load spiral configuration."""
        self.start_radius = self._getfloat('start_radius', 0.0)
        self.end_radius = self._getfloat('end_radius', 50.0)
        self.turns = self._getfloat('turns', 3.0)
        self.direction = self._getint('direction', 1)
        self.cycles = self._getfloat('cycles', 1.0)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on spiral at time t.
        
        With cycles > 1, draws the spiral multiple times.
        Combined with transforms, creates moiré effects.
        """
        # Normalize t to [0,1] for global interpolation
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Radius grows linearly within each spiral
        r = self.start_radius + t_frac * (self.end_radius - self.start_radius)
        
        # Angle for this single spiral
        angle = self.direction * t_frac * self.turns * 2 * pi
        
        point = r * np.exp(1j * angle)
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return f"SpiralModule({self.start_radius}→{self.end_radius}, {self.turns} turns, cycles={self.cycles})"
