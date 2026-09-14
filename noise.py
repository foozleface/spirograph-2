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


def _hash(n, seed):
    """Deterministic pseudo-random value in [-1, 1] at integer grid point n.
    Array-safe: the arithmetic stays inside 64 bits at every step."""
    n = np.asarray(n, dtype=np.int64)
    n = ((n + seed) * 374761393) & 0xFFFFFFFF
    n = ((n ^ (n >> 16)) * 668265263) & 0xFFFFFFFF
    n = (n ^ (n >> 16)) & 0xFFFFFFFF
    return (n / 0xFFFFFFFF) * 2 - 1


def _value_noise_1d(t, frequency: float, seed: int):
    """
    Simple 1D value noise: hash-based random values at integer grid points,
    smoothly interpolated between them. Array-safe.

    Args:
        t: Input coordinate(s)
        frequency: How many noise bumps per unit t
        seed: Random seed for reproducibility

    Returns:
        Noise value(s) in [-1, 1]
    """
    t_scaled = np.asarray(t, dtype=float) * frequency
    i = np.floor(t_scaled).astype(np.int64)
    frac = t_scaled - i

    # Smoothstep interpolation
    frac = frac * frac * (3 - 2 * frac)

    v0 = _hash(i, seed)
    v1 = _hash(i + 1, seed)

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
            return z + (dx + 1j * dy)
        else:
            # Radial: perturb distance from origin
            noise_val = _value_noise_1d(t_use, self.frequency, self.seed) * amp
            magnitude = np.abs(z)
            safe = np.where(magnitude > 1e-10, magnitude, 1.0)
            direction = np.where(magnitude > 1e-10, z / safe, 1 + 0j)
            return z + direction * noise_val

    @property
    def natural_period(self) -> Fraction:
        return Fraction(1, 1)

    def __repr__(self):
        return f"NoiseModule(amp={self.amplitude}, freq={self.frequency}, mode={self.mode})"
