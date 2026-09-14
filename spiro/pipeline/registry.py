"""What modules exist, what knobs they have, and what those knobs mean.

Pure data. The UI builds its palette and its parameter editors from this, the
INI writer validates against it, and nothing here imports anything — which is
why the same table can serve a Qt panel, a web page and a test.

Each entry is ``type -> {category, label, desc, params}``; each parameter is
``name -> {type, default, min, max, step, desc}``. A parameter carrying
``drift_for`` is the *end* value of another parameter: the pipeline interpolates
from the base value to this one over the course of the draw.
"""

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
            "hole_position":     {"type": "float", "default": 0.7,  "min": 0.0, "max": 1.5, "step": 0.05, "desc": "Pen hole (0=center, 1=edge)"},
            "end_hole_position": {"type": "float", "default": 0.7,  "min": 0.0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "inside":            {"type": "bool",  "default": True,  "desc": "Inside (hypo) vs outside (epi)"},
            "cycles":            {"type": "float", "default": 1.0,  "min": 1,   "max": 50, "step": 1, "desc": "Repetitions"},
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
            "duration": {"type": "float", "default": 60.0, "min": 10, "max": 200, "desc": "Simulation duration"},
            "cycles":   {"type": "float", "default": 1.0,  "min": 1, "max": 10, "step": 1, "desc": "Repetitions"},
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
    "rotation": {
        "category": "transform",
        "label": "Rotation",
        "desc": "Spin pattern around center as it draws",
        "params": {
            "total_degrees": {"type": "float", "default": 360.0, "min": 0, "max": 3600, "desc": "Total rotation°"},
            "origin_x":      {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Origin X"},
            "origin_y":      {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Origin Y"},
            "normalize":     {"type": "bool",  "default": True,   "desc": "Normalize timing"},
        },
    },
    "scale": {
        "category": "transform",
        "label": "Scale",
        "desc": "Grow/shrink pattern over time",
        "params": {
            "start_scale": {"type": "float", "default": 1.0, "min": 0.01, "max": 5, "step": 0.1, "desc": "Start scale"},
            "end_scale":   {"type": "float", "default": 1.0, "min": 0.01, "max": 5, "step": 0.1, "desc": "End value", "drift_for": "start_scale"},
            "normalize":   {"type": "bool",  "default": True, "desc": "Normalize timing"},
        },
    },
    "translation": {
        "category": "transform",
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
        "category": "transform",
        "label": "Arc Path",
        "desc": "Slide pattern along circular arc",
        "params": {
            "radius":      {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Arc radius"},
            "start_angle": {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Start angle°"},
            "sweep_angle": {"type": "float", "default": 180.0, "min": 10, "max": 720, "desc": "Sweep°"},
            "cycles":      {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            "normalize":   {"type": "bool",  "default": True,  "desc": "Normalize timing"},
        },
    },
    "spiral_arc": {
        "category": "transform",
        "label": "Spiral Path",
        "desc": "Slide pattern along spiral path",
        "params": {
            "inner_radius": {"type": "float", "default": 20.0,  "min": 0,  "max": 200, "desc": "Inner radius"},
            "outer_radius": {"type": "float", "default": 160.0, "min": 10, "max": 300, "desc": "Outer radius"},
            "start_angle":  {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Start angle°"},
            "sweep_angle":  {"type": "float", "default": 720.0, "min": 10, "max": 2880, "desc": "Sweep°"},
            "normalize":    {"type": "bool",  "default": True,   "desc": "Normalize timing"},
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
            "rotation":    {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Direction"},
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


def module_names(category=None):
    """Every module type, optionally just the generators or just the transforms."""
    return [name for name, spec in MODULE_DEFS.items()
            if category is None or spec["category"] == category]


def defaults_for(module_type):
    """A fresh parameter dict for a module, ready to be edited."""
    spec = MODULE_DEFS.get(module_type)
    if not spec:
        raise KeyError("unknown module type: %s" % module_type)
    params = {"type": module_type}
    for name, p in spec["params"].items():
        params[name] = p["default"]
    return params
