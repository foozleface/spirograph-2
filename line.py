#!/usr/bin/env python3
"""
Line Module
===========
Generates straight lines with configurable timing and length animation.

This is a GENERATOR module - it creates coordinates from scratch based on t.

Key features:
- cycles: Draw the line multiple times (pen returns to start each cycle)
- stroke_time: Fraction of each cycle spent drawing (rest is idle at start)
- end_length: Animate line length from short to long over the drawing

With stroke_time < 1.0, lines appear as discrete segments rather than 
continuous paths - useful with rotation for fan/starburst effects, or 
with bend to create straight-line approximations of arcs.

Examples:
    line (cycles=1) = single line
    line (cycles=12) + rotation (360°) = 12-ray starburst (with curved connectors)
    line (cycles=12, stroke_time=0.1) + rotation (360°) = 12 discrete rays
    line (cycles=8, stroke_time=0.05) + bend (90°) = straight-line arc approximation
    line (length=50, end_length=200) + rotation = growing fan
"""

import numpy as np
from fractions import Fraction
from main import TransformModule


class LineModule(TransformModule):
    """
    Line generator with timing control and length animation.
    
    Configuration:
        length: Starting line length (shorthand for end_x when start is origin)
        end_length: Ending line length (for grow/shrink animation)
        start_x, start_y: Line start point (default: 0, 0)
        end_x, end_y: Line end point (default: length, 0) - sets direction
        cycles: Number of times to draw the line (default: 1)
        stroke_time: Fraction of each cycle spent drawing (default: 1.0)
                     1.0 = continuous drawing
                     0.1 = draw quickly in 10% of cycle, idle 90%
                     0.01 = nearly instantaneous lines
        idle_at: Where to stay during idle time: 'start' or 'end' (default: start)
    """
    
    def _load_config(self):
        """Load line configuration."""
        # Length parameters
        self.length = self._getfloat('length', 100.0)
        self.end_length = self._getfloat('end_length', self.length)
        
        # Position parameters
        self.start_x = self._getfloat('start_x', 0.0)
        self.start_y = self._getfloat('start_y', 0.0)
        self.end_x = self._getfloat('end_x', self.length)
        self.end_y = self._getfloat('end_y', 0.0)
        
        # Timing parameters
        self.cycles = self._getfloat('cycles', 1.0)
        self.stroke_time = self._getfloat('stroke_time', 1.0)
        self.stroke_time = max(0.001, min(1.0, self.stroke_time))  # Clamp to [0.001, 1.0]
        
        idle_at_str = self._get('idle_at', 'start').lower()
        self.idle_at_end = (idle_at_str == 'end')
        
        # Compute direction vector (unit vector)
        self.start = self.start_x + 1j * self.start_y
        end = self.end_x + 1j * self.end_y
        direction = end - self.start
        self.dir_length = abs(direction)
        if self.dir_length > 0:
            self.unit_dir = direction / self.dir_length
        else:
            self.unit_dir = 1 + 0j  # Default to +X direction
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Generate point on line at time t.
        
        With cycles > 1, the line repeats.
        With stroke_time < 1, each line is drawn quickly with idle time.
        """
        # Normalize t to [0, cycles] range
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t  # [0, 1] over entire drawing
        t_in_cycles = t_norm * self.cycles  # [0, cycles]
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Interpolate line length based on overall progress
        current_length = self.length + t_norm * (self.end_length - self.length)
        
        # Calculate draw progress based on stroke_time
        if self.stroke_time >= 1.0:
            # Continuous drawing - simple linear progress
            draw_progress = t_frac
        else:
            # Discrete drawing with idle time
            idle_time = 1.0 - self.stroke_time
            
            if self.idle_at_end:
                # Draw first, then idle at end
                if t_frac < self.stroke_time:
                    # Drawing phase
                    draw_progress = t_frac / self.stroke_time
                else:
                    # Idle at end
                    draw_progress = 1.0
            else:
                # Idle first, then draw (default)
                if t_frac < idle_time:
                    # Idle at start
                    draw_progress = 0.0
                else:
                    # Drawing phase - map remaining time to [0, 1]
                    draw_progress = (t_frac - idle_time) / self.stroke_time
        
        # Compute position along line
        direction = self.unit_dir * current_length
        point = self.start + draw_progress * direction
        
        return z + point
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return (f"LineModule(length={self.length}→{self.end_length}, "
                f"cycles={self.cycles}, stroke_time={self.stroke_time})")
