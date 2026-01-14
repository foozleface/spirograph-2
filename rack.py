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
        self.laps = self._getint('laps', 1)
        self.cycles = self._getfloat('cycles', 1.0)  # How many times to draw the pattern
        self.scale = self._getfloat('scale', 1.0)
        
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
        
        # Total progress through all laps within this cycle
        total_progress = t_frac * self.laps
        lap_num = int(total_progress)
        lap_frac = total_progress - lap_num
        if total_progress > 0 and lap_frac == 0:
            lap_frac = 1.0
            lap_num -= 1
        
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
        
        if s <= seg1:
            # SEGMENT 1: Bottom straight (left to right)
            # Trochoid: gear center at y = -(end_radius + gear_radius)
            dist = s
            gear_rot = base_rotation + dist / self.gear_radius
            
            # Gear center position
            cx = -self.straight_length / 2 + dist
            cy = -(self.end_radius + self.gear_radius)
            
            # Pen position (trochoid: pen points down at t=0)
            px = cx + self.pen_distance * np.sin(gear_rot)
            py = cy - self.pen_distance * np.cos(gear_rot)
            
        elif s <= seg2:
            # SEGMENT 2: Right semicircle - EPITROCHOID
            arc_s = s - seg1
            
            # Orbital angle φ around the semicircle (0 to π)
            phi = arc_s / (self.end_radius + self.gear_radius)  # NO! This is wrong
            # Actually: arc_s = (R + r) * φ for the gear center path
            # But the teeth are on the RACK, so the gear rolls on a path of radius R_end + r_gear
            # The arc length the gear center travels is (R_end + r_gear) * φ
            # And we know the arc length along the rack surface is end_arc_length = R_end * π for full semicircle
            # But the gear center path is longer by (R+r)/R
            
            # Let me reconsider:
            # The rack's semicircular end has radius R_end
            # The gear center orbits at radius (R_end + r_gear) 
            # When gear center travels arc_length on its orbital path, the rack surface traveled is:
            # surface_arc = orbital_arc * R_end / (R_end + r_gear)
            
            # We're parameterizing by rack surface distance s
            # So orbital angle φ = s / R_end (since s = R_end * φ on the rack surface)
            phi = arc_s / self.end_radius
            
            # Gear center position (orbiting around right end center)
            end_center_x = self.straight_length / 2
            end_center_y = 0
            orbit_r = self.end_radius + self.gear_radius
            
            # Position angle: starts at -π/2 (bottom), goes to +π/2 (top)
            pos_angle = -pi/2 + phi
            cx = end_center_x + orbit_r * np.cos(pos_angle)
            cy = end_center_y + orbit_r * np.sin(pos_angle)
            
            # Gear rotation: epitrochoid formula
            # For epitrochoid, pen angle = speed_ratio * orbital_angle
            # Total rotation = previous segments + epitrochoid rotation
            gear_rot = base_rotation + rotation_seg1 + self.speed_ratio * phi
            
            # Pen position
            px = cx + self.pen_distance * np.sin(gear_rot)
            py = cy - self.pen_distance * np.cos(gear_rot)
            
        elif s <= seg3:
            # SEGMENT 3: Top straight (right to left)
            dist = s - seg2
            gear_rot = base_rotation + rotation_seg1 + rotation_seg2 + dist / self.gear_radius
            
            # Gear center position (y = end_radius + gear_radius)
            cx = self.straight_length / 2 - dist
            cy = self.end_radius + self.gear_radius
            
            # Pen position
            px = cx + self.pen_distance * np.sin(gear_rot)
            py = cy - self.pen_distance * np.cos(gear_rot)
            
        else:
            # SEGMENT 4: Left semicircle - EPITROCHOID
            arc_s = s - seg3
            phi = arc_s / self.end_radius  # 0 to π
            
            # Gear center position (orbiting around left end center)
            end_center_x = -self.straight_length / 2
            end_center_y = 0
            orbit_r = self.end_radius + self.gear_radius
            
            # Position angle: starts at +π/2 (top), goes to +3π/2 (bottom)
            pos_angle = pi/2 + phi
            cx = end_center_x + orbit_r * np.cos(pos_angle)
            cy = end_center_y + orbit_r * np.sin(pos_angle)
            
            # Gear rotation
            gear_rot = base_rotation + rotation_seg1 + rotation_seg2 + rotation_seg3 + self.speed_ratio * phi
            
            # Pen position
            px = cx + self.pen_distance * np.sin(gear_rot)
            py = cy - self.pen_distance * np.cos(gear_rot)
        
        result = (px + 1j * py) * self.scale
        return z + result
    
    @property
    def natural_period(self) -> Fraction:
        """Period based on cycles."""
        return Fraction(self.cycles).limit_denominator(1000)
    
    def __repr__(self):
        return (f"RackModule(straight={self.straight_teeth}T, ends={self.end_teeth}T, "
                f"gear={self.gear_teeth}T, laps={self.laps}, cycles={self.cycles})")
