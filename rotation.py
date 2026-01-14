#!/usr/bin/env python3
"""
Rotation Module
===============
Rotates the entire drawing surface during the animation.

This is a TRANSFORMER module - it takes input coordinates and rotates them
around a specified center point based on the time parameter.

This simulates slowly spinning the paper (or the entire spirograph apparatus)
while drawing, creating spiral or rosette-like patterns from simpler curves.

The rotation is applied as:
    z' = center + (z - center) * e^(iθ(t))
    
Where θ(t) increases linearly from 0 to total_rotation as t goes from 0 to 1.
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class RotationModule(TransformModule):
    """
    Surface rotation: rotates input coordinates around a center point.
    
    This is a TRANSFORMER module - it modifies input z based on time t.
    
    Configuration:
        total_degrees: Total rotation over the full drawing in degrees
        origin_x, origin_y: Center of rotation (default 0,0)
        normalize: If true (default), normalize t to [0,1] regardless of pipeline period
    """
    
    def _load_config(self):
        """Load rotation configuration."""
        self.total_degrees = self._getfloat('total_degrees', 360.0)
        self.origin_x = self._getfloat('origin_x', 0.0)
        self.origin_y = self._getfloat('origin_y', 0.0)
        self.normalize = self._getboolean('normalize', True)
        
        # Convert to radians
        self.total_radians = self.total_degrees * pi / 180
        
        # Rotation center as complex number
        self.origin = self.origin_x + 1j * self.origin_y
        
        # Determine the period based on rotation amount
        self._compute_period()
    
    def _compute_period(self):
        """Compute the natural period based on rotation."""
        # Express total rotation as a fraction of full circles
        full_circles = abs(self.total_degrees) / 360.0
        
        if full_circles == 0:
            self._period = Fraction(1, 1)
        else:
            self._period = Fraction(full_circles).limit_denominator(1000)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Rotate input coordinates around the origin point.
        
        Args:
            z: Input position to transform
            t: Time parameter in [0, 1] or [0, period]
            
        Returns:
            Rotated position
        """
        # Normalize t to [0,1] if requested
        if self.normalize:
            period = float(self._pipeline_period)
            t_use = t / period if period > 0 else t
        else:
            t_use = t
        
        # Current rotation angle
        theta = t_use * self.total_radians
        
        # Rotation factor
        rotation = np.exp(1j * theta)
        
        # Rotate around origin: z' = origin + (z - origin) * rotation
        relative = z - self.origin
        rotated = relative * rotation
        result = self.origin + rotated
        
        return result
    
    @property
    def natural_period(self) -> Fraction:
        """Period of the rotation."""
        return self._period
    
    @property
    def is_generator(self) -> bool:
        """This module transforms coordinates, not generates."""
        return False
    
    def __repr__(self):
        if self.origin_x == 0 and self.origin_y == 0:
            return f"RotationModule({self.total_degrees}° around origin)"
        return f"RotationModule({self.total_degrees}° around ({self.origin_x}, {self.origin_y}))"


class OscillatingRotationModule(TransformModule):
    """
    Oscillating rotation: rotates back and forth instead of continuously.
    
    This creates a pendulum-like motion, useful for creating symmetric patterns.
    
    Configuration:
        amplitude_degrees: Maximum rotation angle in each direction
        oscillations: Number of complete back-and-forth cycles
        rotate_around_origin: If true, rotate around (0,0)
        center_x, center_y: Center of rotation (if not origin)
        normalize: If true (default), normalize t to [0,1] regardless of pipeline period
    """
    
    def _load_config(self):
        """Load oscillation configuration."""
        self.amplitude_degrees = self._getfloat('amplitude_degrees', 45.0)
        self.oscillations = self._getfloat('oscillations', 1.0)
        self.rotate_around_origin = self._getboolean('rotate_around_origin', True)
        self.center_x = self._getfloat('center_x', 0.0)
        self.center_y = self._getfloat('center_y', 0.0)
        self.normalize = self._getboolean('normalize', True)
        
        # Convert to radians
        self.amplitude_radians = self.amplitude_degrees * pi / 180
        
        # Rotation center
        if self.rotate_around_origin:
            self.center = 0 + 0j
        else:
            self.center = self.center_x + 1j * self.center_y
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Apply oscillating rotation to input coordinates.
        
        Uses a sinusoidal rotation angle.
        
        Args:
            z: Input position to transform
            t: Time parameter in [0, 1] or [0, period]
            
        Returns:
            Rotated position
        """
        # Normalize t to [0,1] if requested
        if self.normalize:
            period = float(self._pipeline_period)
            t_use = t / period if period > 0 else t
        else:
            t_use = t
        
        # Oscillating angle using sine wave
        theta = self.amplitude_radians * np.sin(2 * pi * self.oscillations * t_use)
        
        # Rotation factor
        rotation = np.exp(1j * theta)
        
        # Rotate around center
        relative = z - self.center
        rotated = relative * rotation
        result = self.center + rotated
        
        return result
    
    @property
    def natural_period(self) -> Fraction:
        """Period matches the oscillation count."""
        return Fraction(self.oscillations).limit_denominator(1000)
    
    @property
    def is_generator(self) -> bool:
        """This module transforms coordinates."""
        return False
    
    def __repr__(self):
        return f"OscillatingRotationModule(±{self.amplitude_degrees}°, {self.oscillations} cycles)"


# Convenience function for standalone testing
def _test():
    """Quick visual test of the module."""
    import configparser
    
    config = configparser.ConfigParser()
    config.read_string("""
[rotation]
total_degrees = 360.0
center_x = 0.0
center_y = 0.0
rotate_around_origin = true
""")
    
    module = RotationModule(config, 'rotation')
    print(module)
    print(f"Natural period: {module.natural_period}")
    
    # Test with a point at (1, 0)
    test_point = 1 + 0j
    print(f"\nRotating point {test_point}:")
    for t in [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]:
        z = module.transform(test_point, t)
        angle = np.angle(z) * 180 / pi
        print(f"  t={t:.3f}: ({z.real:8.5f}, {z.imag:8.5f}) angle={angle:7.2f}°")


if __name__ == "__main__":
    _test()
