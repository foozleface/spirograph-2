#!/usr/bin/env python3
"""
Ellipse Module
==============
Draws ellipses (ovals) with configurable semi-axes.
Can grow/shrink over time.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class EllipseModule(TransformModule):
    """
    Ellipse generator.
    
    Configuration:
        radius_x: Semi-major axis (horizontal radius)
        radius_y: Semi-minor axis (vertical radius)
        end_radius_x: Ending horizontal radius (for animation)
        end_radius_y: Ending vertical radius (for animation)
        cycles: Number of times around the ellipse
        rotation: Ellipse rotation in degrees
        start_x, start_y: Center position
    """
    
    def _load_config(self):
        """Load ellipse configuration."""
        self.radius_x = self._getfloat('radius_x', 50.0)
        self.radius_y = self._getfloat('radius_y', 30.0)
        self.end_radius_x = self._getfloat('end_radius_x', self.radius_x)
        self.end_radius_y = self._getfloat('end_radius_y', self.radius_y)
        self.cycles = self._getfloat('cycles', 1.0)
        self.rotation_deg = self._getfloat('rotation', 0.0)
        
        self.rotation_rad = self.rotation_deg * pi / 180
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on ellipse at time t.
        
        With cycles > 1, draws the ellipse multiple times.
        Combined with transforms, creates moiré effects.
        """
        # Normalize t to [0,1] for global interpolation
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Interpolate radii based on overall progress
        rx = self.radius_x + t_norm * (self.end_radius_x - self.radius_x)
        ry = self.radius_y + t_norm * (self.end_radius_y - self.radius_y)
        
        # Angle for this single ellipse (one full revolution per cycle)
        angle = t_frac * 2 * pi
        
        # Point on ellipse (before rotation)
        x = rx * np.cos(angle)
        y = ry * np.sin(angle)
        point = x + 1j * y
        
        # Apply rotation
        point *= np.exp(1j * self.rotation_rad)
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return f"EllipseModule(rx={self.radius_x}, ry={self.radius_y})"
