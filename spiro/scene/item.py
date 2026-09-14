"""A drawing placed on the paper: where it sits, how big it is, which pen.

This is the module the old code did not have, and its absence is the whole bug.
Placement used to be a percentage of the paper in the browser and a derived
centre in the plot route, each with its own idea of how big the pattern was —
one fitting to the paper's height, the other to both axes. Whenever the two
aspect ratios differed they disagreed, and dragging moved the item in units
that matched neither.

Here there is one description of a placement, in millimetres:

    the item's box is w_mm x h_mm, its centre is at (x_mm, y_mm), and it is
    turned rotation_deg about that centre.

``w_mm``/``h_mm`` are the pattern's real bounding box on the paper — the aspect
ratio is the drawing's own, kept by construction, so the box is never a lie
about what will be drawn. Everything that needs geometry calls
:meth:`PlacedItem.paths_mm`, and there is nowhere else for a second rule to
hide.
"""

import math
from itertools import count

_ids = count(1)


class PlacedItem:
    """One pattern on the sheet.

    The size is *one* number. ``h_mm`` is stored and ``w_mm`` is derived from
    it through the drawing's own aspect ratio, because the geometry is: the
    curves are placed by scaling a box that is ``aspect`` wide and 1 tall.
    Storing both invites them to disagree — and a width that disagrees with
    the drawn width is a box that lies about what will be plotted. Setting
    either one is fine; both go through the same place.
    """

    def __init__(self, drawing, x_mm=0.0, y_mm=0.0, w_mm=None, h_mm=100.0,
                 rotation_deg=0.0, pen=0, name="pattern", visible=True,
                 item_id=None, source=None):
        self.drawing = drawing              # a spiro.pipeline.Drawing
        self.x_mm = float(x_mm)             # centre of the item's box
        self.y_mm = float(y_mm)
        self.h_mm = float(h_mm)
        if w_mm is not None:                # a width, if that is how you think
            self.set_width(w_mm)
        self.rotation_deg = float(rotation_deg)
        self.pen = int(pen)                 # index into Scene.pens
        self.name = name
        self.visible = bool(visible)
        self.item_id = next(_ids) if item_id is None else item_id
        # Which document produced these curves. Editing that document
        # re-renders the item in place; editing a different one must not,
        # even when the two happen to share a name.
        self.source = source
        self._unit = None                   # the cached curves, see unit_paths

    def __repr__(self):
        return ("PlacedItem(%r, %.1f x %.1f mm at %.1f, %.1f, pen %d)"
                % (self.name, self.w_mm, self.h_mm, self.x_mm, self.y_mm,
                   self.pen))

    # -- construction -------------------------------------------------------- #

    @classmethod
    def fitted_to(cls, drawing, paper, fraction=0.8, **kw):
        """Place a drawing centred on the paper at ``fraction`` of the
        drawable area — the sane default for "add this to the canvas"."""
        _, _, avail_w, avail_h = paper.drawable
        _, h = _box_for(drawing.aspect, avail_w * fraction, avail_h * fraction)
        cx, cy = paper.center
        return cls(drawing=drawing, x_mm=cx, y_mm=cy, h_mm=h, **kw)

    # -- size ---------------------------------------------------------------- #

    @property
    def aspect(self):
        return self.drawing.aspect

    @property
    def w_mm(self):
        """The drawn width. Derived, never stored — see the class docstring."""
        return self.h_mm * self.aspect

    @w_mm.setter
    def w_mm(self, value):
        self.set_width(value)

    def set_width(self, w_mm):
        """Resize by width; the height follows, because the pattern's shape is
        not ours to change."""
        self.h_mm = max(float(w_mm), 0.1) / self.aspect

    def set_height(self, h_mm):
        self.h_mm = max(float(h_mm), 0.1)

    def fit_into(self, w_mm, h_mm):
        """The largest box of this shape that fits the given one."""
        self.h_mm = _box_for(self.aspect, w_mm, h_mm)[1]

    def scale_by(self, factor):
        self.h_mm = max(self.h_mm * float(factor), 0.1)

    # -- rotation ------------------------------------------------------------ #

    def rotate_to(self, degrees):
        """Turn the item about its centre. Kept in [0, 360) so two ways of
        saying the same angle compare equal in the stamp."""
        self.rotation_deg = float(degrees) % 360.0

    def rotate_by(self, degrees):
        self.rotate_to(self.rotation_deg + float(degrees))

    # -- position ------------------------------------------------------------ #

    @property
    def rect_mm(self):
        """(x, y, w, h) of the unrotated box, from its top-left corner."""
        return (self.x_mm - self.w_mm / 2, self.y_mm - self.h_mm / 2,
                self.w_mm, self.h_mm)

    def move_to(self, x_mm, y_mm):
        self.x_mm, self.y_mm = float(x_mm), float(y_mm)

    def move_by(self, dx_mm, dy_mm):
        self.x_mm += float(dx_mm)
        self.y_mm += float(dy_mm)

    def bounds_mm(self):
        """(min_x, min_y, max_x, max_y) of what will actually be drawn.

        Not the same as :attr:`rect_mm` once the item is rotated: a turned
        rectangle needs a bigger one to hold it.
        """
        if not self.rotation_deg % 360:
            x, y, w, h = self.rect_mm
            return (x, y, x + w, y + h)
        rad = math.radians(self.rotation_deg)
        c, s = abs(math.cos(rad)), abs(math.sin(rad))
        w = self.w_mm * c + self.h_mm * s
        h = self.w_mm * s + self.h_mm * c
        return (self.x_mm - w / 2, self.y_mm - h / 2,
                self.x_mm + w / 2, self.y_mm + h / 2)

    def contains(self, x_mm, y_mm):
        """Hit test, in the item's own frame so rotation is honoured."""
        rad = math.radians(-self.rotation_deg)
        dx, dy = x_mm - self.x_mm, y_mm - self.y_mm
        lx = dx * math.cos(rad) - dy * math.sin(rad)
        ly = dx * math.sin(rad) + dy * math.cos(rad)
        return abs(lx) <= self.w_mm / 2 and abs(ly) <= self.h_mm / 2

    # -- geometry ------------------------------------------------------------ #

    def unit_paths(self):
        """The curves in the item's own frame: a box ``aspect`` wide and 1
        tall, y down, origin at its top-left.

        Independent of where the item is or how big it is, so it is computed
        once per drawing and cached. Moving or resizing an item then costs a
        transform, not a re-fit of a hundred thousand points — which is what
        makes dragging on the canvas smooth.
        """
        if self._unit is None:
            self._unit = self.drawing.fitted(self.aspect, 1.0)
        return self._unit

    def affine(self):
        """``(scale, rotation_deg, tx, ty)`` mapping the item's own frame to
        paper millimetres.

        THE placement. :meth:`paths_mm` applies it to get geometry and the
        canvas builds its QTransform from the same four numbers, so the screen
        and the paper cannot describe the item differently.
        """
        rad = math.radians(self.rotation_deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        # The rotation pivot is the box's centre, which in the item's own frame
        # (after scaling by h_mm) sits at (w/2, h/2).
        px, py = self.w_mm / 2, self.h_mm / 2
        tx = self.x_mm - (px * cos_r - py * sin_r)
        ty = self.y_mm - (px * sin_r + py * cos_r)
        return (self.h_mm, self.rotation_deg, tx, ty)

    def paths_mm(self):
        """The curves in paper millimetres, y down from the sheet's top-left.

        The single source of truth. The canvas draws these (through
        :meth:`affine`), the SVG writer writes these, and the plotter plots
        what the SVG writer wrote — so what is on screen and what reaches the
        paper cannot drift apart.
        """
        scale, rotation, tx, ty = self.affine()
        offset = complex(tx, ty)
        if not rotation % 360:
            return [p * scale + offset for p in self.unit_paths()]
        rad = math.radians(rotation)
        turn = complex(math.cos(rad), math.sin(rad)) * scale
        return [p * turn + offset for p in self.unit_paths()]

    def point_count(self):
        return self.drawing.point_count

    # -- persistence ---------------------------------------------------------- #

    def to_dict(self):
        """Everything but the curves — the INI regenerates those.

        ``w_mm`` is written for a reader's benefit only; :meth:`from_dict`
        takes the height, because the width is derived from it and the
        drawing's own aspect ratio (see the class docstring).
        """
        return {"name": self.name, "source": self.source,
                "x_mm": self.x_mm, "y_mm": self.y_mm,
                "w_mm": self.w_mm, "h_mm": self.h_mm,
                "rotation_deg": self.rotation_deg, "pen": self.pen,
                "visible": self.visible,
                "ini": getattr(self.drawing, "ini_text", "")}

    @classmethod
    def from_dict(cls, data, drawing, source=None):
        """An item from :meth:`to_dict` output plus the drawing its ``ini``
        regenerated. ``source`` is fresh, not the saved one: a token only
        means something in the session that minted it."""
        return cls(drawing=drawing,
                   x_mm=data.get("x_mm", 0.0), y_mm=data.get("y_mm", 0.0),
                   h_mm=data.get("h_mm", 100.0),
                   rotation_deg=data.get("rotation_deg", 0.0),
                   pen=data.get("pen", 0), name=data.get("name", "pattern"),
                   visible=data.get("visible", True), source=source)


def _box_for(aspect, max_w, max_h):
    """The largest ``aspect``-shaped box inside ``max_w`` x ``max_h``."""
    if max_w / max_h > aspect:
        return (max_h * aspect, max_h)
    return (max_w, max_w / aspect)
