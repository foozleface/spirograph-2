"""The four kinds of step, and how the window shows them.

One vocabulary for the whole window, so a colour means the same thing in
the step strip, the gallery, the machine overlay and the parameter panel:

    arm     amber   adds a moving arm; the pen rides the last one
    path    teal    carries the whole mechanism along a track
    move    violet  the table moves under what is drawn
    clock   grey    re-times the steps after it

The words are chosen for someone with a drawing machine in mind rather
than a compositor: an arm is an arm, a table move is what happens when
the paper turns.
"""

from PySide6.QtGui import QColor

from spiro.pipeline.registry import CATEGORIES, MODULE_DEFS

KIND_COLORS = {
    "generator": QColor("#e0a437"),   # amber — brass arms
    "path":      QColor("#3fb8b0"),   # teal — the carriage rail
    "transform": QColor("#9b7cf6"),   # violet — the table
    "clock":     QColor("#9aa0ad"),   # grey — the clock
    "finish":    QColor("#7fb069"),   # green — after the ink is dry
}

KIND_GLYPHS = {
    "generator": "⟲",
    "path":      "⤳",
    "transform": "⟳",
    "clock":     "⏱",
    "finish":    "✦",
}

# What each kind does, in one line, for tooltips and the legend.
KIND_WORDS = {
    "generator": ("Arm", "adds a moving arm — the pen rides the last one"),
    "path":      ("Carriage path", "carries the whole mechanism along a track"),
    "transform": ("Table move", "moves the paper under what is drawn so far"),
    "clock":     ("Clock", "re-times every step after it"),
    "finish":    ("Finishing", "after the ink is dry: copies, strokes, a window"),
}

# One line per module, the way a person at the machine would say it. Falls
# back to the registry's description for anything not listed.
PLAIN_WORDS = {
    "circle":          "an arm going round — stack two for an epicycle",
    "ellipse":         "an arm sweeping an oval",
    "polygon":         "an arm tracing straight sides",
    "star_shape":      "an arm tracing points in and out",
    "spiral_shape":    "an arm winding outward",
    "rose":            "petals: an arm whose reach pulses as it turns",
    "lissajous":       "two pendulums crossed — the oscilloscope figure",
    "harmonograph":    "swinging pendulums, dying away",
    "spirograph_gear": "a wheel rolling inside (or around) a ring — the toy",
    "spirograph_rail": "a wheel rolling along a straight rack",
    "rack":            "a wheel rolling around a stadium track",
    "geneva":          "stop, snap, stop — the Maltese-cross mechanism",
    "guilloche":       "engine-turned banknote lace",
    "pintograph":      "two cranks, two rods, the pen where they meet",
    "line":            "a stroke, with time for the pen to dwell",
    "torus": "a wire doughnut, seen from an angle",
    "mobius": "a strip with one twist",
    "klein_bottle": "the bottle with no inside",
    "sphere": "a wire globe",
    "figure8": "a doughnut folded through itself",
    "ribbon": "a ribbon with a chosen number of twists",
    "helix_ribbon": "a ribbon climbing a helix",
    "translation":     "slide the whole thing along a line",
    "arc":             "carry the whole thing round an arc",
    "spiral_arc":      "carry the whole thing out along a spiral",
    "rail_slide":      "shuttle the whole thing back and forth",
    "rotation":        "turn the paper as it draws",
    "oscillating_rotation": "rock the paper back and forth",
    "scale":           "grow or shrink the paper as it draws",
    "stretch":         "squash the paper along one axis",
    "damping":         "let the drawing die away toward a centre",
    "bend":            "wrap the paper round a drum",
    "noise":           "a hand that is not quite steady",
    "tempo":           "change the clock for everything below",
}


def kind_of(module_type):
    return MODULE_DEFS[module_type]["category"]


def color_of(module_type):
    return KIND_COLORS[kind_of(module_type)]


def glyph_of(module_type):
    return KIND_GLYPHS[kind_of(module_type)]


def plain(module_type):
    return PLAIN_WORDS.get(module_type) or MODULE_DEFS[module_type].get("desc", "")


def kind_label(kind):
    return CATEGORIES.get(kind, {}).get("label") or KIND_WORDS[kind][0]
