#!/usr/bin/env python3
"""
Spirograph Rail Module
======================
Simulates a spirograph gear rolling along a linear rack (the horizontal
"rail" base that comes with some spirograph sets).

The gear rolls along the rack while a pen traces from a hole in the gear.
This produces a trochoid curve translated along the rail direction.

Parametric equations:
    x = rail_position(t) + d·cos(gear_angle(t))
    y = r + d·sin(gear_angle(t))
    
Where:
    r = radius of the gear
    d = distance from gear center to pen hole
    rail_position = how far along the rail the gear has traveled
    gear_angle = rotation angle of the gear (depends on distance traveled)
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class SpirographRailModule(TransformModule):
    """
    Linear rail spirograph: gear rolling along a straight rack.
    
    This is a GENERATOR module - it ignores input z and produces coordinates
    purely from the time parameter t.
    
    The gear rolls without slipping, so the rotation angle is determined by
    the distance traveled along the rail.
    
    Configuration:
        rail_length: Total length of the rail
        gear_teeth: Number of teeth on the gear
        tooth_pitch: Distance per tooth (determines gear circumference)
        hole_position: Position of pen hole (0=center, 1=edge)
        passes: Number of complete passes along the rail
        scale: Output scale factor
        rail_angle: Orientation of rail in degrees (0=horizontal)
    """
    
    def _load_config(self):
        """Load rail configuration."""
        self.rail_length = self._getfloat('rail_length', 200.0)
        self.gear_teeth = self._getint('gear_teeth', 40)
        self.tooth_pitch = self._getfloat('tooth_pitch', 1.0)
        self.hole_position = self._getfloat('hole_position', 0.6)
        self.passes = self._getint('passes', 2)
        self.cycles = self._getfloat('cycles', 1.0)  # How many times to draw the pattern
        self.scale = self._getfloat('scale', 1.0)
        self.rail_angle = self._getfloat('rail_angle', 0.0)
        
        # Compute derived values
        # Gear circumference = teeth * pitch
        self.gear_circumference = self.gear_teeth * self.tooth_pitch
        self.gear_radius = self.gear_circumference / (2 * pi)
        self.pen_distance = self.hole_position * self.gear_radius
        
        # Convert rail angle to radians
        self.rail_angle_rad = self.rail_angle * pi / 180
        
        # Unit vector along the rail
        self.rail_direction = np.exp(1j * self.rail_angle_rad)
        
        # Perpendicular direction (gear center is offset from rail)
        self.perp_direction = np.exp(1j * (self.rail_angle_rad + pi/2))
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate rail spirograph point at time t and add to input.
        
        The motion is back-and-forth: each pass alternates direction.
        With cycles > 1, the pattern repeats for moiré effects.
        """
        # Normalize t to [0, 1]
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Total distance to travel over all passes within this cycle
        total_distance = self.rail_length * self.passes
        
        # Distance traveled at time t
        raw_distance = t_frac * total_distance
        
        # Compute position along rail (handles back-and-forth motion)
        # Each pass is one rail_length
        pass_number = int(raw_distance / self.rail_length)
        within_pass = raw_distance - pass_number * self.rail_length
        
        # Odd passes go backward
        if pass_number % 2 == 1:
            rail_position = self.rail_length - within_pass
            direction_sign = -1
        else:
            rail_position = within_pass
            direction_sign = 1
        
        # Center the rail around the origin
        centered_position = rail_position - self.rail_length / 2
        
        # Gear rotation angle (based on distance traveled, accounting for direction)
        # The gear rotates as it rolls without slipping
        # For every circumference traveled, the gear rotates 2π
        cumulative_distance = raw_distance  # Total distance, not position
        gear_angle = (cumulative_distance / self.gear_radius)
        
        # Position of gear center (on the rail, offset by gear radius)
        gear_center = (centered_position * self.rail_direction + 
                       self.gear_radius * self.perp_direction)
        
        # Position of pen relative to gear center
        pen_offset = self.pen_distance * np.exp(1j * gear_angle)
        
        # Rotate pen offset to align with rail orientation
        pen_offset = pen_offset * self.rail_direction
        
        # Total position - add to input
        result = gear_center + pen_offset
        
        return z + result * self.scale
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return (f"SpirographRailModule(rail={self.rail_length}, "
                f"gear_teeth={self.gear_teeth}, passes={self.passes}, cycles={self.cycles})")


class SpirographRailTransformModule(TransformModule):
    """
    Linear rail as a TRANSFORMER - adds rail motion to existing coordinates.
    
    This version takes input coordinates and translates them along the rail
    path, useful for chaining after another spirograph module.
    
    Configuration is the same as SpirographRailModule, but hole_position
    is ignored (the "pen" is the input coordinate).
    """
    
    def _load_config(self):
        """Load rail configuration."""
        self.rail_length = self._getfloat('rail_length', 200.0)
        self.gear_teeth = self._getint('gear_teeth', 40)
        self.tooth_pitch = self._getfloat('tooth_pitch', 1.0)
        self.passes = self._getint('passes', 2)
        self.cycles = self._getfloat('cycles', 1.0)
        self.scale = self._getfloat('scale', 1.0)
        self.rail_angle = self._getfloat('rail_angle', 0.0)
        
        # Compute derived values
        self.gear_circumference = self.gear_teeth * self.tooth_pitch
        self.gear_radius = self.gear_circumference / (2 * pi)
        
        self.rail_angle_rad = self.rail_angle * pi / 180
        self.rail_direction = np.exp(1j * self.rail_angle_rad)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Transform input coordinates by rail motion.
        
        With cycles > 1, the transform repeats for moiré effects.
        """
        # Normalize t to [0, 1]
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        t_frac = t_in_cycles % 1.0
        
        # Total distance over all passes
        total_distance = self.rail_length * self.passes
        raw_distance = t_frac * total_distance
        
        # Position along rail
        pass_number = int(raw_distance / self.rail_length)
        within_pass = raw_distance - pass_number * self.rail_length
        
        if pass_number % 2 == 1:
            rail_position = self.rail_length - within_pass
        else:
            rail_position = within_pass
        
        centered_position = rail_position - self.rail_length / 2
        
        # Translation vector
        translation = centered_position * self.rail_direction * self.scale
        
        return z + translation
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return f"SpirographRailTransformModule(rail={self.rail_length}, passes={self.passes}, cycles={self.cycles})"


# Convenience function for standalone testing
def _test():
    """Quick visual test of the module."""
    import configparser
    
    config = configparser.ConfigParser()
    config.read_string("""
[spirograph_rail]
rail_length = 200.0
gear_teeth = 40
tooth_pitch = 1.0
hole_position = 0.6
passes = 2
scale = 1.0
rail_angle = 0.0
""")
    
    module = SpirographRailModule(config, 'spirograph_rail')
    print(module)
    print(f"Gear radius: {module.gear_radius:.3f}")
    print(f"Pen distance: {module.pen_distance:.3f}")
    print(f"Natural period: {module.natural_period}")
    
    # Generate some test points
    for t in [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]:
        z = module.transform(0j, t)
        print(f"  t={t:.3f}: ({z.real:8.3f}, {z.imag:8.3f})")


if __name__ == "__main__":
    _test()
