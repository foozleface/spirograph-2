"""The sheet: what is on it, which pen draws what, and the SVG that goes out.

A :class:`Scene` is the document. It owns the paper, the pens, and the placed
items, and it can turn all three into the one artefact the plotter understands:
an SVG in millimetres, each path stroked with the colour of the pen that should
draw it. Splitting that into per-pen layers is :mod:`axiplot.colorsplit`'s job,
which is why the stroke colour is the only thing this file has to get right.

The SVG is written at 1 user unit = 1 mm with the physical size declared in mm,
so no consumer has to guess a DPI. That, plus :meth:`PlacedItem.paths_mm` being
the only geometry, is what makes the preview and the plot the same drawing.
"""

import hashlib
from dataclasses import dataclass, field

from spiro.scene.item import PlacedItem
from spiro.scene.paper import Paper

# A default pen set that stays distinguishable on white paper and in the UI's
# swatches. Deliberately not a rainbow: these are ink colours a person is
# likely to own, in an order that reads as an order.
DEFAULT_PEN_COLORS = [
    ("#000000", "Black"), ("#c0392b", "Red"), ("#1f6fb4", "Blue"),
    ("#1e8449", "Green"), ("#8e44ad", "Purple"), ("#d68910", "Orange"),
    ("#16a085", "Teal"), ("#7f8c8d", "Grey"),
]


@dataclass
class Pen:
    """One nib. ``color`` is both the swatch and the key the SVG is split on,
    so two pens must never share one."""

    color: str = "#000000"
    label: str = "Black"
    include: bool = True

    def to_dict(self):
        return {"color": self.color, "label": self.label, "include": self.include}


def default_pens(n=2):
    return [Pen(color, label) for color, label in DEFAULT_PEN_COLORS[:max(n, 1)]]


@dataclass
class Scene:
    """Paper, pens, and the patterns placed on it."""

    paper: Paper = field(default_factory=Paper)
    pens: list = field(default_factory=lambda: default_pens(2))
    items: list = field(default_factory=list)

    # -- items ---------------------------------------------------------------- #

    def add(self, drawing, name="pattern", pen=None, fraction=0.8, source=None):
        """Place a drawing centred on the paper. ``pen`` defaults to the next
        one that has nothing on it yet, so a second pattern lands on a second
        pen without anyone having to say so."""
        item = PlacedItem.fitted_to(drawing, self.paper, fraction,
                                    name=name, source=source,
                                    pen=self._next_pen() if pen is None else int(pen))
        self.items.append(item)
        return item

    def remove(self, item_id):
        before = len(self.items)
        self.items = [i for i in self.items if i.item_id != item_id]
        return len(self.items) != before

    def find(self, item_id):
        for item in self.items:
            if item.item_id == item_id:
                return item
        return None

    def item_at(self, x_mm, y_mm):
        """The topmost item under a point — last drawn is first hit."""
        for item in reversed(self.items):
            if item.visible and item.contains(x_mm, y_mm):
                return item
        return None

    def _next_pen(self):
        used = {i.pen for i in self.items}
        for index in range(len(self.pens)):
            if index not in used:
                return index
        return 0

    # -- paper ---------------------------------------------------------------- #

    def set_paper(self, paper, rescale=True):
        """Change the sheet. With ``rescale`` the items keep their position and
        size *relative to the paper*, which is what someone switching from A4 to
        A3 means; without it they keep their millimetres."""
        old = self.paper
        self.paper = paper
        if not rescale or not old.width_mm or not old.height_mm:
            return
        fx = paper.width_mm / old.width_mm
        fy = paper.height_mm / old.height_mm
        for item in self.items:
            item.x_mm *= fx
            item.y_mm *= fy
            item.set_width(item.w_mm * min(fx, fy))

    def out_of_bounds(self):
        """Items that reach outside the drawable area — the pen would stall
        against the end of its travel."""
        x0, y0, w, h = self.paper.drawable
        out = []
        for item in self.items:
            if not item.visible:
                continue
            ix0, iy0, ix1, iy1 = item.bounds_mm()
            if ix0 < x0 - 1e-6 or iy0 < y0 - 1e-6 or ix1 > x0 + w + 1e-6 or iy1 > y0 + h + 1e-6:
                out.append(item)
        return out

    # -- pens ------------------------------------------------------------------ #

    def pen_of(self, item):
        index = min(max(item.pen, 0), len(self.pens) - 1) if self.pens else 0
        return self.pens[index] if self.pens else Pen()

    def pens_in_use(self):
        """The pens that actually have something to draw, in pen order."""
        used = {i.pen for i in self.items if i.visible}
        return [(index, pen) for index, pen in enumerate(self.pens)
                if index in used and pen.include]

    def items_for_pen(self, index):
        return [i for i in self.items if i.visible and i.pen == index]

    def ensure_pens(self, n):
        """Grow the pen list to at least n, keeping what is already there."""
        while len(self.pens) < n and len(self.pens) < len(DEFAULT_PEN_COLORS):
            color, label = DEFAULT_PEN_COLORS[len(self.pens)]
            self.pens.append(Pen(color, label))
        return self.pens

    # -- output ----------------------------------------------------------------- #

    def to_svg(self, stroke_width_mm=0.3, background=None, pens=None):
        """The whole sheet as one SVG, in millimetres.

        Paths are stroked with their pen's colour and closed with an explicit
        ``</path>``: both are what :mod:`axiplot.colorsplit` matches on.
        Passing ``pens`` restricts the output to those pen indices.
        """
        w, h = self.paper.width_mm, self.paper.height_mm
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" '
               'width="%gmm" height="%gmm" viewBox="0 0 %g %g">' % (w, h, w, h)]
        if background:
            out.append('<rect x="0" y="0" width="%g" height="%g" fill="%s"/>'
                       % (w, h, background))
        for item in self.items:
            if not item.visible or (pens is not None and item.pen not in pens):
                continue
            color = self.pen_of(item).color
            for path in item.paths_mm():
                if len(path) < 2:
                    continue
                out.append('<path d="%s" fill="none" stroke="%s" '
                           'stroke-width="%g" stroke-linecap="round" '
                           'stroke-linejoin="round"></path>'
                           % (_path_data(path), color, stroke_width_mm))
        out.append('</svg>')
        return "\n".join(out) + "\n"

    def job(self, opts=None, optimizer="auto", vpype=None):
        """The job dict :func:`axiplot.run.plot_job` takes.

        ``mode`` is "color" whenever more than one pen is in use — that is the
        mode that splits the SVG into one layer per pen and stops between them
        for the swap.
        """
        in_use = self.pens_in_use()
        svg = self.to_svg(pens={index for index, _ in in_use} or None)
        return {
            "svg": svg,
            "mode": "color" if len(in_use) > 1 else "mono",
            "pens": [{"color": pen.color, "label": pen.label, "include": True,
                      "order": order} for order, (_, pen) in enumerate(in_use)],
            "paperSize": {"width_mm": self.paper.width_mm,
                          "height_mm": self.paper.height_mm},
            "hash": self.stamp(),
            "opts": opts or {},
            "optimizer": optimizer,
            "vpype": vpype or {},
        }

    def stamp(self):
        """What makes this sheet *this* sheet, for the purposes of "is layer 3
        already on the paper?". Any change to the geometry, the pens or the
        paper gives a different answer."""
        parts = ["%g x %g" % (self.paper.width_mm, self.paper.height_mm)]
        parts += ["pen %s %s %d" % (pen.color, pen.label, pen.include)
                  for pen in self.pens]
        for item in self.items:
            if not item.visible:
                continue
            parts.append("%s|%.4f,%.4f,%.4f,%.4f,%.3f,%d|%s" % (
                item.name, item.x_mm, item.y_mm, item.w_mm, item.h_mm,
                item.rotation_deg, item.pen,
                getattr(item.drawing, "ini_text", "")))
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]

    def summary(self):
        """A line per pen: what it draws and how much of it."""
        rows = []
        for index, pen in self.pens_in_use():
            items = self.items_for_pen(index)
            rows.append({"pen": index, "label": pen.label, "color": pen.color,
                         "items": len(items),
                         "points": sum(i.point_count() for i in items),
                         "names": [i.name for i in items]})
        return rows

    def to_dict(self):
        return {"paper": {"width_mm": self.paper.width_mm,
                          "height_mm": self.paper.height_mm,
                          "margin_mm": self.paper.margin_mm,
                          "label": self.paper.label},
                "pens": [p.to_dict() for p in self.pens],
                "items": [i.to_dict() for i in self.items]}


def _path_data(points):
    """`M x,y L x,y ...` at four decimals — a hundredth of a micron, well past
    what the machine can resolve, and short enough not to bloat the file."""
    parts = ["M %.4f,%.4f" % (points[0].real, points[0].imag)]
    parts += ["L %.4f,%.4f" % (p.real, p.imag) for p in points[1:]]
    return " ".join(parts)
