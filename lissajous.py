#!/usr/bin/env python3
"""
Lissajous Module
================
Draws Lissajous curves: x = A*sin(a*t + δ), y = B*sin(b*t)

These are the patterns seen on oscilloscopes when two 
sine waves are combined. Related to spirograph patterns.

Famous examples:
- a=1, b=2: figure-8
- a=3, b=2: pretzel
- a=5, b=4: complex knot
"""

import numpy as np
from fractions import Fraction
from math import pi, gcd
from main import TransformModule


class LissajousModule(TransformModule):
    """
    Lissajous curve generator.
    
    Configuration:
        freq_x, freq_y: Frequency ratio (integers)
        amplitude_x, amplitude_y: Amplitudes
        phase: Phase difference in degrees
        cycles: Number of complete cycles (0 = auto)
        start_x, start_y: Center position
    """
    
    def _load_config(self):
        """Load Lissajous configuration."""
        self.freq_x = self._getint('freq_x', 3)
        self.freq_y = self._getint('freq_y', 2)
        self.amplitude_x = self._getfloat('amplitude_x', 50.0)
        self.amplitude_y = self._getfloat('amplitude_y', 50.0)
        self.end_amplitude_x = self._getfloat('end_amplitude_x', self.amplitude_x)
        self.end_amplitude_y = self._getfloat('end_amplitude_y', self.amplitude_y)
        self.phase_deg = self._getfloat('phase', 90.0)
        self.cycles = self._getfloat('cycles', 0)
        
        self.phase_rad = self.phase_deg * pi / 180
        
        # Calculate closure cycles (for one complete Lissajous)
        g = gcd(self.freq_x, self.freq_y)
        self._closure_cycles = self.freq_y // g
        
        # If cycles not specified, default to one complete figure
        if self.cycles <= 0:
            self.cycles = 1.0
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on Lissajous curve at time t.
        
        With cycles > 1, draws the figure multiple times.
        Combined with transforms, creates moiré effects.
        """
        # Normalize t to [0,1] for global interpolation
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Interpolate amplitudes based on overall progress
        ax = self.amplitude_x + t_norm * (self.end_amplitude_x - self.amplitude_x)
        ay = self.amplitude_y + t_norm * (self.end_amplitude_y - self.amplitude_y)
        
        # Parameter for this single Lissajous trace
        theta = t_frac * self._closure_cycles * 2 * pi
        
        # Lissajous equations
        x = ax * np.sin(self.freq_x * theta + self.phase_rad)
        y = ay * np.sin(self.freq_y * theta)
        
        point = x + 1j * y
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return f"LissajousModule({self.freq_x}:{self.freq_y}, A=({self.amplitude_x}, {self.amplitude_y}))"
