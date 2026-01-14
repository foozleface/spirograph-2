#!/usr/bin/env python3
"""
Harmonograph Module
===================
Simulates a harmonograph - a mechanical drawing machine using pendulums.

A harmonograph typically has 2-4 pendulums that swing in different directions
with different frequencies, phases, and decay rates. The combination creates
beautiful, complex patterns.

The classic setup uses:
- Two pendulums for X motion (lateral table)
- Two pendulums for Y motion (lateral pen or rotary table)

This module implements a configurable multi-pendulum harmonograph with
optional damping for realistic decay effects.
"""

import numpy as np
from fractions import Fraction
from math import pi, gcd
from functools import reduce
from main import TransformModule


class HarmonographModule(TransformModule):
    """
    Harmonograph pendulum simulator.
    
    Creates patterns by combining multiple sinusoidal oscillations with
    different frequencies, amplitudes, phases, and decay rates.
    
    Configuration:
        ; Pendulum 1 (X component)
        freq1 = 2.0              ; Frequency
        amp1 = 100.0             ; Amplitude
        phase1 = 0.0             ; Phase in degrees
        decay1 = 0.0             ; Decay rate (0 = no decay)
        
        ; Pendulum 2 (Y component)  
        freq2 = 3.0
        amp2 = 100.0
        phase2 = 90.0
        decay2 = 0.0
        
        ; Pendulum 3 (adds to X) - optional
        freq3 = 0.0              ; 0 = disabled
        amp3 = 0.0
        phase3 = 0.0
        decay3 = 0.0
        
        ; Pendulum 4 (adds to Y) - optional
        freq4 = 0.0
        amp4 = 0.0
        phase4 = 0.0
        decay4 = 0.0
        
        duration = 60.0          ; Total time in "seconds"
        
    Presets (set preset= to use):
        lateral: Classic two-pendulum lateral harmonograph
        rotary: Rotary table harmonograph
        complex: All four pendulums active
    """
    
    def _load_config(self):
        """Load harmonograph configuration."""
        # Check for preset
        preset = self._get('preset', '')
        
        if preset == 'lateral':
            self._apply_lateral_preset()
        elif preset == 'rotary':
            self._apply_rotary_preset()
        elif preset == 'complex':
            self._apply_complex_preset()
        else:
            self._load_custom_config()
        
        self.duration = self._getfloat('duration', 60.0)
        self.cycles = self._getfloat('cycles', 1.0)  # How many times to draw the pattern
        
        # Compute frequencies for period calculation
        self.frequencies = [f for f in [self.freq1, self.freq2, self.freq3, self.freq4] if f > 0]
    
    def _load_custom_config(self):
        """Load custom pendulum parameters."""
        # Pendulum 1 (X)
        self.freq1 = self._getfloat('freq1', 2.0)
        self.amp1 = self._getfloat('amp1', 100.0)
        self.phase1 = self._getfloat('phase1', 0.0) * pi / 180
        self.decay1 = self._getfloat('decay1', 0.0)
        
        # Pendulum 2 (Y)
        self.freq2 = self._getfloat('freq2', 3.0)
        self.amp2 = self._getfloat('amp2', 100.0)
        self.phase2 = self._getfloat('phase2', 90.0) * pi / 180
        self.decay2 = self._getfloat('decay2', 0.0)
        
        # Pendulum 3 (X, optional)
        self.freq3 = self._getfloat('freq3', 0.0)
        self.amp3 = self._getfloat('amp3', 0.0)
        self.phase3 = self._getfloat('phase3', 0.0) * pi / 180
        self.decay3 = self._getfloat('decay3', 0.0)
        
        # Pendulum 4 (Y, optional)
        self.freq4 = self._getfloat('freq4', 0.0)
        self.amp4 = self._getfloat('amp4', 0.0)
        self.phase4 = self._getfloat('phase4', 0.0) * pi / 180
        self.decay4 = self._getfloat('decay4', 0.0)
    
    def _apply_lateral_preset(self):
        """Classic two-pendulum lateral harmonograph."""
        self.freq1 = self._getfloat('freq1', 2.0)
        self.amp1 = self._getfloat('amp1', 100.0)
        self.phase1 = self._getfloat('phase1', 0.0) * pi / 180
        self.decay1 = self._getfloat('decay1', 0.02)
        
        self.freq2 = self._getfloat('freq2', 3.0)
        self.amp2 = self._getfloat('amp2', 100.0)
        self.phase2 = self._getfloat('phase2', 90.0) * pi / 180
        self.decay2 = self._getfloat('decay2', 0.02)
        
        self.freq3 = 0.0
        self.amp3 = 0.0
        self.phase3 = 0.0
        self.decay3 = 0.0
        
        self.freq4 = 0.0
        self.amp4 = 0.0
        self.phase4 = 0.0
        self.decay4 = 0.0
    
    def _apply_rotary_preset(self):
        """Rotary table harmonograph with slight detuning."""
        base_freq = self._getfloat('base_freq', 2.0)
        detune = self._getfloat('detune', 0.01)
        
        self.freq1 = base_freq
        self.amp1 = self._getfloat('amp1', 100.0)
        self.phase1 = 0.0
        self.decay1 = self._getfloat('decay1', 0.01)
        
        self.freq2 = base_freq + detune
        self.amp2 = self._getfloat('amp2', 100.0)
        self.phase2 = pi / 2
        self.decay2 = self._getfloat('decay2', 0.01)
        
        self.freq3 = base_freq * 2
        self.amp3 = self._getfloat('amp3', 30.0)
        self.phase3 = pi / 4
        self.decay3 = self._getfloat('decay3', 0.02)
        
        self.freq4 = 0.0
        self.amp4 = 0.0
        self.phase4 = 0.0
        self.decay4 = 0.0
    
    def _apply_complex_preset(self):
        """Four-pendulum harmonograph."""
        self.freq1 = self._getfloat('freq1', 2.0)
        self.amp1 = self._getfloat('amp1', 80.0)
        self.phase1 = 0.0
        self.decay1 = self._getfloat('decay1', 0.01)
        
        self.freq2 = self._getfloat('freq2', 3.0)
        self.amp2 = self._getfloat('amp2', 80.0)
        self.phase2 = pi / 2
        self.decay2 = self._getfloat('decay2', 0.01)
        
        self.freq3 = self._getfloat('freq3', 2.01)
        self.amp3 = self._getfloat('amp3', 40.0)
        self.phase3 = pi / 3
        self.decay3 = self._getfloat('decay3', 0.015)
        
        self.freq4 = self._getfloat('freq4', 3.01)
        self.amp4 = self._getfloat('amp4', 40.0)
        self.phase4 = pi / 6
        self.decay4 = self._getfloat('decay4', 0.015)
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate harmonograph point at time t.
        
        With cycles > 1, the pattern repeats for moiré effects.
        """
        # Normalize t to [0, 1]
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        t_frac = t_in_cycles % 1.0
        
        # Convert to actual time for this pattern
        time = t_frac * self.duration
        
        # X component (pendulum 1 + pendulum 3)
        x = self.amp1 * np.sin(self.freq1 * 2 * pi * time + self.phase1)
        if self.decay1 > 0:
            x *= np.exp(-self.decay1 * time)
        
        if self.freq3 > 0:
            x3 = self.amp3 * np.sin(self.freq3 * 2 * pi * time + self.phase3)
            if self.decay3 > 0:
                x3 *= np.exp(-self.decay3 * time)
            x += x3
        
        # Y component (pendulum 2 + pendulum 4)
        y = self.amp2 * np.sin(self.freq2 * 2 * pi * time + self.phase2)
        if self.decay2 > 0:
            y *= np.exp(-self.decay2 * time)
        
        if self.freq4 > 0:
            y4 = self.amp4 * np.sin(self.freq4 * 2 * pi * time + self.phase4)
            if self.decay4 > 0:
                y4 *= np.exp(-self.decay4 * time)
            y += y4
        
        point = x + 1j * y
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        freqs = f"{self.freq1}:{self.freq2}"
        if self.freq3 > 0:
            freqs += f":{self.freq3}"
        if self.freq4 > 0:
            freqs += f":{self.freq4}"
        return f"HarmonographModule(freqs={freqs}, cycles={self.cycles})"
