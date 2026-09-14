"""What modules exist, what knobs they have, and what those knobs mean.

Pure data. The UI builds its palette and its parameter editors from this, the
INI writer validates against it, and nothing here imports anything — which is
why the same table can serve a Qt panel, a web page and a test.

Each entry is ``type -> {category, label, desc, params}``; each parameter is
``name -> {type, default, min, max, step, desc}``. A parameter carrying
``drift_for`` is the *end* value of another parameter: the pipeline interpolates
from the base value to this one over the course of the draw. One marked
``advanced`` is real but rarely wanted — the window folds those away; one
marked ``hidden`` is read by the module but not worth a knob at all.

The table is exhaustive: every key a module reads is here, and
:func:`valid_keys` is what the INI writer checks a parameter against. A key
that is not here is a mistake, and it is refused rather than silently read
as its default — which is how a third of the recipes came to draw something
other than what they said.

Every module also reads the common keys (``easing``; ``normalize`` on the
transforms that offer it; ``osc_<name>`` beside any drifting parameter;
``scope`` on every transform), see :data:`COMMON_PARAMS`,
:data:`TRANSFORM_PARAMS` and :func:`valid_keys`.

Three categories, and the words the window uses for them:

* ``generator`` — an **arm**. Adds a moving vector to where the pen is; arms
  chain end to end, each turning at its own rate. Two circles are an
  epicycle; a gear is two arms in one.
* ``path`` — a **carriage**. Also adds a vector — the whole mechanism rides
  along a line, an arc, a spiral, a rail — so in the engine it is an arm
  too. Kept apart because a person reaches for it to *move the drawing
  somewhere*, not to add a lobe.
* ``transform`` — a **table move**. Acts on what is already drawn: the paper
  turns, grows, shrinks, wobbles, bends round a drum. ``scope`` says whether
  it moves under everything so far, or only under the last arm (or last
  few) — the difference between spinning the paper and spinning one arm's
  pivot.
"""

# Read by the base class for every module: the timing curve applied to the
# module's own clock.
EASING_MODES = ["linear", "ease_in", "ease_out", "ease_in_out", "sine"]

COMMON_PARAMS = {
    "easing": {"type": "choice", "choices": EASING_MODES, "default": "linear",
               "desc": "Timing curve", "advanced": True},
}

# Read by the base class for every transform. 'all' acts on everything drawn
# so far; an integer k acts on the last k arms only, as if the table turned
# under those arms alone. The window shows it as a bracket beside the steps.
TRANSFORM_PARAMS = {
    "scope": {"type": "scope", "default": "all", "desc": "Acts on"},
}

CATEGORIES = {
    "generator": {"label": "Arms", "word": "arm",
                  "blurb": "Adds a moving arm. Arms chain end to end, each turning at its own rate."},
    "path":      {"label": "Carriage paths", "word": "path",
                  "blurb": "Carries the whole mechanism along a line, an arc, a spiral, a rail."},
    "transform": {"label": "Table moves", "word": "move",
                  "blurb": "Moves the paper under what is drawn: turn, grow, shrink, bend, wobble."},
    "clock":     {"label": "Clocks", "word": "clock",
                  "blurb": "Changes the time every step after it sees: backwards, there and back, in steps, faster."},
}

# The passes that act on the finished curve, in the order they run. Each is
# an INI section of its own name; the document keeps them in `extras`
# (symmetry has its own slot for historical reasons). Built into the
# window's Finishing panel from this table.
FINISHING_DEFS = {
    "symmetry": {
        "label": "Symmetry",
        "desc": "Repeat the finished curve around a centre, and optionally mirror it",
        "params": {
            "n_fold":   {"type": "int",   "default": 1,   "min": 1, "max": 64, "desc": "Fold (1 = none)"},
            "mirror":   {"type": "bool",  "default": False, "desc": "Mirror as well as rotate"},
            "center_x": {"type": "float", "default": 0.0, "min": -5000, "max": 5000, "desc": "Centre X", "advanced": True},
            "center_y": {"type": "float", "default": 0.0, "min": -5000, "max": 5000, "desc": "Centre Y", "advanced": True},
        },
    },
    "pen_lift": {
        "label": "Pen lift",
        "desc": "Break the line into separate strokes",
        "params": {
            "mode":        {"type": "choice", "choices": ["periodic", "threshold", "angular"], "default": "periodic", "desc": "How"},
            "draw_length": {"type": "int",   "default": 100,  "min": 1, "max": 100000, "desc": "Draw for (points)", "when": "periodic"},
            "skip_length": {"type": "int",   "default": 50,   "min": 1, "max": 100000, "desc": "Then skip (points)", "when": "periodic"},
            "threshold":   {"type": "float", "default": 20.0, "min": 0.01, "max": 10000, "desc": "Lift beyond", "when": "threshold"},
            "angle_draw":  {"type": "float", "default": 30.0, "min": 0.1, "max": 360, "desc": "Draw wedge°", "when": "angular"},
            "angle_skip":  {"type": "float", "default": 10.0, "min": 0, "max": 360, "desc": "Skip wedge°", "when": "angular"},
            "center_x":    {"type": "float", "default": 0.0, "min": -5000, "max": 5000, "desc": "Centre X", "when": "angular"},
            "center_y":    {"type": "float", "default": 0.0, "min": -5000, "max": 5000, "desc": "Centre Y", "when": "angular"},
        },
    },
    "moire": {
        "label": "Moiré",
        "desc": "Overlay near-copies of the whole pattern, one parameter nudged",
        "params": {
            "copies":     {"type": "int",   "default": 5,    "min": 2, "max": 40, "desc": "Copies"},
            "vary_param": {"type": "param", "default": "",   "desc": "Vary"},
            "vary_range": {"type": "float", "default": 0.05, "min": 0.0001, "max": 10000, "desc": "Spread ±"},
            "modules":    {"type": "str",   "default": "",   "desc": "Filled in from the pipeline", "hidden": True},
        },
    },
    "tile": {
        "label": "Tile",
        "desc": "Repeat the whole drawing in a grid",
        "params": {
            "rows":    {"type": "int",   "default": 2,     "min": 1, "max": 40, "desc": "Rows"},
            "cols":    {"type": "int",   "default": 2,     "min": 1, "max": 40, "desc": "Columns"},
            "dx":      {"type": "float", "default": 200.0, "min": -5000, "max": 5000, "desc": "Step across"},
            "dy":      {"type": "float", "default": 200.0, "min": -5000, "max": 5000, "desc": "Step down"},
            "stagger": {"type": "bool",  "default": False, "desc": "Offset every other row by half"},
        },
    },
    "clip": {
        "label": "Clip",
        "desc": "Keep only what falls inside a circle or a rectangle",
        "params": {
            "shape":    {"type": "choice", "choices": ["circle", "rect"], "default": "circle", "desc": "Shape"},
            "radius":   {"type": "float", "default": 100.0, "min": 0.1, "max": 5000, "desc": "Radius", "when": "circle"},
            "width":    {"type": "float", "default": 200.0, "min": 0.1, "max": 5000, "desc": "Width", "when": "rect"},
            "height":   {"type": "float", "default": 200.0, "min": 0.1, "max": 5000, "desc": "Height", "when": "rect"},
            "center_x": {"type": "float", "default": 0.0, "min": -5000, "max": 5000, "desc": "Centre X", "advanced": True},
            "center_y": {"type": "float", "default": 0.0, "min": -5000, "max": 5000, "desc": "Centre Y", "advanced": True},
            "invert":   {"type": "bool",  "default": False, "desc": "Keep the outside instead"},
        },
    },
}

# A drifting parameter may oscillate between its two values instead of
# sliding once: ``osc_<name> = speed, irregularity``. Speed is how many times
# it goes there and back over the draw; irregularity (0-1) mixes in two
# incommensurate cosines so it wanders rather than ticks.
OSC_PREFIX = "osc_"

def _adv(**kw):
    kw["advanced"] = True
    return kw

_ORIGIN = {
    "origin_x": {"type": "float", "default": 0.0, "min": -300, "max": 300, "desc": "Centre X", "advanced": True},
    "origin_y": {"type": "float", "default": 0.0, "min": -300, "max": 300, "desc": "Centre Y", "advanced": True},
}
_CENTER = {
    "center_x": {"type": "float", "default": 0.0, "min": -300, "max": 300, "desc": "Centre X", "advanced": True},
    "center_y": {"type": "float", "default": 0.0, "min": -300, "max": 300, "desc": "Centre Y", "advanced": True},
}
_NORMALIZE = {"normalize": {"type": "bool", "default": True, "desc": "Own clock spans the whole draw", "advanced": True}}
_VIEW = {
    "view_angle_x": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt X"},
    "view_angle_y": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Y"},
    "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
}
# The surface parametrisation ranges, in radians. Real, but a partial
# surface is rarely what anyone wants from a knob.
_UV = {
    "u_min": {"type": "float", "default": 0.0, "min": -50, "max": 50, "desc": "u from", "hidden": True},
    "u_max": {"type": "float", "default": 6.283185307179586, "min": -50, "max": 50, "desc": "u to", "hidden": True},
    "v_min": {"type": "float", "default": 0.0, "min": -50, "max": 50, "desc": "v from", "hidden": True},
    "v_max": {"type": "float", "default": 6.283185307179586, "min": -50, "max": 50, "desc": "v to", "hidden": True},
}

MODULE_DEFS = {
    "spirograph_gear": {
        "category": "generator",
        "label": "Spirograph Gear",
        "desc": "Classic two-gear spirograph (hypotrochoid / epitrochoid)",
        "params": {
            "fixed_teeth":       {"type": "int",   "default": 96,   "min": 10,  "max": 300, "desc": "Fixed gear teeth"},
            "rolling_teeth":     {"type": "int",   "default": 36,   "min": 5,   "max": 200, "desc": "Rolling gear teeth"},
            "tooth_pitch":       {"type": "float", "default": 1.0,  "min": 0.1, "max": 5.0, "step": 0.1, "desc": "Size per tooth"},
            "end_tooth_pitch":   {"type": "float", "default": 1.0,  "min": 0.1, "max": 5.0, "step": 0.1, "desc": "End value", "drift_for": "tooth_pitch"},
            "hole_position":     {"type": "float", "default": 0.7,  "min": 0.0, "max": 1.5, "step": 0.05, "desc": "Pen hole (0 centre, 1 edge)"},
            "end_hole_position": {"type": "float", "default": 0.7,  "min": 0.0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "inside":            {"type": "bool",  "default": True,  "desc": "Inside (hypo) vs outside (epi)"},
            "cycles":            {"type": "float", "default": 1.0,  "min": 1,   "max": 50, "step": 1, "desc": "Repetitions"},
            "rotations":         {"type": "int",   "default": 0,    "min": 0,   "max": 200, "desc": "Turns around the fixed gear (0 = until it closes)", "advanced": True},
        },
    },
    "harmonograph": {
        "category": "generator",
        "label": "Harmonograph",
        "desc": "Pendulum drawing simulator (2-4 pendulums)",
        "params": {
            "freq1":  {"type": "float", "default": 2.0,   "min": 0.1, "max": 10, "step": 0.1, "desc": "Pendulum 1 freq"},
            "amp1":   {"type": "float", "default": 100.0, "min": 1,   "max": 200, "desc": "Pendulum 1 amp"},
            "end_amp1": {"type": "float", "default": 100.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp1"},
            "phase1": {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Pendulum 1 phase°"},
            "decay1": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 1 decay"},
            "freq2":  {"type": "float", "default": 3.0,   "min": 0.1, "max": 10, "step": 0.1, "desc": "Pendulum 2 freq"},
            "amp2":   {"type": "float", "default": 100.0, "min": 1,   "max": 200, "desc": "Pendulum 2 amp"},
            "end_amp2": {"type": "float", "default": 100.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp2"},
            "phase2": {"type": "float", "default": 90.0,  "min": 0,   "max": 360, "desc": "Pendulum 2 phase°"},
            "decay2": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 2 decay"},
            "freq3":  {"type": "float", "default": 0.0,   "min": 0,   "max": 10, "step": 0.1, "desc": "Pendulum 3 freq (0=off)"},
            "amp3":   {"type": "float", "default": 0.0,   "min": 0,   "max": 200, "desc": "Pendulum 3 amp"},
            "end_amp3": {"type": "float", "default": 0.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp3"},
            "phase3": {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Pendulum 3 phase°"},
            "decay3": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 3 decay"},
            "freq4":  {"type": "float", "default": 0.0,   "min": 0,   "max": 10, "step": 0.1, "desc": "Pendulum 4 freq (0=off)"},
            "amp4":   {"type": "float", "default": 0.0,   "min": 0,   "max": 200, "desc": "Pendulum 4 amp"},
            "end_amp4": {"type": "float", "default": 0.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp4"},
            "phase4": {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Pendulum 4 phase°"},
            "decay4": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 4 decay"},
            "duration": {"type": "float", "default": 60.0, "min": 10, "max": 200, "desc": "Simulation duration"},
            "cycles":   {"type": "float", "default": 1.0,  "min": 1, "max": 10, "step": 1, "desc": "Repetitions"},
            # The presets predate the recipes and override the pendulums
            # above; kept readable for old files, not offered.
            "preset":    {"type": "str",   "default": "", "desc": "Legacy preset", "hidden": True},
            "base_freq": {"type": "float", "default": 2.0, "min": 0.1, "max": 10, "desc": "Rotary preset base", "hidden": True},
            "detune":    {"type": "float", "default": 0.01, "min": 0, "max": 1, "desc": "Rotary preset detune", "hidden": True},
        },
    },
    "lissajous": {
        "category": "generator",
        "label": "Lissajous",
        "desc": "Oscilloscope-style frequency ratio patterns",
        "params": {
            "freq_x":          {"type": "int",   "default": 3,    "min": 1, "max": 12, "desc": "X frequency"},
            "freq_y":          {"type": "int",   "default": 2,    "min": 1, "max": 12, "desc": "Y frequency"},
            "amplitude_x":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "X amplitude"},
            "end_amplitude_x": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "amplitude_x"},
            "amplitude_y":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "Y amplitude"},
            "end_amplitude_y": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "amplitude_y"},
            "phase":           {"type": "float", "default": 90.0, "min": 0, "max": 360, "desc": "Phase offset°"},
            "end_phase":       {"type": "float", "default": 90.0, "min": 0, "max": 360, "desc": "End value", "drift_for": "phase"},
            "cycles":          {"type": "float", "default": 0,    "min": 0, "max": 20, "step": 1, "desc": "Cycles (0=auto)"},
        },
    },
    "rose": {
        "category": "generator",
        "label": "Rose Curve",
        "desc": "Rhodonea petal patterns: r = cos(k·θ)",
        "params": {
            "k_num":      {"type": "int",   "default": 3,    "min": 1, "max": 12, "desc": "k numerator"},
            "k_den":      {"type": "int",   "default": 1,    "min": 1, "max": 8,  "desc": "k denominator"},
            "radius":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "Petal radius"},
            "end_radius": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "radius"},
            "cycles":     {"type": "float", "default": 0,    "min": 0, "max": 20, "step": 1, "desc": "Cycles (0=auto)"},
        },
    },
    "circle": {
        "category": "generator",
        "label": "Circle",
        "desc": "Simple circle with optional animation",
        "params": {
            "radius":     {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "Radius"},
            "end_radius": {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "radius"},
            "lobe":       {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Lobe \u00b1"},
            "lobe_n":     {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Lobes per rev"},
            "cycles":     {"type": "float", "default": 1.0,  "min": 1,  "max": 500, "step": 1, "desc": "Repetitions"},
        },
    },
    "polygon": {
        "category": "generator",
        "label": "Polygon",
        "desc": "Regular polygon (triangle, square, hex, ...)",
        "params": {
            "sides":      {"type": "int",   "default": 5,    "min": 3, "max": 20, "desc": "Number of sides"},
            "radius":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "Radius"},
            "end_radius": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "radius"},
            "lobe":       {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Lobe \u00b1"},
            "lobe_n":     {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Lobes per rev"},
            "cycles":     {"type": "float", "default": 1.0,  "min": 1, "max": 50, "step": 1, "desc": "Repetitions"},
            "rotation":       {"type": "float", "default": 0.0,  "min": 0, "max": 360, "desc": "Rotation°"},
            "end_rotation":   {"type": "float", "default": 0.0,  "min": 0, "max": 360, "desc": "End value", "drift_for": "rotation"},
        },
    },
    "star_shape": {
        "category": "generator",
        "label": "Star",
        "desc": "Pointed star with inner/outer vertices",
        "params": {
            "points":           {"type": "int",   "default": 5,    "min": 3,  "max": 20, "desc": "Points"},
            "outer_radius":     {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "Outer radius"},
            "end_outer_radius": {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "outer_radius"},
            "inner_radius":     {"type": "float", "default": 19.1, "min": 1,  "max": 200, "desc": "Inner radius"},
            "end_inner_radius": {"type": "float", "default": 19.1, "min": 1,  "max": 200, "desc": "End value", "drift_for": "inner_radius"},
            "lobe":             {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Lobe \u00b1"},
            "lobe_n":           {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Lobes per rev"},
            "cycles":           {"type": "float", "default": 1.0,  "min": 1,  "max": 50, "step": 1, "desc": "Repetitions"},
            "rotation":         {"type": "float", "default": -90,  "min": -180, "max": 180, "desc": "Rotation°"},
            "end_rotation":     {"type": "float", "default": -90,  "min": -180, "max": 180, "desc": "End value", "drift_for": "rotation"},
        },
    },
    "spiral_shape": {
        "category": "generator",
        "label": "Spiral",
        "desc": "Archimedean spiral (linear radius growth)",
        "params": {
            "start_radius":     {"type": "float", "default": 0.0,  "min": 0, "max": 100, "desc": "Start radius"},
            "end_start_radius": {"type": "float", "default": 0.0,  "min": 0, "max": 100, "desc": "End value", "drift_for": "start_radius"},
            "end_radius":       {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End radius"},
            "end_end_radius":   {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "end_radius"},
            "turns":            {"type": "float", "default": 3.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Turns"},
            "direction":        {"type": "choice", "choices": [1, -1], "default": 1, "desc": "Winding (1 anticlockwise, -1 clockwise)", "advanced": True},
            "lobe":             {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Lobe \u00b1"},
            "lobe_n":           {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Lobes per rev"},
            "cycles":           {"type": "float", "default": 1.0,  "min": 1, "max": 10, "step": 1, "desc": "Repetitions"},
        },
    },
    "geneva": {
        "category": "generator",
        "label": "Geneva",
        "desc": "Geneva mechanism \u2014 intermittent stepped rotation with dwells",
        "params": {
            "slots":     {"type": "int",   "default": 4,    "min": 3,   "max": 8,   "desc": "Slots"},
            "radius":    {"type": "float", "default": 80.0, "min": 10,  "max": 200, "desc": "Radius"},
            "pin_ratio": {"type": "float", "default": 0.7,  "min": 0.1, "max": 1.0, "step": 0.05, "desc": "Pin position"},
            "dwell":     {"type": "float", "default": 0.5,  "min": 0.1, "max": 0.9, "step": 0.05, "desc": "Dwell ratio"},
            "depth":     {"type": "float", "default": 0.4,  "min": 0.0, "max": 1.0, "step": 0.05, "desc": "Transition depth"},
            "cycles":    {"type": "float", "default": 1.0,  "min": 1,   "max": 50,  "step": 1, "desc": "Cycles"},
        },
    },
    "guilloche": {
        "category": "generator",
        "label": "Guilloche",
        "desc": "Engine-turning pattern (banknote/certificate style)",
        "params": {
            "inner":     {"type": "float", "default": 60.0,  "min": 5,   "max": 200, "desc": "Inner radius"},
            "end_inner": {"type": "float", "default": 60.0,  "min": 5,   "max": 200, "desc": "End value", "drift_for": "inner"},
            "outer":     {"type": "float", "default": 180.0, "min": 20,  "max": 400, "desc": "Outer radius"},
            "end_outer": {"type": "float", "default": 180.0, "min": 20,  "max": 400, "desc": "End value", "drift_for": "outer"},
            "nodes":     {"type": "float", "default": 120.0, "min": 10,  "max": 300, "desc": "Wave oscillations"},
            "end_nodes": {"type": "float", "default": 120.0, "min": 10,  "max": 300, "desc": "End value", "drift_for": "nodes"},
            "div":       {"type": "int",   "default": 37,    "min": 7,   "max": 97,  "desc": "Overlap (use primes)"},
            "n0":        {"type": "float", "default": 6.0,   "min": 0,   "max": 30,  "desc": "Inner envelope waves"},
            "h0":        {"type": "float", "default": 10.0,  "min": 0,   "max": 50,  "desc": "Inner envelope amp"},
            "n1":        {"type": "float", "default": 12.0,  "min": 0,   "max": 30,  "desc": "Outer envelope waves"},
            "h1":        {"type": "float", "default": 15.0,  "min": 0,   "max": 50,  "desc": "Outer envelope amp"},
            "cycles":    {"type": "float", "default": 1.0,   "min": 1,   "max": 10,  "step": 1, "desc": "Cycles"},
        },
    },
    "pintograph": {
        "category": "generator",
        "label": "Pintograph",
        "desc": "Two cranks, two rods, the pen where the rods meet — the two-disc drawing machine",
        "params": {
            "spacing":      {"type": "float", "default": 200.0, "min": 10, "max": 600, "desc": "Crank spacing"},
            "radius_1":     {"type": "float", "default": 60.0,  "min": 1,  "max": 300, "desc": "Crank 1 radius"},
            "end_radius_1": {"type": "float", "default": 60.0,  "min": 1,  "max": 300, "desc": "End value", "drift_for": "radius_1"},
            "radius_2":     {"type": "float", "default": 45.0,  "min": 1,  "max": 300, "desc": "Crank 2 radius"},
            "end_radius_2": {"type": "float", "default": 45.0,  "min": 1,  "max": 300, "desc": "End value", "drift_for": "radius_2"},
            "turns_1":      {"type": "float", "default": 7.0,   "min": 0.1, "max": 200, "step": 0.5, "desc": "Crank 1 turns"},
            "turns_2":      {"type": "float", "default": 5.0,   "min": 0.1, "max": 200, "step": 0.5, "desc": "Crank 2 turns"},
            "phase_1":      {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Crank 1 start°", "advanced": True},
            "phase_2":      {"type": "float", "default": 90.0,  "min": 0,  "max": 360, "desc": "Crank 2 start°", "advanced": True},
            "arm_1":        {"type": "float", "default": 180.0, "min": 10, "max": 800, "desc": "Rod 1 length"},
            "arm_2":        {"type": "float", "default": 180.0, "min": 10, "max": 800, "desc": "Rod 2 length"},
            "elbow":        {"type": "choice", "choices": [1, -1], "default": 1, "desc": "Elbow up (1) or down (-1)", "advanced": True},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 50, "step": 1, "desc": "Repetitions"},
        },
    },
    "tempo": {
        "category": "clock",
        "label": "Tempo",
        "desc": "Re-clock everything after it: backwards, there and back, in steps, faster, offset, eased",
        "params": {
            "mode":  {"type": "choice", "choices": ["pingpong", "reverse", "stutter", "speed", "offset", "ease"], "default": "pingpong", "desc": "How"},
            "rate":  {"type": "float", "default": 2.0, "min": 0.1, "max": 50, "step": 0.5, "desc": "Times over (speed)", "when": "speed"},
            "steps": {"type": "int",   "default": 8,   "min": 1,   "max": 200, "desc": "Stops (stutter)", "when": "stutter"},
            "dwell": {"type": "float", "default": 0.5, "min": 0,   "max": 0.95, "step": 0.05, "desc": "Time stopped (stutter)", "when": "stutter"},
            "phase": {"type": "float", "default": 0.25, "min": 0,  "max": 1, "step": 0.05, "desc": "Start ahead by (offset)", "when": "offset"},
            "curve": {"type": "choice", "choices": EASING_MODES, "default": "ease_in_out", "desc": "Curve (ease)", "when": "ease"},
        },
    },
    "rotation": {
        "category": "transform",
        "label": "Rotation",
        "desc": "Spin pattern around center as it draws",
        "params": {
            "total_degrees": {"type": "float", "default": 360.0, "min": -3600, "max": 3600, "desc": "Total rotation°"},
            "origin_x":      {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Origin X"},
            "origin_y":      {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Origin Y"},
            "normalize":     {"type": "bool",  "default": True,   "desc": "Normalize timing"},
        },
    },
    "oscillating_rotation": {
        "category": "transform",
        "label": "Rocking",
        "desc": "Rock the pattern back and forth about a centre, like a pendulum",
        "params": {
            "amplitude_degrees":    {"type": "float", "default": 45.0, "min": 0, "max": 360, "desc": "Swing each way°"},
            "oscillations":         {"type": "float", "default": 1.0,  "min": 0.5, "max": 100, "step": 0.5, "desc": "Swings over the draw"},
            "rotate_around_origin": {"type": "bool",  "default": True,  "desc": "About the origin", "advanced": True},
            **_CENTER,
            **_NORMALIZE,
        },
    },
    "scale": {
        "category": "transform",
        "label": "Scale",
        "desc": "Grow/shrink pattern over time",
        "params": {
            "start_scale": {"type": "float", "default": 1.0, "min": 0.01, "max": 5, "step": 0.1, "desc": "Start scale"},
            "end_scale":   {"type": "float", "default": 1.0, "min": 0.01, "max": 5, "step": 0.1, "desc": "End value", "drift_for": "start_scale"},
            **_ORIGIN,
            "normalize":   {"type": "bool",  "default": True, "desc": "Normalize timing"},
        },
    },
    "translation": {
        "category": "path",
        "label": "Translation",
        "desc": "Slide pattern along a line as it draws",
        "params": {
            "start_x":  {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Start X"},
            "end_x":    {"type": "float", "default": 100.0, "min": -200, "max": 200, "desc": "End value", "drift_for": "start_x"},
            "start_y":  {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Start Y"},
            "end_y":    {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "End value", "drift_for": "start_y"},
            "normalize": {"type": "bool", "default": True,  "desc": "Normalize timing"},
        },
    },
    "arc": {
        "category": "path",
        "label": "Arc Path",
        "desc": "Slide pattern along circular arc",
        "params": {
            "radius":      {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Arc radius"},
            "start_angle": {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Start angle°"},
            "sweep_angle": {"type": "float", "default": 180.0, "min": 10, "max": 720, "desc": "Sweep°"},
            "cycles":      {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_CENTER,
            "normalize":   {"type": "bool",  "default": True,  "desc": "Normalize timing"},
        },
    },
    "spiral_arc": {
        "category": "path",
        "label": "Spiral Path",
        "desc": "Slide pattern along spiral path",
        "params": {
            "inner_radius": {"type": "float", "default": 20.0,  "min": 0,  "max": 200, "desc": "Inner radius"},
            "outer_radius": {"type": "float", "default": 160.0, "min": 10, "max": 300, "desc": "Outer radius"},
            "start_angle":  {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Start angle°"},
            "sweep_angle":  {"type": "float", "default": 720.0, "min": 10, "max": 2880, "desc": "Sweep°"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_CENTER,
            "normalize":    {"type": "bool",  "default": True,   "desc": "Normalize timing"},
        },
    },
    "rail_slide": {
        "category": "path",
        "label": "Rail Slide",
        "desc": "Slide pattern back and forth along a straight rail",
        "params": {
            "rail_length": {"type": "float", "default": 200.0, "min": 10, "max": 500, "desc": "Rail length"},
            "passes":      {"type": "int",   "default": 2,     "min": 1,  "max": 20, "desc": "Passes (odd ones return)"},
            "rail_angle":  {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Rail angle"},
            "cycles":      {"type": "float", "default": 1.0,   "min": 1,  "max": 20, "step": 1, "desc": "Cycles"},
            "scale":       {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale", "advanced": True},
            "gear_teeth":  {"type": "int",   "default": 40,    "min": 5,  "max": 100, "desc": "Gear teeth", "hidden": True},
            "tooth_pitch": {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "desc": "Tooth pitch", "hidden": True},
        },
    },
    "torus": {
        "category": "generator",
        "label": "Torus",
        "desc": "3D torus (donut shape)",
        "params": {
            "surface":      {"type": "str", "default": "torus", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Tube radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_UV,
            "twists":       {"type": "float", "default": 0.0, "min": 0, "max": 8, "desc": "Unused for this surface", "hidden": True},
            "width":        {"type": "float", "default": 60.0, "min": 5, "max": 200, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Unused for this surface", "hidden": True},
        },
        "_module": "surface",
    },
    "mobius": {
        "category": "generator",
        "label": "Mobius Strip",
        "desc": "Single-sided twisted strip",
        "params": {
            "surface":      {"type": "str", "default": "mobius", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "width":        {"type": "float", "default": 60.0,  "min": 5,  "max": 200, "desc": "Strip width"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 30.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 15.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_UV,
            "twists":       {"type": "float", "default": 0.0, "min": 0, "max": 8, "desc": "Unused for this surface", "hidden": True},
            "minor_radius": {"type": "float", "default": 40.0, "min": 5, "max": 150, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Unused for this surface", "hidden": True},
        },
        "_module": "surface",
    },
    "klein_bottle": {
        "category": "generator",
        "label": "Klein Bottle",
        "desc": "Non-orientable surface (self-intersecting)",
        "params": {
            "surface":      {"type": "str", "default": "klein", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Body radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Neck radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 30.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_UV,
            "twists":       {"type": "float", "default": 0.0, "min": 0, "max": 8, "desc": "Unused for this surface", "hidden": True},
            "width":        {"type": "float", "default": 60.0, "min": 5, "max": 200, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Unused for this surface", "hidden": True},
        },
        "_module": "surface",
    },
    "sphere": {
        "category": "generator",
        "label": "Sphere",
        "desc": "3D sphere wireframe",
        "params": {
            "surface":      {"type": "str", "default": "sphere", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_VIEW,
            **_UV,
            "twists":       {"type": "float", "default": 0.0, "min": 0, "max": 8, "desc": "Unused for this surface", "hidden": True},
            "minor_radius": {"type": "float", "default": 40.0, "min": 5, "max": 150, "desc": "Unused for this surface", "hidden": True},
            "width":        {"type": "float", "default": 60.0, "min": 5, "max": 200, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Unused for this surface", "hidden": True},
        },
        "_module": "surface",
    },
    "figure8": {
        "category": "generator",
        "label": "Figure-8 Torus",
        "desc": "Self-intersecting figure-8 torus",
        "params": {
            "surface":      {"type": "str", "default": "figure8", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Tube radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_UV,
            "twists":       {"type": "float", "default": 0.0, "min": 0, "max": 8, "desc": "Unused for this surface", "hidden": True},
            "width":        {"type": "float", "default": 60.0, "min": 5, "max": 200, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Unused for this surface", "hidden": True},
        },
        "_module": "surface",
    },
    "ribbon": {
        "category": "generator",
        "label": "Twisted Ribbon",
        "desc": "Ribbon with configurable twists",
        "params": {
            "surface":      {"type": "str", "default": "ribbon", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "width":        {"type": "float", "default": 60.0,  "min": 5,  "max": 200, "desc": "Ribbon width"},
            "twists":       {"type": "float", "default": 2.0,   "min": 0,  "max": 8, "step": 0.5, "desc": "Half-twists"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 25.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 10.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            **_UV,
            "minor_radius": {"type": "float", "default": 40.0, "min": 5, "max": 150, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Unused for this surface", "hidden": True},
        },
        "_module": "surface",
    },
    "helix_ribbon": {
        "category": "generator",
        "label": "Helix Ribbon",
        "desc": "Rising helical ribbon",
        "params": {
            "surface":      {"type": "str", "default": "helix_ribbon", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Helix radius"},
            "width":        {"type": "float", "default": 40.0,  "min": 5,  "max": 200, "desc": "Ribbon width"},
            "twists":       {"type": "float", "default": 1.0,   "min": 0,  "max": 8, "step": 0.5, "desc": "Half-twists"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 30.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 15.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            "pitch":        {"type": "float", "default": 50.0, "min": 0, "max": 300, "desc": "Rise per turn"},
            **_UV,
            "minor_radius": {"type": "float", "default": 40.0, "min": 5, "max": 150, "desc": "Unused for this surface", "hidden": True},
            "length":       {"type": "float", "default": 200.0, "min": 1, "max": 500, "desc": "Unused", "hidden": True},
        },
        "_module": "surface",
    },
    "line": {
        "category": "generator",
        "label": "Line",
        "desc": "Straight lines with timing control",
        "params": {
            "length":      {"type": "float", "default": 100.0, "min": 1,   "max": 500, "desc": "Length"},
            "end_length":  {"type": "float", "default": 100.0, "min": 1,   "max": 500, "desc": "End value", "drift_for": "length"},
            "cycles":      {"type": "float", "default": 1.0,   "min": 1,   "max": 50, "step": 1, "desc": "Cycles"},
            "stroke_time": {"type": "float", "default": 1.0,   "min": 0.01, "max": 1, "step": 0.01, "desc": "Stroke time (0-1)"},
            "rotation":    {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Direction°"},
            "idle_at":     {"type": "choice", "choices": ["start", "end"], "default": "start", "desc": "Where the pen waits", "advanced": True},
            "start_x":     {"type": "float", "default": 0.0,   "min": -300, "max": 300, "desc": "Start X", "advanced": True},
            "start_y":     {"type": "float", "default": 0.0,   "min": -300, "max": 300, "desc": "Start Y", "advanced": True},
            "end_x":       {"type": "float", "default": 0.0,   "min": -300, "max": 300, "desc": "End X (0,0 = use length and direction)", "advanced": True},
            "end_y":       {"type": "float", "default": 0.0,   "min": -300, "max": 300, "desc": "End Y", "advanced": True},
        },
    },
    "ellipse": {
        "category": "generator",
        "label": "Ellipse",
        "desc": "Oval with independent X/Y radii",
        "params": {
            "radius_x":     {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "Radius X"},
            "end_radius_x": {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "radius_x"},
            "radius_y":     {"type": "float", "default": 30.0, "min": 5,  "max": 200, "desc": "Radius Y"},
            "end_radius_y": {"type": "float", "default": 30.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "radius_y"},
            "rotation":     {"type": "float", "default": 0.0,  "min": 0,  "max": 360, "desc": "Rotation"},
            "end_rotation": {"type": "float", "default": 0.0,  "min": 0,  "max": 360, "desc": "End value", "drift_for": "rotation"},
            "lobe":         {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Lobe \u00b1"},
            "lobe_n":       {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Lobes per rev"},
            "decay":        {"type": "float", "default": 0.0,  "min": 0,  "max": 2, "step": 0.05, "desc": "Shrink per cycle"},
            "cycles":       {"type": "float", "default": 1.0,  "min": 1,  "max": 500, "step": 1, "desc": "Cycles"},
        },
    },
    "rack": {
        "category": "generator",
        "label": "Rack",
        "desc": "Gear rolling around stadium-shaped track",
        "params": {
            "straight_teeth": {"type": "int",   "default": 50,   "min": 5,  "max": 200, "desc": "Straight teeth"},
            "end_teeth":      {"type": "int",   "default": 24,   "min": 5,  "max": 100, "desc": "End curve teeth"},
            "gear_teeth":     {"type": "int",   "default": 24,   "min": 5,  "max": 100, "desc": "Gear teeth"},
            "tooth_pitch":    {"type": "float", "default": 2.0,  "min": 0.1, "max": 5, "step": 0.1, "desc": "Tooth pitch"},
            "hole_position":  {"type": "float", "default": 0.75, "min": 0, "max": 1.5, "step": 0.05, "desc": "Pen hole"},
            "end_hole_position": {"type": "float", "default": 0.75, "min": 0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "laps":           {"type": "int",   "default": 1,    "min": 1, "max": 20, "desc": "Laps"},
            "cycles":         {"type": "float", "default": 1.0,  "min": 1, "max": 20, "step": 1, "desc": "Cycles"},
            "scale":          {"type": "float", "default": 1.0,  "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
        },
    },
    "spirograph_rail": {
        "category": "generator",
        "label": "Rail",
        "desc": "Gear rolling along linear rail",
        "params": {
            "rail_length":   {"type": "float", "default": 200.0, "min": 10, "max": 500, "desc": "Rail length"},
            "gear_teeth":    {"type": "int",   "default": 40,    "min": 5,  "max": 100, "desc": "Gear teeth"},
            "tooth_pitch":   {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Tooth pitch"},
            "hole_position": {"type": "float", "default": 0.6,   "min": 0, "max": 1.5, "step": 0.05, "desc": "Pen hole"},
            "end_hole_position": {"type": "float", "default": 0.6, "min": 0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "passes":        {"type": "int",   "default": 2,     "min": 1, "max": 20, "desc": "Passes"},
            "cycles":        {"type": "float", "default": 1.0,   "min": 1, "max": 20, "step": 1, "desc": "Cycles"},
            "rail_angle":    {"type": "float", "default": 0.0,   "min": 0, "max": 360, "desc": "Rail angle"},
            "scale":         {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale", "advanced": True},
        },
    },
    "bend": {
        "category": "transform",
        "label": "Bend",
        "desc": "Wrap flat pattern into arc (X to angle, Y to radius)",
        "params": {
            "radius":      {"type": "float", "default": 200.0, "min": 10,  "max": 500, "desc": "Bend radius"},
            "start_angle": {"type": "float", "default": 0.0,   "min": -180, "max": 360, "desc": "Start angle"},
            "sweep_angle": {"type": "float", "default": 90.0,  "min": 10,  "max": 720, "desc": "Sweep"},
            "direction":   {"type": "choice", "choices": [1, -1], "default": 1, "desc": "Y outward (1) or inward (-1)", "advanced": True},
            "x_range":     {"type": "float", "default": 0.0,   "min": 0,   "max": 2000, "desc": "X span that fills the sweep (0 = radius × sweep)", "advanced": True},
            **_CENTER,
        },
    },
    "damping": {
        "category": "transform",
        "label": "Damping",
        "desc": "Exponential decay toward center",
        "params": {
            "decay_rate":     {"type": "float", "default": 0.02, "min": 0, "max": 0.2, "step": 0.005, "desc": "Decay rate"},
            "end_decay_rate": {"type": "float", "default": 0.02, "min": 0, "max": 0.2, "step": 0.005, "desc": "End value", "drift_for": "decay_rate"},
            "duration":       {"type": "float", "default": 60.0, "min": 1, "max": 200, "desc": "Duration"},
            **_ORIGIN,
            **_NORMALIZE,
        },
    },
    "noise": {
        "category": "transform",
        "label": "Noise",
        "desc": "Smooth random perturbation (hand-drawn look)",
        "params": {
            "amplitude":     {"type": "float", "default": 5.0,  "min": 0.1, "max": 50, "desc": "Amplitude"},
            "end_amplitude": {"type": "float", "default": 5.0,  "min": 0,   "max": 50, "desc": "End value", "drift_for": "amplitude"},
            "frequency":     {"type": "float", "default": 50.0, "min": 1,   "max": 500, "desc": "Frequency"},
            "seed":          {"type": "int",   "default": 42,   "min": 0,   "max": 9999, "desc": "Seed"},
            "mode":          {"type": "choice", "choices": ["radial", "xy"], "default": "radial", "desc": "Radial (bumpy edge) or xy (shaky hand)"},
            **_NORMALIZE,
        },
    },
    "stretch": {
        "category": "transform",
        "label": "Stretch",
        "desc": "Non-uniform X/Y scaling — elongate along either axis",
        "params": {
            "scale_x":     {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "X scale"},
            "end_scale_x": {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "End value", "drift_for": "scale_x"},
            "scale_y":     {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "Y scale"},
            "end_scale_y": {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "End value", "drift_for": "scale_y"},
            **_ORIGIN,
            **_NORMALIZE,
        },
    },
}


# A few UI type names are views onto one implementation module: every surface
# is `surface.py` picking a different parametrisation. The INI writer maps them
# back on the way out.
TYPE_TO_MODULE = {
    "torus": "surface", "mobius": "surface", "klein_bottle": "surface",
    "sphere": "surface", "figure8": "surface", "ribbon": "surface",
    "helix_ribbon": "surface",
}


# Keys that changed name. Applied when a file is read, so a pattern saved
# under the old spelling still draws what it drew — rather than the module
# quietly reading its default, which is what happened to every file that
# said `sweep` after the rename to `lobe`.
RENAMED_KEYS = {
    "sweep": "lobe", "sweep_n": "lobe_n",
    "end_sweep": "end_lobe",
}


def modernise(params):
    """A params dict with every renamed key spelled the current way."""
    return {RENAMED_KEYS.get(key, key): value for key, value in params.items()}


def module_names(category=None):
    """Every module type, optionally just the generators or just the transforms."""
    return [name for name, spec in MODULE_DEFS.items()
            if category is None or spec["category"] == category]


def defaults_for(module_type):
    """A fresh parameter dict for a module, ready to be edited.

    Hidden parameters are left out unless they carry the module's identity
    (a surface's ``surface`` key): a file should say what was chosen, not
    restate every default the module has."""
    spec = MODULE_DEFS.get(module_type)
    if not spec:
        raise KeyError("unknown module type: %s" % module_type)
    params = {"type": module_type}
    for name, p in spec["params"].items():
        if p.get("hidden") and name != "surface":
            continue
        params[name] = p["default"]
    return params


def drift_bases(module_type):
    """The parameters of a module that have an ``end_`` twin — the ones that
    may also carry ``osc_<name>``."""
    spec = MODULE_DEFS[module_type]
    return {p["drift_for"] for p in spec["params"].values() if "drift_for" in p}


def valid_keys(module_type):
    """Every key a module's INI section may hold, or None for an unknown type."""
    spec = MODULE_DEFS.get(module_type)
    if not spec:
        return None
    keys = {"type"} | set(spec["params"]) | set(COMMON_PARAMS)
    keys |= {OSC_PREFIX + base for base in drift_bases(module_type)}
    if spec["category"] == "transform":
        keys |= set(TRANSFORM_PARAMS)
    return keys


def is_arm(module_type):
    """Does this module add a vector — a generator or a path?"""
    return MODULE_DEFS[module_type]["category"] in ("generator", "path")


def finishing_keys(section):
    """Every key a finishing section may hold, or None for an unknown one."""
    spec = FINISHING_DEFS.get(section)
    return {"type"} | set(spec["params"]) if spec else None


def by_module_file():
    """UI type names grouped by the Python module that implements them."""
    out = {}
    for name in MODULE_DEFS:
        out.setdefault(TYPE_TO_MODULE.get(name, name), []).append(name)
    return out
