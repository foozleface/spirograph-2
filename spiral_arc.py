#!/usr/bin/env python3
"""
Spiral Arc Module
=================
Translates the pattern along a spiral path (radius increases as it goes around).
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class SpiralArcModule(TransformModule):
    """
    Spiral arc: pattern SLIDES along a spiral path.
    
    Like arc, but the radius changes as it goes around.
    This is a SLIDING transform - it moves the pattern along a spiral trajectory.
    
    Configuration:
        inner_radius: Starting radius
        outer_radius: Ending radius
        start_angle: Starting angle in degrees
        sweep_angle: Total angle swept in degrees
        center_x, center_y: Center of the spiral
        cycles: Number of spiral arms/traversals
        normalize: If true, normalize t to [0,1] regardless of pipeline period
    """
    
    def _load_config(self):
        """Load spiral configuration."""
        self.inner_radius = self._getfloat('inner_radius', 50.0)
        self.outer_radius = self._getfloat('outer_radius', 150.0)
        self.start_angle = self._getfloat('start_angle', 0.0)
        self.sweep_angle = self._getfloat('sweep_angle', 720.0)
        self.center_x = self._getfloat('center_x', 0.0)
        self.center_y = self._getfloat('center_y', 0.0)
        self.cycles = self._getfloat('cycles', 1.0)
        self.normalize = self._getboolean('normalize', True)
        
        # Convert to radians
        self.start_rad = self.start_angle * pi / 180
        self.sweep_rad = self.sweep_angle * pi / 180
        
        # Center as complex
        self.center = self.center_x + 1j * self.center_y
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Translate input coordinates along a spiral path.
        """
        # Normalize t to [0,1] if requested
        if self.normalize:
            period = float(self._pipeline_period)
            t_use = t / period if period > 0 else t
        else:
            t_use = t
        
        # Current angle
        angle = self.start_rad + t_use * self.sweep_rad
        
        # Interpolate radius
        radius = self.inner_radius + t_use * (self.outer_radius - self.inner_radius)
        
        # Position on the spiral
        spiral_position = self.center + radius * np.exp(1j * angle)
        
        return z + spiral_position
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        if self.cycles == 0:
            return Fraction(1, 1)
        return Fraction(self.cycles).limit_denominator(1000)
    
    @property
    def is_generator(self) -> bool:
        return False
    
    def __repr__(self):
        return (f"SpiralArcModule(r={self.inner_radius}->{self.outer_radius}, "
                f"sweep={self.sweep_angle}°)")
