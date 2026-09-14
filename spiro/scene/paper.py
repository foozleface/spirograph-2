"""Paper and beds, in millimetres.

One unit of length in this program is a millimetre. Not a pixel, not a
percentage of something, not an inch — those are all conversions that happen at
an edge. The AxiDraw table is the exception that proves it: the model numbers
and their travel are what the machine's own options use, so they are kept in
inches exactly as EMS publishes them and converted once, here.
"""

from dataclasses import dataclass

MM_PER_INCH = 25.4

# AxiDraw model id -> the machine's travel, transcribed from
# axidrawinternal's own table (axidraw.py's model switch and the
# x_travel_*/y_travel_* defaults in axidraw_conf.py). The ids ARE
# pyaxidraw's `options.model`, so a wrong row here is a machine clamped to
# the wrong bed.
#
# The old web UI's table had model 4 as the SE/A2. It is the MiniKit — a
# 160 x 102 mm bed against the A2's 594 x 432 — so anything plotted on an
# SE/A2 selected by that name was silently clipped to a sixth of the sheet.
# The SE/A2 is model 6. Model 1 is not in the switch at all; it falls to the
# default travel, which is the A4's, which is what it should be.
AXIDRAW_MODELS = {
    1: {"label": "AxiDraw V2 / V3 / SE A4", "width_in": 11.81, "height_in": 8.58},
    2: {"label": "AxiDraw V3/A3 or SE/A3", "width_in": 16.93, "height_in": 11.69},
    3: {"label": "AxiDraw V3 XLX", "width_in": 23.42, "height_in": 8.58},
    4: {"label": "AxiDraw MiniKit", "width_in": 6.30, "height_in": 4.00},
    5: {"label": "AxiDraw SE/A1", "width_in": 34.02, "height_in": 23.39},
    6: {"label": "AxiDraw SE/A2", "width_in": 23.39, "height_in": 17.01},
    7: {"label": "AxiDraw V3/B6", "width_in": 7.48, "height_in": 5.51},
}

# Sheet sizes worth having in a menu, portrait, in millimetres.
PAPER_PRESETS = {
    "A5": (148.0, 210.0),
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
    "Tabloid": (279.4, 431.8),
}


@dataclass(frozen=True)
class Paper:
    """A rectangle of paper, and how much of it the pen may reach.

    ``margin_mm`` is the border kept clear on every side — the drawable area is
    the rest. Placement is still expressed against the *paper*, because that is
    what a person is looking at; the margin only says where the pen is allowed.
    """

    width_mm: float = 297.0
    height_mm: float = 210.0
    margin_mm: float = 0.0
    label: str = ""

    @classmethod
    def from_axidraw(cls, model, margin_mm=0.0):
        """The travel of an AxiDraw model, as a sheet."""
        spec = AXIDRAW_MODELS.get(int(model))
        if not spec:
            raise KeyError("unknown AxiDraw model: %r" % (model,))
        return cls(round(spec["width_in"] * MM_PER_INCH, 2),
                   round(spec["height_in"] * MM_PER_INCH, 2),
                   margin_mm, spec["label"])

    @classmethod
    def preset(cls, name, landscape=False, margin_mm=0.0):
        w, h = PAPER_PRESETS[name]
        if landscape:
            w, h = h, w
        return cls(w, h, margin_mm, name + (" landscape" if landscape else ""))

    @property
    def drawable(self):
        """(x, y, w, h) of the area inside the margin, in mm."""
        m = self.margin_mm
        return (m, m, max(self.width_mm - 2 * m, 0.0),
                max(self.height_mm - 2 * m, 0.0))

    @property
    def center(self):
        return (self.width_mm / 2, self.height_mm / 2)

    @property
    def aspect(self):
        return self.width_mm / self.height_mm if self.height_mm else 1.0

    def contains(self, x_mm, y_mm):
        """Is this point inside the drawable area?"""
        x0, y0, w, h = self.drawable
        return x0 <= x_mm <= x0 + w and y0 <= y_mm <= y0 + h

    def clamp(self, x_mm, y_mm):
        """The nearest point inside the drawable area."""
        x0, y0, w, h = self.drawable
        return (min(max(x_mm, x0), x0 + w), min(max(y_mm, y0), y0 + h))

    def describe(self):
        size = "%g x %g mm" % (round(self.width_mm, 1), round(self.height_mm, 1))
        return "%s (%s)" % (self.label, size) if self.label else size
