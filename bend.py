#!/usr/bin/env python3
"""
Bend Module
===========
Bends/warps a pattern by mapping Cartesian coordinates to polar coordinates.

This transforms a flat pattern into a curved one:
- Input X coordinate → angle along the arc
- Input Y coordinate → radial distance from arc center

Think of it like wrapping a flat sheet around a cylinder.

Example: A horizontal line from (0,0) to (100,0) bent with sweep_angle=90
becomes a 90° arc segment.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class BendModule(TransformModule):
    """
    Bend transformation: maps X→angle, Y→radius.
    
    Configuration:
        radius: Base radius of the bend (distance from center to where Y=0 maps)
        start_angle: Starting angle in degrees (where X=0 maps)
        sweep_angle: Angular range to map X coordinates into (degrees)
        x_range: The X range of input to map (default: auto-fit)
        center_x, center_y: Center point of the bend arc
        direction: 1 = bend upward (convex), -1 = bend downward (concave)
    
    The transformation:
        - x_input in [0, x_range] → angle in [start_angle, start_angle + sweep_angle]
        - y_input → radius offset from base radius
    """
    
    def _load_config(self):
        """Load bend configuration."""
        self.radius = self._getfloat('radius', 200.0)
        self.start_angle = self._getfloat('start_angle', 0.0)
        self.sweep_angle = self._getfloat('sweep_angle', 90.0)
        self.x_range = self._getfloat('x_range', 0.0)  # 0 = auto
        self.center_x = self._getfloat('center_x', 0.0)
        self.center_y = self._getfloat('center_y', 0.0)
        self.direction = self._getint('direction', 1)
        
        # Convert to radians
        self.start_rad = self.start_angle * pi / 180
        self.sweep_rad = self.sweep_angle * pi / 180
        
        # Center as complex
        self.center = self.center_x + 1j * self.center_y
        
        # If x_range not specified, compute from radius and sweep
        # Arc length = radius * angle_in_radians
        if self.x_range <= 0:
            self.x_range = self.radius * abs(self.sweep_rad)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Bend the input coordinates.
        
        Maps (x, y) → polar coordinates centered on the arc.
        """
        x = z.real
        y = z.imag
        
        # Map x to angle
        # x=0 → start_angle, x=x_range → start_angle + sweep_angle
        if self.x_range != 0:
            normalized_x = x / self.x_range
        else:
            normalized_x = 0
        
        angle = self.start_rad + normalized_x * self.sweep_rad
        
        # Map y to radius offset
        # y=0 → base radius, y>0 → further from center (if direction=1)
        r = self.radius + self.direction * y
        
        # Convert to Cartesian
        result = self.center + r * np.exp(1j * angle)
        
        return result
    
    @property
    def natural_period(self) -> Fraction:
        """Bend doesn't affect period."""
        return Fraction(1, 1)
    
    @property
    def is_generator(self) -> bool:
        return False
    
    def __repr__(self):
        return f"BendModule(r={self.radius}, sweep={self.sweep_angle}°)"


class BendVerticalModule(TransformModule):
    """
    Vertical bend: maps Y→angle, X→radius.
    
    Like BendModule but rotated 90° - bends vertical patterns into arcs.
    
    Configuration:
        radius: Base radius of the bend
        start_angle: Starting angle in degrees
        sweep_angle: Angular range to map Y coordinates into
        y_range: The Y range of input to map (default: auto-fit)
        center_x, center_y: Center point of the bend arc
        direction: 1 = bend rightward, -1 = bend leftward
    """
    
    def _load_config(self):
        """Load bend configuration."""
        self.radius = self._getfloat('radius', 200.0)
        self.start_angle = self._getfloat('start_angle', -90.0)  # Start pointing down
        self.sweep_angle = self._getfloat('sweep_angle', 90.0)
        self.y_range = self._getfloat('y_range', 0.0)  # 0 = auto
        self.center_x = self._getfloat('center_x', 0.0)
        self.center_y = self._getfloat('center_y', 0.0)
        self.direction = self._getint('direction', 1)
        
        # Convert to radians
        self.start_rad = self.start_angle * pi / 180
        self.sweep_rad = self.sweep_angle * pi / 180
        
        # Center as complex
        self.center = self.center_x + 1j * self.center_y
        
        # If y_range not specified, compute from radius and sweep
        if self.y_range <= 0:
            self.y_range = self.radius * abs(self.sweep_rad)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Bend the input coordinates (vertical version).
        """
        x = z.real
        y = z.imag
        
        # Map y to angle
        if self.y_range != 0:
            normalized_y = y / self.y_range
        else:
            normalized_y = 0
        
        angle = self.start_rad + normalized_y * self.sweep_rad
        
        # Map x to radius offset
        r = self.radius + self.direction * x
        
        # Convert to Cartesian
        result = self.center + r * np.exp(1j * angle)
        
        return result
    
    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)
    
    @property
    def is_generator(self) -> bool:
        return False
    
    def __repr__(self):
        return f"BendVerticalModule(r={self.radius}, sweep={self.sweep_angle}°)"
