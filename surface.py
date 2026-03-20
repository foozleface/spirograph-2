#!/usr/bin/env python3
"""
Surface Module
==============
Generates 3D parametric surfaces projected to 2D.

Unlike path-based modules that trace a single curve, this module sweeps
two parameters (u, v) across a surface and draws parallel lines.

Supports: torus, mobius strip, twisted ribbon, sphere, klein bottle, etc.
"""

import numpy as np
from fractions import Fraction
from math import pi, sin, cos
from main import TransformModule


class SurfaceModule(TransformModule):
    """
    3D parametric surface generator with 2D projection.
    
    The surface is drawn as a series of parallel curves - sweeping u
    while stepping through v values.
    
    Configuration:
        surface: Type of surface (torus, mobius, ribbon, sphere, klein)
        
        # Size parameters
        major_radius: For torus - radius from center to tube center
        minor_radius: For torus - radius of the tube itself
        width: For ribbon/mobius - width of the strip
        
        # Sweep parameters  
        u_min, u_max: Range for u parameter (usually 0 to 2π)
        v_min, v_max: Range for v parameter
        v_lines: Number of parallel lines to draw
        
        # Twist parameters (for ribbon/mobius)
        twists: Number of half-twists (2 = full twist, 1 = mobius)
        
        # View parameters
        view_angle_x: Rotation around X axis (degrees)
        view_angle_y: Rotation around Y axis (degrees) 
        view_angle_z: Rotation around Z axis (degrees)
        scale: Overall scale factor
        
        # Drawing
        cycles: Number of times to draw all v_lines (for moiré with transforms)
    """
    
    def _load_config(self):
        """Load surface configuration."""
        self.surface_type = self._get('surface', 'torus').lower()
        
        # Size parameters
        self.major_radius = self._getfloat('major_radius', 100.0)
        self.minor_radius = self._getfloat('minor_radius', 40.0)
        self.width = self._getfloat('width', 60.0)
        self.length = self._getfloat('length', 200.0)
        
        # Sweep parameters
        self.u_min = self._getfloat('u_min', 0.0)
        self.u_max = self._getfloat('u_max', 2 * pi)
        self.v_min = self._getfloat('v_min', 0.0)
        self.v_max = self._getfloat('v_max', 2 * pi)
        self.v_lines = self._getint('v_lines', 40)
        
        # Twist parameters
        self.twists = self._getfloat('twists', 0.0)
        
        # View parameters (degrees)
        self.view_angle_x = self._getfloat('view_angle_x', 20.0) * pi / 180
        self.view_angle_y = self._getfloat('view_angle_y', 0.0) * pi / 180
        self.view_angle_z = self._getfloat('view_angle_z', 0.0) * pi / 180
        self.scale = self._getfloat('scale', 1.0)
        
        # Cycles for moiré
        self.cycles = self._getfloat('cycles', 1.0)
        
        # Precompute rotation matrices
        self._compute_rotation_matrix()
    
    def _compute_rotation_matrix(self):
        """Precompute combined rotation matrix."""
        # Rotation around X
        cx, sx = cos(self.view_angle_x), sin(self.view_angle_x)
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        
        # Rotation around Y
        cy, sy = cos(self.view_angle_y), sin(self.view_angle_y)
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        
        # Rotation around Z
        cz, sz = cos(self.view_angle_z), sin(self.view_angle_z)
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        
        # Combined rotation: first Z, then Y, then X
        self.rotation_matrix = Rx @ Ry @ Rz
    
    def _surface_point(self, u: float, v: float) -> tuple:
        """
        Compute 3D point on surface for parameters (u, v).
        Returns (x, y, z).
        """
        if self.surface_type == 'torus':
            # Torus: (R + r*cos(v)) * cos(u), (R + r*cos(v)) * sin(u), r*sin(v)
            R, r = self.major_radius, self.minor_radius
            x = (R + r * cos(v)) * cos(u)
            y = (R + r * cos(v)) * sin(u)
            z = r * sin(v)
            
        elif self.surface_type == 'mobius':
            # Möbius strip: 1 half-twist
            R = self.major_radius
            w = self.width
            # v goes from -0.5 to 0.5 (across width)
            v_scaled = (v / (2 * pi) - 0.5) * w
            x = (R + v_scaled * cos(u / 2)) * cos(u)
            y = (R + v_scaled * cos(u / 2)) * sin(u)
            z = v_scaled * sin(u / 2)
            
        elif self.surface_type == 'ribbon':
            # Twisted ribbon with configurable twists
            R = self.major_radius
            w = self.width
            twist_angle = self.twists * pi * u / (self.u_max - self.u_min)
            # v goes from -0.5 to 0.5 (across width)
            v_scaled = (v / (2 * pi) - 0.5) * w
            x = (R + v_scaled * cos(twist_angle)) * cos(u)
            y = (R + v_scaled * cos(twist_angle)) * sin(u)
            z = v_scaled * sin(twist_angle)
            
        elif self.surface_type == 'sphere':
            # Sphere: r*sin(v)*cos(u), r*sin(v)*sin(u), r*cos(v)
            r = self.major_radius
            x = r * sin(v) * cos(u)
            y = r * sin(v) * sin(u)
            z = r * cos(v)
            
        elif self.surface_type == 'klein':
            # Klein bottle (figure-8 immersion)
            r = self.minor_radius
            R = self.major_radius
            if u < pi:
                x = (R + r * cos(u)) * cos(u) - r * sin(u) * cos(v)
                y = (R + r * cos(u)) * sin(u)
                z = r * sin(v)
            else:
                x = (R + r * cos(u)) * cos(u) + r * sin(u) * cos(v)
                y = (R + r * cos(u)) * sin(u)
                z = r * sin(v)
                
        elif self.surface_type == 'helix_ribbon':
            # Helical ribbon - ribbon that also rises in Z
            R = self.major_radius
            w = self.width
            pitch = self._getfloat('pitch', 50.0)
            twist_angle = self.twists * pi * u / (self.u_max - self.u_min)
            v_scaled = (v / (2 * pi) - 0.5) * w
            x = (R + v_scaled * cos(twist_angle)) * cos(u)
            y = (R + v_scaled * cos(twist_angle)) * sin(u)
            z = v_scaled * sin(twist_angle) + pitch * u / (2 * pi)
            
        elif self.surface_type == 'figure8':
            # Figure-8 torus (self-intersecting)
            R = self.major_radius
            r = self.minor_radius
            x = (R + r * cos(v)) * cos(u)
            y = (R + r * cos(v)) * sin(u) * cos(u)
            z = r * sin(v)
            
        else:
            # Default to torus
            R, r = self.major_radius, self.minor_radius
            x = (R + r * cos(v)) * cos(u)
            y = (R + r * cos(v)) * sin(u)
            z = r * sin(v)
        
        return x, y, z
    
    def _project(self, x: float, y: float, z: float) -> complex:
        """Project 3D point to 2D complex number."""
        # Apply rotation
        point = np.array([x, y, z])
        rotated = self.rotation_matrix @ point
        
        # Orthographic projection (drop z)
        return complex(rotated[0] * self.scale, rotated[1] * self.scale)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on surface at time t.
        
        Single continuous spiral: u sweeps around many times (v_lines rotations)
        while v gradually increases from v_min to v_max.
        
        No direction changes - just one smooth spiral from start to finish.
        """
        # Normalize t to [0, 1]
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Apply cycles
        t_in_cycles = t_norm * self.cycles
        t_frac = t_in_cycles % 1.0
        
        # u sweeps around v_lines times (continuous rotation)
        u = self.u_min + t_frac * self.v_lines * (self.u_max - self.u_min)
        
        # v increases linearly from min to max over the entire drawing
        v = self.v_min + t_frac * (self.v_max - self.v_min)
        
        # Get 3D point and project
        x3d, y3d, z3d = self._surface_point(u, v)
        point_2d = self._project(x3d, y3d, z3d)
        
        return z + point_2d
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return f"SurfaceModule({self.surface_type}, R={self.major_radius}, r={self.minor_radius})"
