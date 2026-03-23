#!/usr/bin/env python3
"""
Noise Module
============
Adds controlled randomness to patterns — transforms precise mathematical
curves into organic, hand-drawn looking art.

Uses seeded value noise with interpolation for smooth perturbations.
No external dependencies beyond numpy.

Modes:
    radial: Perturb distance from origin (bumpy edges)
    xy:     Independent x/y jitter (shaky hand effect)
"""

import numpy as np
from fractions import Fraction
from main import TransformModule


def _value_noise_1d(t: float, frequency: float, seed: int) -> float:
    """
    Simple 1D value noise: hash-based random values at integer grid points,
    smoothly interpolated between them.

    Args:
        t: Input coordinate
        frequency: How many noise bumps per unit t
        seed: Random seed for reproducibility

    Returns:
        Noise value in [-1, 1]
    """
    t_scaled = t * frequency
    i = int(np.floor(t_scaled))
    frac = t_scaled - i

    # Smoothstep interpolation
    frac = frac * frac * (3 - 2 * frac)

    # Hash function for deterministic pseudo-random values at grid points
    def _hash(n):
        # Simple integer hash
        n = ((n + seed) * 374761393) & 0xFFFFFFFF
        n = ((n ^ (n >> 16)) * 668265263) & 0xFFFFFFFF
        n = (n ^ (n >> 16)) & 0xFFFFFFFF
        return (n / 0xFFFFFFFF) * 2 - 1  # Map to [-1, 1]

    v0 = _hash(i)
    v1 = _hash(i + 1)

    return v0 + (v1 - v0) * frac


class NoiseModule(TransformModule):
    """
    Noise perturbation: adds smooth random displacement to points.

    Configuration:
        amplitude: Maximum displacement magnitude (default 5.0)
        frequency: Noise frequency — bumps per full drawing (default 50)
        seed: Random seed for reproducibility (default 42)
        mode: 'radial' (distance from origin) or 'xy' (independent x/y)
        normalize: If true, normalize t to [0,1] using pipeline period
    """

    def _load_config(self):
        self.amplitude = self._getfloat('amplitude', 5.0)
        self.end_amplitude = self._getfloat('end_amplitude', self.amplitude)
        self.frequency = self._getfloat('frequency', 50.0)
        self.seed = self._getint('seed', 42)
        self.mode = self._get('mode', 'radial')
        self.normalize = self._getboolean('normalize', True)

    def transform(self, z: complex, t: float) -> complex:
        t_use = self._normalize_t(t)
        amp = self._interpolate(self.amplitude, self.end_amplitude, t_use, 'amplitude')

        if self.mode == 'xy':
            # Independent x/y displacement
            dx = _value_noise_1d(t_use, self.frequency, self.seed) * amp
            dy = _value_noise_1d(t_use, self.frequency, self.seed + 7919) * amp
            return z + complex(dx, dy)
        else:
            # Radial: perturb distance from origin
            noise_val = _value_noise_1d(t_use, self.frequency, self.seed) * amp
            if abs(z) > 1e-10:
                direction = z / abs(z)
            else:
                direction = 1 + 0j
            return z + direction * noise_val

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    def __repr__(self):
        return f"NoiseModule(amp={self.amplitude}, freq={self.frequency}, mode={self.mode})"
