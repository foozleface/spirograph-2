# Spirograph Generator

A modular system for creating complex mathematical art through composed transformations — a digital spirograph toy where you can stack effects, run parallel drawing arms, and smoothly drift parameters to create patterns impossible with physical tools.

![Decay Shell Joe](decay_shell_joe.svg)

*Harmonograph + circle + translation running as simultaneous parallel arms, with rotation and parameter drift*

## Web UI

The interactive frontend runs as a single-file FastAPI + React app — no build step required.

```bash
pip install fastapi uvicorn numpy
python server.py
# Open http://127.0.0.1:8890/
```

### Features

- **Drag-and-drop pipeline builder** — drag generators and transforms from the palette onto a visual pipeline tree
- **Parallel arms (groups)** — drop a module *onto* an existing step to create simultaneous branches, like independent drawing arms on a mechanical machine
- **Placeholder slots** — click `+` to add empty slots, then drag modules into them
- **Continuous parameter drift** — expand any parameter's drift control to smoothly interpolate its value over the draw (e.g., hole position drifts from 0.5 to 0.8)
- **Moire effects** — overlay multiple copies of the pattern with a parameter varying across copies
- **Quality presets** — Draft / Fine / Ultra sampling resolution
- **File browser** — load, save, delete `.ini` files; click to load and auto-generate
- **SVG export** — download the generated pattern
- **Symmetry** — apply n-fold rotational and mirror symmetry
- **Live parameter editing** — sliders and number inputs with instant regeneration

## Command Line

```bash
# Generate from an INI file
python main.py examples/spirograph_gear_simple.ini

# PNG output (requires cairosvg)
python main.py examples/harmonograph_simple.ini --png output.png

# Generate all examples
./generate_all.sh --output-dir ./output
```

## How It Works

### Pipeline Composition

Every pattern is a pipeline of modules. Generators create shapes, transforms modify them, and the output of each feeds into the next:

```ini
[pipeline]
modules = spirograph_gear, rotation, arc
```

*"Generate a spirograph, rotate it while drawing, slide it along an arc."*

### Parallel Arms (Groups)

Modules separated by `|` in a group run simultaneously from the origin and their outputs sum — like independent drawing arms on a mechanical machine:

```ini
[arm]
type = group
modules = harmonograph | circle | translation
```

Each branch can itself be a serial chain:

```ini
[arm]
type = group
modules = gear1, slow_rotation | gear2, fast_rotation
```

### Parameter Drift

Any parameter with an `end_*` variant smoothly interpolates over the draw. Instead of discrete copies, the value changes continuously as the pen moves:

```ini
[gear]
type = spirograph_gear
hole_position = 0.3
end_hole_position = 0.9    # drifts from 0.3 → 0.9 over the draw
tooth_pitch = 1.0
end_tooth_pitch = 2.5      # drifts from 1.0 → 2.5 over the draw
```

## Generators

| Module | Description |
|--------|-------------|
| `spirograph_gear` | Classic two-gear spirograph (hypotrochoid/epitrochoid) |
| `harmonograph` | Pendulum simulator — 2–4 pendulums with decay |
| `lissajous` | Frequency-ratio curves (figure-8s, pretzels) |
| `rose` | Rhodonea petal patterns: r = cos(k·θ) |
| `circle` | Simple circle with radius drift |
| `polygon` | Regular polygons (triangle, hex, etc.) |
| `star_shape` | Pointed stars with inner/outer radii |
| `spiral_shape` | Archimedean spirals |
| `ellipse` | Oval with independent X/Y radii |
| `surface` | 3D parametric surfaces (torus, Möbius, Klein bottle, etc.) |
| `line` | Straight lines with timing control |
| `rack` | Gear rolling around stadium-shaped track |
| `spirograph_rail` | Gear rolling along a linear rail |

## Transforms

| Module | Description |
|--------|-------------|
| `rotation` | Spin the pattern around a point as it draws |
| `scale` | Grow or shrink over time |
| `translation` | Slide along a straight line |
| `arc` | Slide along a circular arc |
| `spiral_arc` | Slide along a spiral path |
| `bend` | Warp flat geometry into a curve (X→angle, Y→radius) |
| `damping` | Exponential decay envelope — pattern spirals toward a point |
| `noise` | Smooth random perturbation (hand-drawn look) |

## Configuration

```ini
[output]
width = 800
height = 800
stroke_width = 0.3
stroke_color = #000000
background_color = #ffffff
margin = 0.08

[sampling]
initial_samples = 100000   # Dense samples for accuracy
output_samples = 10000     # Final point count after arc-length resampling
use_arc_length = true
```

See `complete.ini` for documentation of every parameter.

## Requirements

- Python 3.8+
- NumPy
- FastAPI + Uvicorn (for web UI)
- Optional: `cairosvg` for PNG export

## License

MIT
