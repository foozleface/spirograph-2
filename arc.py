#!/usr/bin/env python3
"""
Arc Module
==========
Makes the pattern SLIDE along a circular arc path as it draws.

This is a SLIDING TRANSFORM - it adds a position offset that moves along 
an arc over time. The pattern itself is NOT bent or warped.

Think of it like this:
- You're drawing a pattern
- As you draw, someone slowly moves the paper in an arc underneath
- The pattern follows/traces the arc path

Example: circle + arc = a circle that orbits along an arc while drawing
Result: the circle pattern appears multiple places along an arc trajectory

IMPORTANT: This is different from the 'bend' module!
- arc = pattern MOVES along arc path (sliding transform)
- bend = pattern is WARPED into arc shape (coordinate remap)

If you want to turn a straight line INTO an arc shape, use 'bend'.
If you want a pattern to FOLLOW an arc trajectory, use 'arc'.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class ArcModule(TransformModule):
    """
    Arc path: translates input coordinates along a circular arc.
    
    This is a TRANSFORMER module - it modifies input z based on time t.
    
    Configuration:
        radius: Radius of the arc path
        start_angle: Starting angle in degrees (0 = right, 90 = up)
        sweep_angle: Total angle swept in degrees (positive = counter-clockwise)
        center_x, center_y: Center of the arc
        cycles: Number of times to traverse the arc (can be fractional)
    """
    
    def _load_config(self):
        """Load arc configuration."""
        self.radius = self._getfloat('radius', 100.0)
        self.start_angle = self._getfloat('start_angle', 0.0)
        self.sweep_angle = self._getfloat('sweep_angle', 180.0)
        self.center_x = self._getfloat('center_x', 0.0)
        self.center_y = self._getfloat('center_y', 0.0)
        self.cycles = self._getfloat('cycles', 1.0)
        self.normalize = self._getboolean('normalize', True)
        
        # Convert to radians
        self.start_rad = self.start_angle * pi / 180
        self.sweep_rad = self.sweep_angle * pi / 180
        
        # Arc center as complex number
        self.center = self.center_x + 1j * self.center_y
        
        # Compute period based on sweep and cycles
        self._compute_period()
    
    def _compute_period(self):
        """Compute the natural period based on arc configuration."""
        # One full traversal of the arc is one "cycle" of this module
        # If cycles > 1, we repeat the arc traversal
        if self.cycles == 0:
            self._period = Fraction(1, 1)
        else:
            self._period = Fraction(self.cycles).limit_denominator(1000)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Translate input coordinates along the arc.
        
        Args:
            z: Input position to transform
            t: Time parameter in [0, 1] (or beyond for multi-cycle)
            
        Returns:
            Translated position along the arc
        """
        # Normalize t to [0,1] if requested, using pipeline period
        if self.normalize:
            period = float(self._pipeline_period)
            t_use = t / period if period > 0 else t
        else:
            t_use = t
        
        # Current angle along the arc
        angle = self.start_rad + t_use * self.sweep_rad
        
        # Position on the arc
        arc_position = self.center + self.radius * np.exp(1j * angle)
        
        # Translate input by the arc position
        return z + arc_position
    
    @property
    def natural_period(self) -> Fraction:
        """
        Period of the arc traversal.
        """
        return self._period
    
    @property
    def is_generator(self) -> bool:
        """This module transforms coordinates."""
        return False
    
    def __repr__(self):
        return (f"ArcModule(r={self.radius}, start={self.start_angle}°, "
                f"sweep={self.sweep_angle}°, cycles={self.cycles})")


class SpiralArcModule(TransformModule):
    """
    Spiral arc: like ArcModule but the radius changes over time.
    
    Creates spiral patterns by varying the radius from inner_radius to
    outer_radius as the arc is traversed.
    
    Configuration:
        inner_radius: Starting radius
        outer_radius: Ending radius
        start_angle: Starting angle in degrees
        sweep_angle: Total angle swept in degrees
        center_x, center_y: Center of the spiral
        cycles: Number of spiral arms/traversals
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
        
        # Convert to radians
        self.start_rad = self.start_angle * pi / 180
        self.sweep_rad = self.sweep_angle * pi / 180
        
        # Center as complex
        self.center = self.center_x + 1j * self.center_y
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Translate input coordinates along a spiral path.
        """
        # Current angle
        angle = self.start_rad + t * self.sweep_rad * self.cycles
        
        # Interpolate radius
        radius = self.inner_radius + t * (self.outer_radius - self.inner_radius)
        
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


# Convenience function for standalone testing
def _test():
    """Quick visual test of the module."""
    import configparser
    
    config = configparser.ConfigParser()
    config.read_string("""
[arc]
radius = 100.0
start_angle = 0.0
sweep_angle = 180.0
center_x = 0.0
center_y = 0.0
cycles = 1.0
""")
    
    module = ArcModule(config, 'arc')
    print(module)
    print(f"Natural period: {module.natural_period}")
    
    # Test with a point at origin
    test_point = 0 + 0j
    print(f"\nTranslating point {test_point} along arc:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        z = module.transform(test_point, t)
        print(f"  t={t:.2f}: ({z.real:8.2f}, {z.imag:8.2f})")


if __name__ == "__main__":
    _test()
