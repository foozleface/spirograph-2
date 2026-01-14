#!/usr/bin/env python3
"""
Star Module
===========
Draws pointed stars (not regular polygons - these have inner and outer radii).

A 5-pointed star has 5 outer points and 5 inner vertices.
The skip parameter controls how connected the points are.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class StarShapeModule(TransformModule):
    """
    Pointed star generator.
    
    Configuration:
        points: Number of points (5 = classic 5-pointed star)
        outer_radius: Radius to outer points
        inner_radius: Radius to inner vertices (0 = auto 38% of outer)
        end_outer_radius: Ending outer radius for animation
        end_inner_radius: Ending inner radius for animation
        cycles: Number of times around the star
        rotation: Initial rotation in degrees
        start_x, start_y: Center position
    """
    
    def _load_config(self):
        """Load star configuration."""
        self.points = self._getint('points', 5)
        self.outer_radius = self._getfloat('outer_radius', 50.0)
        default_inner = self.outer_radius * 0.382  # Golden ratio based
        self.inner_radius = self._getfloat('inner_radius', default_inner)
        self.end_outer_radius = self._getfloat('end_outer_radius', self.outer_radius)
        self.end_inner_radius = self._getfloat('end_inner_radius', self.inner_radius)
        self.cycles = self._getfloat('cycles', 1.0)
        self.rotation_deg = self._getfloat('rotation', -90.0)  # Point up by default
        
        self.rotation_rad = self.rotation_deg * pi / 180
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on star perimeter at time t.
        
        With cycles > 1, draws the star multiple times.
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
        outer_r = self.outer_radius + t_norm * (self.end_outer_radius - self.outer_radius)
        inner_r = self.inner_radius + t_norm * (self.end_inner_radius - self.inner_radius)
        
        # Total vertices = 2 * points (alternating outer/inner)
        total_vertices = self.points * 2
        
        # Progress around this single star
        vertex_progress = (t_frac * total_vertices) % total_vertices
        vertex_index = int(vertex_progress)
        vertex_frac = vertex_progress - vertex_index
        
        # Get radii for current and next vertex
        is_outer = (vertex_index % 2 == 0)
        r1 = outer_r if is_outer else inner_r
        r2 = inner_r if is_outer else outer_r
        
        # Angles
        angle1 = self.rotation_rad + (vertex_index / total_vertices) * 2 * pi
        angle2 = self.rotation_rad + ((vertex_index + 1) / total_vertices) * 2 * pi
        
        # Vertices
        v1 = r1 * np.exp(1j * angle1)
        v2 = r2 * np.exp(1j * angle2)
        
        # Interpolate
        point = v1 + vertex_frac * (v2 - v1)
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return f"StarModule({self.points}-pointed, outer={self.outer_radius}, inner={self.inner_radius})"
