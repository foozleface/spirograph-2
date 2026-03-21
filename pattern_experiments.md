# Spirograph Pattern Experiments

208 pattern combinations tested against the `/api/generate-points` endpoint.
Each pattern evaluated for path length, structural complexity, and visual character.

**Key finding**: The `surface` module parameter must be `"surface"` not `"surface_type"` --
the latter silently defaults to torus for all surface types.

---

## Category 1: Damped Harmonographs (Best Overall Patterns)

Harmonographs with musical frequency ratios and slight detuning produce the richest,
most visually complex patterns. Higher frequency ratios = more complex structure.
Slow decay rates create denser fills.

### Top Pick: Slow Decay 4-Frequency (path_length=575409, paths=1, points=40000)

Extremely long-lived pattern with 4 frequencies at near-musical ratios. The very low
decay (0.001) means the pattern fills the entire drawing space with fine structure.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 3,
      "freq2": 2.003,
      "freq3": 5,
      "freq4": 4.002,
      "amp1": 100,
      "amp2": 80,
      "amp3": 50,
      "amp4": 40,
      "phase1": 0,
      "phase2": 0.7854,
      "phase3": 1.5708,
      "phase4": 2.3562,
      "decay1": 0.001,
      "decay2": 0.001,
      "decay3": 0.001,
      "decay4": 0.001,
      "duration": 150,
      "cycles": 1
    }
  }
]
```

### 7:5 Complex (path_length=397472, paths=1, points=40000)

High-frequency ratio creates intricate interference patterns. Dense center with
gradually loosening outer structure from asymmetric decay rates.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 7,
      "freq2": 5.003,
      "freq3": 3,
      "freq4": 4.005,
      "amp1": 100,
      "amp2": 80,
      "amp3": 60,
      "amp4": 50,
      "phase1": 0,
      "phase2": 1.5708,
      "phase3": 0.5,
      "phase4": 2.0,
      "decay1": 0.004,
      "decay2": 0.003,
      "decay3": 0.005,
      "decay4": 0.004,
      "duration": 60,
      "cycles": 1
    }
  }
]
```

### 5:4 Detuned (path_length=310599, paths=1, points=40000)

Classic just-major-third interval creates a recognizable but complex pattern.
The slight detuning prevents exact closure, creating visual depth.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 5,
      "freq2": 4.005,
      "freq3": 3,
      "freq4": 2.003,
      "amp1": 100,
      "amp2": 80,
      "amp3": 60,
      "amp4": 50,
      "phase1": 0,
      "phase2": 1.5708,
      "phase3": 0.5,
      "phase4": 2.0,
      "decay1": 0.004,
      "decay2": 0.003,
      "decay3": 0.005,
      "decay4": 0.004,
      "duration": 60,
      "cycles": 1
    }
  }
]
```

### 2:3:5:7 Prime Harmonics (path_length=257624, paths=1, points=40000)

All-prime frequency ratios produce patterns with no simple symmetry --
organic and aperiodic-looking.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 2,
      "freq2": 3.005,
      "freq3": 5,
      "freq4": 7.003,
      "amp1": 100,
      "amp2": 80,
      "amp3": 60,
      "amp4": 50,
      "phase1": 0,
      "phase2": 1.5708,
      "phase3": 0.5,
      "phase4": 2.0,
      "decay1": 0.004,
      "decay2": 0.003,
      "decay3": 0.005,
      "decay4": 0.004,
      "duration": 60,
      "cycles": 1
    }
  }
]
```

### Extreme Detuning (path_length=272548, paths=1, points=40000)

Larger detuning (+0.05 instead of +0.005) creates visible beat patterns --
the trace visibly "breathes" as frequencies go in and out of phase.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 2,
      "freq2": 2.05,
      "freq3": 3,
      "freq4": 3.07,
      "amp1": 100,
      "amp2": 80,
      "amp3": 60,
      "amp4": 40,
      "phase1": 0,
      "phase2": 1.5708,
      "phase3": 1.0,
      "phase4": 2.5,
      "decay1": 0.002,
      "decay2": 0.003,
      "decay3": 0.001,
      "decay4": 0.002,
      "duration": 100,
      "cycles": 1
    }
  }
]
```

### Drifting Amplitude (path_length=208493, paths=1, points=40000)

Amplitudes change over time, causing the pattern envelope to morph.
Creates asymmetric density: the pattern evolves as you draw.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 2,
      "freq2": 3.005,
      "amp1": 100,
      "amp2": 80,
      "end_amp1": 20,
      "end_amp2": 120,
      "phase1": 0,
      "phase2": 1.5708,
      "decay1": 0.003,
      "decay2": 0.004,
      "duration": 50,
      "cycles": 1
    }
  }
]
```

### Fast Decay (path_length=86305, paths=1, points=40000)

High decay rates (0.02) create dramatic spiral-in effects. The pattern
traces a complex outer shape then rapidly converges to center.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 3,
      "freq2": 2.005,
      "freq3": 5,
      "freq4": 7.003,
      "amp1": 120,
      "amp2": 100,
      "amp3": 80,
      "amp4": 60,
      "phase1": 0,
      "phase2": 1.5708,
      "phase3": 0.5,
      "phase4": 2.0,
      "decay1": 0.02,
      "decay2": 0.015,
      "decay3": 0.025,
      "decay4": 0.02,
      "duration": 20,
      "cycles": 1
    }
  }
]
```

---

## Category 2: Harmonograph + Circle Groups

Superimposing a harmonograph with a circle creates oscillating-orbit patterns.
The circle adds periodic loops that ride the harmonograph's damped trajectory.

### Small Fast Circles (path_length=144103, paths=1, points=40000)

Many small fast circles (r=15, 20 cycles) riding the harmonograph create
a fuzzy texture along the decay path.

```json
[
  {
    "kind": "group",
    "branches": [
      [
        {
          "type": "harmonograph",
          "freq1": 2,
          "freq2": 3.005,
          "amp1": 100,
          "amp2": 80,
          "phase1": 0,
          "phase2": 1.5708,
          "decay1": 0.005,
          "decay2": 0.004,
          "duration": 40,
          "cycles": 1
        }
      ],
      [
        {
          "type": "circle",
          "radius": 15,
          "end_radius": 15,
          "cycles": 20
        }
      ]
    ]
  }
]
```

### Large Slow Circles (path_length=127011, paths=1, points=40000)

Larger circles (r=30, 5 cycles) create clearly visible loops that sweep
through the harmonograph envelope.

```json
[
  {
    "kind": "group",
    "branches": [
      [
        {
          "type": "harmonograph",
          "freq1": 2,
          "freq2": 3.005,
          "amp1": 100,
          "amp2": 80,
          "phase1": 0,
          "phase2": 1.5708,
          "decay1": 0.005,
          "decay2": 0.004,
          "duration": 40,
          "cycles": 1
        }
      ],
      [
        {
          "type": "circle",
          "radius": 30,
          "end_radius": 30,
          "cycles": 5
        }
      ]
    ]
  }
]
```

---

## Category 3: Gear Patterns

Gear ratios determine symmetry and complexity. Coprime teeth counts produce
the most intricate patterns. Fibonacci ratios are especially interesting.

### Fibonacci Gears (path_length=154740, paths=1, points=40000)

233:144 teeth (consecutive Fibonacci numbers) produces a nearly irrational
ratio, creating extremely dense fill patterns that almost never close.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_gear",
      "fixed_teeth": 233,
      "rolling_teeth": 144,
      "tooth_pitch": 1.0,
      "hole_position": 0.8,
      "inside": true,
      "cycles": 1
    }
  }
]
```

### Large Coprime (path_length=123256, paths=1, points=40000)

200:73 -- large coprime ratio creates 200 lobes with intricate interweaving.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_gear",
      "fixed_teeth": 200,
      "rolling_teeth": 73,
      "tooth_pitch": 1.0,
      "hole_position": 0.8,
      "inside": true,
      "cycles": 1
    }
  }
]
```

### Gear + Rotation + Scale (path_length=42916, paths=1, points=40000)

Layering a gear pattern with progressive rotation and scale creates
concentric rings of increasingly-rotated gear traces.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_gear",
      "fixed_teeth": 100,
      "rolling_teeth": 37,
      "tooth_pitch": 1.0,
      "hole_position": 0.8,
      "inside": true,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 720,
      "normalize": true
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "scale",
      "start_scale": 0.3,
      "end_scale": 1.0
    }
  }
]
```

### Gear + Damping (path_length=56693, paths=1, points=40000)

Damping a gear pattern creates spiral-in effect where gear loops
progressively shrink toward center.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_gear",
      "fixed_teeth": 100,
      "rolling_teeth": 37,
      "tooth_pitch": 1.0,
      "hole_position": 0.8,
      "inside": true,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "damping",
      "decay_rate": 0.005,
      "duration": 40
    }
  }
]
```

### Gear with Drifting Hole (path_length=82422, paths=1, points=40000)

The hole position drifts from 0.3 to 0.95 over the drawing. Creates
a pattern that evolves from nearly-circular to deeply-cusped.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_gear",
      "fixed_teeth": 144,
      "rolling_teeth": 55,
      "tooth_pitch": 1.0,
      "hole_position": 0.3,
      "end_hole_position": 0.95,
      "inside": true,
      "cycles": 1
    }
  }
]
```

### Gear + Bend (path_length=90442, paths=1, points=40000)

Bending a complex gear pattern wraps it into a curved shape.
Works best with coprime ratios that produce long traces.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_gear",
      "fixed_teeth": 144,
      "rolling_teeth": 55,
      "tooth_pitch": 1.0,
      "hole_position": 0.8,
      "inside": true,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "bend",
      "radius": 200,
      "sweep_angle": 180
    }
  }
]
```

---

## Category 4: Lissajous Figures

Higher frequency ratios produce more complex knot-like patterns.
Adjacent frequencies (n:n+1) create the densest fills.

### 9:8 Lissajous (path_length=137704, paths=1, points=40000)

Adjacent high frequencies create an extremely dense mesh pattern
with fine internal structure.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "lissajous",
      "freq_x": 9,
      "freq_y": 8,
      "amp_x": 100,
      "amp_y": 100,
      "phase": 1.5708,
      "cycles": 1
    }
  }
]
```

### 7:8 Lissajous (path_length=121552, paths=1, points=40000)

Similar dense mesh but with different crossing pattern.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "lissajous",
      "freq_x": 7,
      "freq_y": 8,
      "amp_x": 100,
      "amp_y": 100,
      "phase": 0.7,
      "cycles": 1
    }
  }
]
```

### Lissajous + Scale + Rotation (path_length=36900, paths=1, points=40000)

Scaling and rotating a Lissajous figure creates nested, rotated copies
that produce moire-like interference.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "lissajous",
      "freq_x": 5,
      "freq_y": 6,
      "amp_x": 100,
      "amp_y": 100,
      "phase": 0.5,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "scale",
      "start_scale": 0.5,
      "end_scale": 1.2
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  }
]
```

### Lissajous + Damping (path_length=59725, paths=1, points=40000)

Damping creates a Lissajous that spirals inward, like a harmonograph
but with the characteristic rectangular envelope of Lissajous figures.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "lissajous",
      "freq_x": 5,
      "freq_y": 6,
      "amp_x": 100,
      "amp_y": 100,
      "phase": 0.5,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "damping",
      "decay_rate": 0.008,
      "duration": 30
    }
  }
]
```

---

## Category 5: Ellipse Petal Family

Ellipses combined with rotation create flower-like patterns. The ratio
of radius_x/radius_y controls petal width; cycle count controls petal number.

### Razor Petals (path_length=28845, paths=1, points=40000)

Extreme aspect ratio (80:10) with 20 cycles creates very narrow,
dense petals -- almost like a starburst.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "ellipse",
      "radius_x": 80,
      "radius_y": 10,
      "end_radius_x": 80,
      "end_radius_y": 10,
      "cycles": 20
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 720,
      "normalize": true
    }
  }
]
```

### Ellipse with Internal Rotation (path_length=27309, paths=1, points=40000)

The `rotation` parameter on the ellipse itself creates a different
effect than the rotation transform -- the ellipse axis rotates
as it traces, creating spiraling petal patterns.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "ellipse",
      "radius_x": 100,
      "radius_y": 10,
      "cycles": 20,
      "rotation": 360
    }
  }
]
```

### High-Cycle Petals (path_length=21440, paths=1, points=40000)

15 cycles at 1440-degree rotation create a dense flower with
many overlapping petals.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "ellipse",
      "radius_x": 50,
      "radius_y": 30,
      "end_radius_x": 90,
      "end_radius_y": 10,
      "cycles": 15
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 1440,
      "normalize": true
    }
  }
]
```

### Morphing Axes (path_length=10314, paths=1, points=40000)

Radius changes from (60,60) to (20,100) -- the ellipse starts
as a circle and stretches, creating petals that widen as they go.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "ellipse",
      "radius_x": 60,
      "radius_y": 60,
      "end_radius_x": 20,
      "end_radius_y": 100,
      "cycles": 6
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  }
]
```

---

## Category 6: Surfaces

3D parametric surfaces projected to 2D. Each draws a spiral trace across
the surface. Different surface types produce genuinely different patterns
when using the correct `"surface"` parameter.

### Klein Bottle Front (path_length=44947, paths=1, points=40000)

The Klein bottle's self-intersection creates distinctive crossing patterns.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "surface",
      "surface": "klein",
      "major_radius": 80,
      "minor_radius": 30,
      "u_lines": 50,
      "v_lines": 25,
      "view_angle_x": 30,
      "view_angle_y": 20,
      "width": 60,
      "twists": 1
    }
  }
]
```

### Mobius Strip (path_length=41185, paths=1, points=40000)

The half-twist creates a single-sided trace with characteristic twist.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "surface",
      "surface": "mobius",
      "major_radius": 80,
      "minor_radius": 30,
      "u_lines": 50,
      "v_lines": 25,
      "view_angle_x": 30,
      "view_angle_y": 20,
      "width": 60,
      "twists": 1
    }
  }
]
```

### Torus with Rotation (path_length=37410, paths=1, points=40000)

Adding a rotation transform to a torus creates a moiré-like layered effect.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "surface",
      "surface": "torus",
      "major_radius": 80,
      "minor_radius": 30,
      "u_lines": 50,
      "v_lines": 25,
      "view_angle_x": 30,
      "view_angle_y": 20
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  }
]
```

### Torus Bent (path_length=29036, paths=1, points=40000)

Bending a torus surface creates a double-curved shape.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "surface",
      "surface": "torus",
      "major_radius": 60,
      "minor_radius": 20,
      "u_lines": 40,
      "v_lines": 20,
      "view_angle_x": 30,
      "view_angle_y": 15
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "bend",
      "radius": 200,
      "sweep_angle": 180
    }
  }
]
```

---

## Category 7: Multi-Arm Groups

Superimposing different generator types creates hybrid patterns.
Harmonographs dominate due to their high path lengths.

### Dual Harmonograph (path_length=185985, paths=1, points=40000)

Two harmonographs at different frequency ratios (2:3 and 5:7) superimposed.
Creates an incredibly complex interference pattern.

```json
[
  {
    "kind": "group",
    "branches": [
      [
        {
          "type": "harmonograph",
          "freq1": 2,
          "freq2": 3.005,
          "amp1": 80,
          "amp2": 60,
          "phase1": 0,
          "phase2": 1.5708,
          "decay1": 0.003,
          "decay2": 0.004,
          "duration": 50,
          "cycles": 1
        }
      ],
      [
        {
          "type": "harmonograph",
          "freq1": 5,
          "freq2": 7.003,
          "amp1": 30,
          "amp2": 25,
          "phase1": 0.5,
          "phase2": 2.0,
          "decay1": 0.005,
          "decay2": 0.006,
          "duration": 50,
          "cycles": 1
        }
      ]
    ]
  }
]
```

### Triple Arm: Harmonograph + Harmonograph + Circle (path_length=160211, paths=1, points=40000)

Two different harmonographs plus a shrinking circle create a pattern with
multiple scales of structure.

```json
[
  {
    "kind": "group",
    "branches": [
      [
        {
          "type": "harmonograph",
          "freq1": 3,
          "freq2": 2.005,
          "amp1": 80,
          "amp2": 60,
          "phase1": 0,
          "phase2": 0.7,
          "decay1": 0.003,
          "decay2": 0.004,
          "duration": 50,
          "cycles": 1
        }
      ],
      [
        {
          "type": "harmonograph",
          "freq1": 5,
          "freq2": 4.003,
          "amp1": 40,
          "amp2": 30,
          "phase1": 1.0,
          "phase2": 2.0,
          "decay1": 0.005,
          "decay2": 0.006,
          "duration": 50,
          "cycles": 1
        }
      ],
      [
        {
          "type": "circle",
          "radius": 15,
          "end_radius": 5,
          "cycles": 12
        }
      ]
    ]
  }
]
```

### Harmonograph + Gear + Rotation (path_length=139473, paths=1, points=40000)

Harmonograph and gear superimposed, then rotated. The gear adds periodic
cusps to the harmonograph's smooth decay.

```json
[
  {
    "kind": "group",
    "branches": [
      [
        {
          "type": "harmonograph",
          "freq1": 3,
          "freq2": 2.005,
          "amp1": 60,
          "amp2": 40,
          "phase1": 0,
          "phase2": 1.0,
          "decay1": 0.004,
          "decay2": 0.005,
          "duration": 40,
          "cycles": 1
        }
      ],
      [
        {
          "type": "spirograph_gear",
          "fixed_teeth": 80,
          "rolling_teeth": 21,
          "tooth_pitch": 0.5,
          "hole_position": 0.7,
          "inside": true,
          "cycles": 1
        }
      ]
    ]
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  }
]
```

### Triple Arm: Lissajous + Gear + Spiral (path_length=20838, paths=1, points=40000)

Three completely different generator types create a hybrid with
rectangular (Lissajous), cusped (gear), and expanding (spiral) character.

```json
[
  {
    "kind": "group",
    "branches": [
      [
        {
          "type": "lissajous",
          "freq_x": 3,
          "freq_y": 4,
          "amp_x": 40,
          "amp_y": 40,
          "phase": 1.5708,
          "cycles": 1
        }
      ],
      [
        {
          "type": "spirograph_gear",
          "fixed_teeth": 60,
          "rolling_teeth": 17,
          "tooth_pitch": 0.5,
          "hole_position": 0.8,
          "inside": true,
          "cycles": 1
        }
      ],
      [
        {
          "type": "spiral_shape",
          "start_radius": 5,
          "end_radius": 20,
          "turns": 3,
          "cycles": 1
        }
      ]
    ]
  }
]
```

---

## Category 8: Spirals

Spiral shapes with various transforms. Dense turn counts create interesting fills.

### Dense 40-Turn Spiral (path_length=46709, paths=1, points=40000)

40 turns from radius 10 to 100 creates a tightly-wound filling pattern.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spiral_shape",
      "start_radius": 10,
      "end_radius": 100,
      "turns": 40,
      "cycles": 1
    }
  }
]
```

### Spiral + Bend (path_length=7183, paths=1, points=40000)

Bending a spiral wraps it into a curved tube shape.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spiral_shape",
      "start_radius": 10,
      "end_radius": 100,
      "turns": 6,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "bend",
      "radius": 150,
      "sweep_angle": 360
    }
  }
]
```

---

## Category 9: Rack and Rail

Physical spirograph rack/rail patterns. Need multiple laps/passes for complexity.

### Rack 8-Lap Rotated (path_length=14548, paths=1, points=40000)

8 laps around the rack track, then rotated 360 degrees, creates
a ring of overlapping trochoid patterns.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "rack",
      "straight_teeth": 50,
      "end_teeth": 24,
      "gear_teeth": 24,
      "tooth_pitch": 2.0,
      "hole_position": 0.75,
      "laps": 8
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  }
]
```

### Rack Bent 360 (path_length=8419, paths=1, points=40000)

5 laps bent into a full circle -- wraps the linear rack into a ring shape.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "rack",
      "straight_teeth": 50,
      "end_teeth": 24,
      "gear_teeth": 24,
      "tooth_pitch": 2.0,
      "hole_position": 0.75,
      "laps": 5
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "bend",
      "radius": 200,
      "sweep_angle": 360
    }
  }
]
```

### Rail 12-Pass (path_length=8808, paths=1, points=40000)

12 passes along the rail with back-and-forth creates a dense trochoid weave.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "spirograph_rail",
      "rail_length": 200,
      "gear_teeth": 40,
      "tooth_pitch": 1.0,
      "hole_position": 0.6,
      "passes": 12
    }
  }
]
```

---

## Category 10: Chained Transforms

Multiple transforms create layered effects. The best chains combine
geometric (rotation, scale) with deformation (bend, arc) transforms.

### Harmonograph + Arc Ring (path_length=49890, paths=1, points=40000)

Wrapping a harmonograph around an arc creates a ring of decaying oscillation.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 3,
      "freq2": 2.005,
      "amp1": 40,
      "amp2": 30,
      "phase1": 0,
      "phase2": 1.5708,
      "decay1": 0.005,
      "decay2": 0.004,
      "duration": 40,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "arc",
      "arc_radius": 120,
      "sweep_angle": 360,
      "start_angle": 0,
      "cycles": 1
    }
  }
]
```

### Harmonograph + Translation (path_length=49816, paths=1, points=40000)

Translating a harmonograph creates a decaying oscillation that drifts across
the canvas -- like a physical pendulum on a moving platform.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 2,
      "freq2": 3.005,
      "amp1": 60,
      "amp2": 50,
      "phase1": 0,
      "phase2": 1.5708,
      "decay1": 0.006,
      "decay2": 0.005,
      "duration": 30,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "translation",
      "start_x": -100,
      "end_x": 100,
      "start_y": 0,
      "end_y": 0,
      "normalize": true
    }
  }
]
```

### Circle + Translation + Rotation + Noise (path_length=6315, paths=1, points=40000)

Simple circle made complex: translated, rotated into a ring, then textured
with noise. Creates a fuzzy torus shape.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "circle",
      "radius": 30,
      "cycles": 8
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "translation",
      "start_x": 0,
      "end_x": 80,
      "start_y": 0,
      "end_y": 0,
      "normalize": true
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "noise",
      "amplitude": 2,
      "frequency": 10
    }
  }
]
```

### Lissajous + Damping + Rotation + Scale (path_length=15237, paths=1, points=40000)

Four-stage chain: Lissajous figure that damps, rotates, and scales.
Creates concentric, rotated, shrinking Lissajous copies.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "lissajous",
      "freq_x": 3,
      "freq_y": 4,
      "amp_x": 80,
      "amp_y": 80,
      "phase": 1.5708,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "damping",
      "decay_rate": 0.008,
      "duration": 40
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "scale",
      "start_scale": 0.2,
      "end_scale": 1.0
    }
  }
]
```

---

## Category 11: Noise Textures

Noise adds organic texture to clean geometric patterns.

### Harmonograph + Noise (path_length=168799, paths=1, points=40000)

Subtle noise on a harmonograph adds a hand-drawn quality
without destroying the underlying structure.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "harmonograph",
      "freq1": 2,
      "freq2": 3.005,
      "amp1": 100,
      "amp2": 80,
      "phase1": 0,
      "phase2": 1.5708,
      "decay1": 0.004,
      "decay2": 0.003,
      "duration": 40,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "noise",
      "amplitude": 3,
      "frequency": 5
    }
  }
]
```

### Circle + Heavy Noise (path_length=9973, paths=1, points=40000)

Heavy noise on a simple circle creates an abstract woolly texture.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "circle",
      "radius": 80,
      "cycles": 5
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "noise",
      "amplitude": 8,
      "frequency": 3
    }
  }
]
```

---

## Category 12: Rose Curves

Rose curves have fixed path lengths regardless of petal/denom parameters
(all ~5105 in our tests), suggesting the curve length is normalized.
Best used as components in groups rather than standalone.

### Rose + Scale (path_length=3611, paths=1, points=40000)

Scaling creates a spiral-rose hybrid where petals grow over time.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "rose",
      "petals": 5,
      "denom": 3,
      "radius": 100,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "scale",
      "start_scale": 0.3,
      "end_scale": 1.5
    }
  }
]
```

### Rose + Rotation (path_length=5333, paths=1, points=40000)

Slight rotation creates overlapping petal layers.

```json
[
  {
    "kind": "single",
    "params": {
      "type": "rose",
      "petals": 7,
      "denom": 3,
      "radius": 100,
      "cycles": 1
    }
  },
  {
    "kind": "single",
    "params": {
      "type": "rotation",
      "total_degrees": 360,
      "normalize": true
    }
  }
]
```

---

## Summary of Best Recipes for Random Generation

| Category | Best Pattern | Path Length | Key Insight |
|----------|-------------|-------------|-------------|
| Harmonograph | harm_slow_decay | 575,409 | Very low decay + 4 freqs = richest patterns |
| Harmonograph | harm_damp_7:5 complex | 397,472 | Higher freq ratios = more complexity |
| Group | group_dual_harm | 185,985 | Two harmonographs beat one |
| Group | 3arm_harm_harm_circle | 160,211 | Three arms with shrinking circle |
| Gear | gear_fib_large (233:144) | 154,740 | Fibonacci ratios for near-irrational fill |
| Lissajous | liss_9_8 | 137,704 | Adjacent high freqs for dense mesh |
| Gear+Transform | group_harm_gear_rot | 139,473 | Gear + harmonograph hybrid |
| Harmonograph | harm_extreme_detune | 272,548 | Large detuning for beat patterns |
| Gear | gear_damped | 56,694 | Damping on gear = spiral-in cusps |
| Ellipse | ellipse_petal_razor_petal | 28,845 | Extreme aspect ratio petals |
| Surface | surf_klein_front | 44,947 | Klein bottle self-intersection |
| Rack | rack_8lap_rot | 14,548 | Multi-lap rack + rotation |
| Spiral | spiral_dense_40 | 46,709 | High turn count fills |
