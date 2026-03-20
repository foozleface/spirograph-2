# Pattern Experiment Results

12 experiments testing new pattern combinations. Rated by visual quality.

## Winners (add to random recipes)

### Harmonograph Amplitude Drift — "Butterfly"
Harmonograph with 3 pendulums, all amplitudes drifting down over the draw. Creates a pillow/butterfly shape with beautiful depth gradient from dense center to light edges.
```
type:harmonograph, freq1:2, amp1:120, end_amp1:40, decay1:0.003,
freq2:3.004, amp2:120, end_amp2:60, phase2:90, decay2:0.003,
freq3:1.002, amp3:50, end_amp3:10, phase3:45, decay3:0.003
duration:100, cycles:4
```

### Torus + Rotation 360 — "Trefoil Knot"
Surface torus with full 360-degree rotation. Produces an elegant trefoil knot shape with clean, evenly spaced lines. Looks like a Celtic knot.
```
type:surface, surface_type:torus, major_radius:120, minor_radius:50,
u_lines:80, v_lines:40, view_angle_x:30, view_angle_y:20
→ rotation total_degrees:360
```

### Gear Drift + Bend — "Wreath"
Spirograph gear with hole_position drifting from 0.5 to 0.85 over 15 cycles, translated and bent into a ring, then rotated. Creates a detailed wreath/garland pattern.
```
type:spirograph_gear, fixed_teeth:105, rolling_teeth:52, tooth_pitch:6,
hole_position:0.5, end_hole_position:0.85, inside:true, cycles:15
→ translation end_x:200
→ bend radius:200, sweep_angle:200
→ rotation total_degrees:270
```

### Lissajous 7:8 + Scale Decay — "Nautilus Mesh"
High-frequency Lissajous (7:8 ratio near unison) with scale shrinking to 0.3 and 180-degree rotation. Creates an intricate nautilus-like spiral mesh.
```
type:lissajous, freq_x:7, freq_y:8, amp_x:120, amp_y:120, phase:60, cycles:3
→ scale start_scale:1.0, end_scale:0.3
→ rotation total_degrees:180
```

### Ellipse Axis Swap + Damping — "Lens"
Ellipse where axes swap over 150 cycles (wide→tall) with damping and rotation. Produces a striking eye/lens shape unlike anything else in the system.
```
type:ellipse, radius_x:180, radius_y:30, end_radius_x:30, end_radius_y:180,
cycles:150, rotation:0
→ damping decay_rate:0.015, duration:60
→ rotation total_degrees:180
```

## Good (occasionally use in random)

### 3-Arm Group — harm + gear + circle
Complex organic form. Works because the three generators have very different frequencies/scales.

### Dual Harmonograph — 2:3 + 5:4
Two harmonographs with different consonances summed, then damped. Dense and dramatic.

### Gear Epitrochoid + Noise
Clean ring pattern with subtle hand-drawn texture from noise module. The noise amplitude must be small (2-4) relative to the pattern.

## Failures (avoid in random)

- Rose + symmetry alone: too simple, needs more structure
- Circle drift + symmetry: just concentric circles, boring
- Mobius + damping: too sparse, damping kills the detail
- Star + scale alone: clean but uninteresting
