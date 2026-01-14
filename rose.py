#!/usr/bin/env python3
"""
Rose Curve Module (Rhodonea)
============================
Draws mathematical rose curves: r = cos(k*θ)

These create flower-like patterns with petals determined by k:
- k integer: k petals if k is odd, 2k petals if k is even
- k = p/q (fraction): (p+q) petals if both odd, 2(p+q) if one even

Famous examples:
- k=2: quadrifolium (4 petals)
- k=3: trifolium (3 petals)  
- k=5: cinquefoil (5 petals)
"""

import numpy as np
from fractions import Fraction
from math import pi, gcd
from main import TransformModule


class RoseModule(TransformModule):
    """
    Rose curve (rhodonea) generator: r = a * cos(k*θ)
    
    Configuration:
        k_num, k_den: k = k_num/k_den (petal ratio)
        radius: Maximum radius
        end_radius: Ending radius for grow/shrink
        cycles: How many times to trace (auto-calculated if 0)
        start_x, start_y: Center position
    """
    
    def _load_config(self):
        """Load rose configuration."""
        self.k_num = self._getint('k_num', 3)
        self.k_den = self._getint('k_den', 1)
        self.k = self.k_num / self.k_den
        self.radius = self._getfloat('radius', 50.0)
        self.end_radius = self._getfloat('end_radius', self.radius)
        self.cycles = self._getfloat('cycles', 0)
        
        # Calculate closure cycles (how many times around to complete the rose)
        if self.k_den == 1:
            # Integer k
            self._closure_cycles = 1 if self.k_num % 2 == 1 else 2
        else:
            # Fractional k = p/q
            g = gcd(self.k_num, self.k_den)
            p, q = self.k_num // g, self.k_den // g
            self._closure_cycles = q if (p * q) % 2 == 1 else 2 * q
        
        # If cycles not specified, default to one complete rose
        if self.cycles <= 0:
            self.cycles = 1.0
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on rose curve at time t.
        
        With cycles > closure_cycles, draws the rose multiple times.
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
        
        # Angle for this single rose trace
        theta = t_frac * self._closure_cycles * 2 * pi
        
        # Rose curve: r = a * cos(k*θ)
        r = current_radius * np.cos(self.k * theta)
        
        # Convert to Cartesian
        point = r * np.exp(1j * theta)
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        if self.k_den == 1:
            return f"RoseModule(k={self.k_num}, r={self.radius})"
        return f"RoseModule(k={self.k_num}/{self.k_den}, r={self.radius})"
