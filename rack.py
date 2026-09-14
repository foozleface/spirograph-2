#!/usr/bin/env python3
"""
Rack Module
===========
Simulates a gear rolling around a Spirograph rack - a straight bar with 
rounded (semicircular) toothed ends.

Physical model:
    - The rack is a "stadium" shape: two straight sides + two semicircular ends
    - ALL edges have teeth at the same pitch
    - A gear wheel rolls AROUND the outside of this shape
    
On straight sections: TROCHOID (curtate cycloid)
    x = s - d*sin(s/r)
    y = r - d*cos(s/r)
    where s = distance traveled, r = gear radius, d = pen distance

On curved ends: EPITROCHOID (rolling outside a circle)
    The gear orbits the semicircular end while rotating
    Pen traces cusps based on ratio (R_end + r_gear) / r_gear
"""

import numpy as np
from fractions import Fraction
from math import pi, gcd
from main import TransformModule


class RackModule(TransformModule):
    """
    Rack: gear rolling around a stadium-shaped rack with toothed ends.
    
    Configuration:
        straight_teeth: Teeth along one straight edge
        end_teeth: Teeth around one semicircular end
        gear_teeth: Number of teeth on the rolling gear
        tooth_pitch: Distance per tooth (same for all edges)
        hole_position: Pen hole as fraction of gear radius (0=center, 1=edge)
        laps: Number of complete circuits around the rack
        scale: Output scale factor
    """
    
    def _load_config(self):
        """Load rack configuration."""
        self.straight_teeth = self._getint('straight_teeth', 50)
        self.end_teeth = self._getint('end_teeth', 24)
        self.gear_teeth = self._getint('gear_teeth', 24)
        self.tooth_pitch = self._getfloat('tooth_pitch', 2.0)
        self.hole_position = self._getfloat('hole_position', 0.75)
        self.end_hole_position = self._getfloat('end_hole_position', self.hole_position)
        self.laps = self._getint('laps', 1)
        self.cycles = self._getfloat('cycles', 1.0)  # How many times to draw the pattern
        self.scale = self._getfloat('scale', 1.0)
        self._drifts = (self.end_hole_position != self.hole_position)
        
        # Straight section length
        self.straight_length = self.straight_teeth * self.tooth_pitch
        
        # End semicircle: arc_length = end_teeth * tooth_pitch = π * radius
        # So: radius = (end_teeth * tooth_pitch) / π
        self.end_arc_length = self.end_teeth * self.tooth_pitch
        self.end_radius = self.end_arc_length / pi
        
        # Gear geometry
        self.gear_circumference = self.gear_teeth * self.tooth_pitch
        self.gear_radius = self.gear_circumference / (2 * pi)
        self.pen_distance = self.hole_position * self.gear_radius
        
        # Total perimeter = 2 * straight + 2 * semicircle
        self.total_perimeter = 2 * self.straight_length + 2 * self.end_arc_length
        
        # Epitrochoid speed ratio for ends
        # (R + r) / r where R = end_radius, r = gear_radius
        self.speed_ratio = (self.end_radius + self.gear_radius) / self.gear_radius
    
    def transform(self, z: complex, t: float) -> complex:
        """
        Compute position at time t as gear rolls around rack perimeter.
        
        With cycles > 1, the pattern repeats for moiré effects.
        """
        # Normalize t to [0, 1]
        period = float(self._pipeline_period)
        t_norm = t / period if period > 0 else t
        
        # Convert to position within cycles
        t_in_cycles = t_norm * self.cycles
        
        # Position within current cycle [0, 1)
        t_frac = t_in_cycles % 1.0
        
        # Total progress through all laps within this cycle. A point landing
        # exactly on a lap boundary belongs to the end of the previous lap.
        total_progress = t_frac * self.laps
        lap_num = np.floor(total_progress)
        lap_frac = total_progress - lap_num
        on_boundary = (total_progress > 0) & (lap_frac == 0)
        lap_frac = np.where(on_boundary, 1.0, lap_frac)
        lap_num = np.where(on_boundary, lap_num - 1, lap_num)
        
        # Interpolate pen distance for drift
        if self._drifts:
            hole = self._interpolate(self.hole_position, self.end_hole_position, t_norm, 'hole_position')
            pen_d = hole * self.gear_radius
        else:
            pen_d = self.pen_distance

        # Distance along perimeter for this lap
        s = lap_frac * self.total_perimeter
        
        # Segment boundaries
        seg1 = self.straight_length  # Bottom straight ends
        seg2 = seg1 + self.end_arc_length  # Right semicircle ends
        seg3 = seg2 + self.straight_length  # Top straight ends
        # seg4 (left semicircle) ends at total_perimeter
        
        # Gear rotation accumulated from previous laps
        base_rotation = lap_num * (self.total_perimeter / self.gear_radius)
        
        # Compute rotation accumulated through previous segments in THIS lap
        rotation_seg1 = self.straight_length / self.gear_radius
        rotation_seg2 = self.speed_ratio * pi  # Epitrochoid rotation for full semicircle
        rotation_seg3 = self.straight_length / self.gear_radius
        
        orbit_r = self.end_radius + self.gear_radius
        half = self.straight_length / 2

        # SEGMENT 1: bottom straight, left to right. A trochoid: the gear
        # centre runs along y = -(end_radius + gear_radius).
        d1 = s
        rot1 = base_rotation + d1 / self.gear_radius
        c1x = -half + d1
        c1y = -orbit_r

        # SEGMENT 2: right semicircle, an epitrochoid. The rack surface is
        # what has teeth, so the orbital angle is the surface distance over
        # the end radius; the gear turns speed_ratio times as fast.
        phi2 = (s - seg1) / self.end_radius
        ang2 = -pi / 2 + phi2
        c2x = half + orbit_r * np.cos(ang2)
        c2y = orbit_r * np.sin(ang2)
        rot2 = base_rotation + rotation_seg1 + self.speed_ratio * phi2

        # SEGMENT 3: top straight, right to left.
        d3 = s - seg2
        rot3 = base_rotation + rotation_seg1 + rotation_seg2 + d3 / self.gear_radius
        c3x = half - d3
        c3y = orbit_r

        # SEGMENT 4: left semicircle.
        phi4 = s - seg3
        phi4 = phi4 / self.end_radius
        ang4 = pi / 2 + phi4
        c4x = -half + orbit_r * np.cos(ang4)
        c4y = orbit_r * np.sin(ang4)
        rot4 = (base_rotation + rotation_seg1 + rotation_seg2 + rotation_seg3
                + self.speed_ratio * phi4)

        which = [s <= seg1, s <= seg2, s <= seg3]
        cx = np.select(which, [c1x, c2x, c3x], c4x)
        cy = np.select(which, [c1y, c2y, c3y], c4y)
        gear_rot = np.select(which, [rot1, rot2, rot3], rot4)

        # Pen position (trochoid: the pen points down at the start)
        px = cx + pen_d * np.sin(gear_rot)
        py = cy - pen_d * np.cos(gear_rot)

        result = (px + 1j * py) * self.scale
        return z + result
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return (f"RackModule(straight={self.straight_teeth}T, ends={self.end_teeth}T, "
                f"gear={self.gear_teeth}T, laps={self.laps}, cycles={self.cycles})")
