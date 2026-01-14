#!/usr/bin/env python3
"""
Spirograph Gear Module
======================
Simulates a classic two-gear spirograph where one gear rolls inside or outside
another stationary gear.

Hypotrochoid (inside):  z = (R-r)e^(it) + d·e^(-i(R-r)t/r)
Epitrochoid (outside):  z = (R+r)e^(it) + d·e^(i(R+r)t/r)

Where:
    R = radius of fixed gear = fixed_teeth * tooth_pitch / (2π)
    r = radius of rolling gear = rolling_teeth * tooth_pitch / (2π)
    d = distance from rolling gear center to pen hole
    t = rotation angle of the rolling gear's center around the fixed gear

More teeth = larger gear diameter (physically realistic).

Key parameters:
    rotations: How many times around the fixed gear to complete the pattern
               (0 = auto-calculate for closure)
    cycles: How many times to draw the complete pattern (for moiré effects)
            With cycles > 1 and transforms, creates overlapping patterns
"""

import numpy as np
from fractions import Fraction
from math import gcd, pi
from main import TransformModule


class SpirographGearModule(TransformModule):
    """
    Two-gear spirograph: one gear rolling inside or outside another.
    
    This is a TRANSFORMER module - adds spirograph pattern to input z.
    
    Gear size scales with tooth count: circumference = teeth × tooth_pitch
    
    Configuration:
        fixed_teeth: Number of teeth on the stationary gear
        rolling_teeth: Number of teeth on the rolling gear
        tooth_pitch: Distance per tooth (determines actual size)
        hole_position: Position of pen hole (0=center, 1=edge of rolling gear)
        rotations: Number of rotations (0 = auto-calculate for closure)
        inside: True for hypotrochoid, False for epitrochoid
        cycles: Number of times to draw the complete pattern (default: 1)
    """
    
    def _load_config(self):
        """Load gear configuration."""
        self.fixed_teeth = self._getint('fixed_teeth', 96)
        self.rolling_teeth = self._getint('rolling_teeth', 36)
        self.tooth_pitch = self._getfloat('tooth_pitch', 1.0)
        self.hole_position = self._getfloat('hole_position', 0.7)
        self.rotations = self._getint('rotations', 0)
        self.inside = self._getboolean('inside', True)
        self.cycles = self._getfloat('cycles', 1.0)
        
        # Compute actual radii from teeth and pitch
        # circumference = teeth × pitch, radius = circumference / 2π
        self.R = self.fixed_teeth * self.tooth_pitch / (2 * pi)
        self.r = self.rolling_teeth * self.tooth_pitch / (2 * pi)
        self.d = self.hole_position * self.r  # Pen distance from rolling center
        
        # Calculate rotations needed for closure if not specified
        if self.rotations <= 0:
            g = gcd(self.fixed_teeth, self.rolling_teeth)
            self.rotations = self.rolling_teeth // g
        
        # Precompute the gear ratio for the equation
        if self.inside:
            # Hypotrochoid: gear rolls inside
            self.center_radius = self.R - self.r
            self.speed_ratio = (self.R - self.r) / self.r
            self.direction = -1  # Counter-rotating
        else:
            # Epitrochoid: gear rolls outside
            self.center_radius = self.R + self.r
            self.speed_ratio = (self.R + self.r) / self.r
            self.direction = 1  # Co-rotating
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate spirograph point at time t and add to input.
        
        With cycles > 1, the pattern repeats multiple times.
        Combined with transforms (rotation, arc), creates moiré effects.
        """
        # Normalize t to [0, 1] over entire drawing
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Convert to angle for this single pattern
        theta = t_frac * self.rotations * 2 * pi
        
        # Position of rolling gear center
        center = self.center_radius * np.exp(1j * theta)
        
        # Position of pen relative to rolling gear center
        pen_angle = self.direction * self.speed_ratio * theta
        pen_offset = self.d * np.exp(1j * pen_angle)
        
        # Total position
        result = center + pen_offset
        
        return z + result
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        mode = "hypotrochoid" if self.inside else "epitrochoid"
        return (f"SpirographGearModule({mode}, "
                f"fixed={self.fixed_teeth}T, rolling={self.rolling_teeth}T, "
                f"cycles={self.cycles})")


# Convenience function for standalone testing
def _test():
    """Quick visual test of the module."""
    import configparser
    
    config = configparser.ConfigParser()
    config.read_string("""
[spirograph_gear]
fixed_teeth = 96
rolling_teeth = 36
tooth_pitch = 2.0
hole_position = 0.7
rotations = 0
inside = true
cycles = 1
""")
    
    module = SpirographGearModule(config, 'spirograph_gear')
    print(module)
    print(f"Natural period: {module.natural_period}")
    print(f"Rotations for closure: {module.rotations}")
    
    # Test a few points
    from fractions import Fraction
    module.set_pipeline_period(Fraction(1, 1))
    
    print(f"\nPoints along pattern:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        pt = module.transform(0j, t)
        print(f"  t={t:.2f}: ({pt.real:.2f}, {pt.imag:.2f})")


if __name__ == "__main__":
    _test()
