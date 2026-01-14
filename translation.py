#!/usr/bin/env python3
"""
Translation Module
==================
Makes the pattern SLIDE along a straight line as it draws.

This is a SLIDING TRANSFORM - it adds a position offset that moves linearly
from start to end over time. The pattern itself is NOT warped.

Think of it like this:
- You're drawing a pattern
- As you draw, someone slowly moves the paper in a straight line underneath
- The pattern traces out along that linear path

Example: ellipse + translation = ellipse pattern stretched along a line
Result: ellipse shapes appear along the path from start to end

Common use: Combine with 'bend' to create curved versions of linear patterns.
    ellipse + translation + bend = ellipses arranged in an arc
"""

import numpy as np
from fractions import Fraction
from math import pi
from main import TransformModule


class TranslationModule(TransformModule):
    """
    Linear translation: moves input coordinates along a straight line.
    
    This is a TRANSFORMER module - it modifies input z based on time t.
    
    Single traversal from start to end. For oscillation or repetition,
    compound multiple translation modules with different parameters.
    
    Configuration:
        start_x, start_y: Starting translation offset
        end_x, end_y: Ending translation offset
        normalize: If true, normalize t to [0,1] regardless of pipeline period (default: true)
    """
    
    def _load_config(self):
        """Load translation configuration."""
        self.start_x = self._getfloat('start_x', 0.0)
        self.start_y = self._getfloat('start_y', 0.0)
        self.end_x = self._getfloat('end_x', 100.0)
        self.end_y = self._getfloat('end_y', 0.0)
        self.normalize = self._getboolean('normalize', True)
        
        # Start and end as complex numbers
        self.start = self.start_x + 1j * self.start_y
        self.end = self.end_x + 1j * self.end_y
        
        # Direction vector
        self.direction = self.end - self.start
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Translate input coordinates along the line.
        
        Args:
            z: Input position to transform
            t: Time parameter in [0, 1] or [0, period]
            
        Returns:
            Translated position
        """
        # Normalize t to [0,1] if requested, using pipeline period
        if self.normalize:
            period = float(self._pipeline_period)
            t_use = t / period if period > 0 else t
        else:
            t_use = t
        
        # Linear interpolation from start to end
        offset = self.start + t_use * self.direction
        
        return z + offset
    
    @property
    def natural_period(self) -> Fraction:
        """Single traversal = period of 1."""
        return Fraction(1, 1)
    
    @property
    def is_generator(self) -> bool:
        return False
    
    def __repr__(self):
        return (f"TranslationModule("
                f"({self.start_x}, {self.start_y}) -> ({self.end_x}, {self.end_y}))")


# Convenience function for standalone testing
def _test():
    """Quick visual test of the module."""
    import configparser
    
    config = configparser.ConfigParser()
    config.read_string("""
[translation]
start_x = 0.0
start_y = 0.0
end_x = 100.0
end_y = 50.0
""")
    
    module = TranslationModule(config, 'translation')
    print(module)
    print(f"Natural period: {module.natural_period}")
    
    # Test with a point at origin
    test_point = 0 + 0j
    print(f"\nTranslating point {test_point} along line:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        z = module.transform(test_point, t)
        print(f"  t={t:.2f}: ({z.real:8.2f}, {z.imag:8.2f})")


if __name__ == "__main__":
    _test()
