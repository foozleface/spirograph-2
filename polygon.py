#!/usr/bin/env python3
"""
Polygon Module
==============
Draws regular polygons (triangle, square, pentagon, etc.)
with optional grow/shrink animation.

Vertices are computed at equal angles, then interpolated
to create smooth edges.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class PolygonModule(TransformModule):
    """
    Regular polygon generator.
    
    Configuration:
        sides: Number of sides (3=triangle, 4=square, 5=pentagon, etc.)
        radius: Circumradius (distance from center to vertices)
        end_radius: Ending radius for grow/shrink (default = radius)
        cycles: Number of times around the polygon
        rotation: Initial rotation in degrees
        start_x, start_y: Center position
    """
    
    def _load_config(self):
        """Load polygon configuration."""
        self.sides = self._getint('sides', 4)
        self.radius = self._getfloat('radius', 50.0)
        self.end_radius = self._getfloat('end_radius', self.radius)
        self.cycles = self._getfloat('cycles', 1.0)
        self.rotation_deg = self._getfloat('rotation', 0.0)
        
        self.rotation_rad = self.rotation_deg * pi / 180
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on polygon perimeter at time t.
        
        With cycles > 1, draws the polygon multiple times.
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
        
        # Progress around this single polygon
        side_progress = (t_frac * self.sides) % self.sides
        side_index = int(side_progress)
        side_frac = side_progress - side_index
        
        # Vertices
        angle1 = self.rotation_rad + (side_index / self.sides) * 2 * pi
        angle2 = self.rotation_rad + ((side_index + 1) / self.sides) * 2 * pi
        
        v1 = current_radius * np.exp(1j * angle1)
        v2 = current_radius * np.exp(1j * angle2)
        
        # Interpolate along edge
        point = v1 + side_frac * (v2 - v1)
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        names = {3: 'triangle', 4: 'square', 5: 'pentagon', 6: 'hexagon'}
        name = names.get(self.sides, f'{self.sides}-gon')
        return f"PolygonModule({name}, r={self.radius})"


class TriangleModule(PolygonModule):
    """Convenience class for triangles."""
    def _load_config(self):
        super()._load_config()
        self.sides = 3


class SquareModule(PolygonModule):
    """Convenience class for squares."""
    def _load_config(self):
        super()._load_config()
        self.sides = 4


class PentagonModule(PolygonModule):
    """Convenience class for pentagons."""
    def _load_config(self):
        super()._load_config()
        self.sides = 5


class HexagonModule(PolygonModule):
    """Convenience class for hexagons."""
    def _load_config(self):
        super()._load_config()
        self.sides = 6
