"""The pen timeline: the draw from start to end as a strip, coloured by the
pen that is down, dark where the pen is up.

The machine never stops drawing its pattern; what changes is whether the
pen touches the paper, and which pen. The strip is that plan, and it is
edited by hand, the way the operator worked:

    drag across a band        the pen comes up for that stretch and goes
                              down again -- a holiday, same pen after
    drag the edge of a gap    move where the pen came up or went down;
                              the left edge of a swap's gap is the swap
    double-click a gap        close it: a holiday goes, a swap's gap shuts
    Ctrl-click a band         choose that pen's colour

The plan is the file's ``[output] inks``, ``ink_changes`` and ``holidays``
(see ``main.ink_plan``); the strip reads and writes those, nothing else,
so the Inks box under Finishing and the SVG see the same plan.
"""
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QColorDialog, QWidget

from main import ink_plan
from spiro.ui import theme

MARGIN = 10          # px either side, the scrubber's own margin
HEIGHT = 20
GRAB = 5             # px within which a gap's edge is taken hold of
DRAG_MIN = 3         # px of movement before a press becomes a new holiday


def _spans(text):
    out = []
    for token in str(text or "").split(","):
        token = token.strip()
        if not token:
            continue
        a, _, b = token.partition("-")
        a = min(max(float(a), 0.0), 1.0)
        b = min(max(float(b), a), 1.0) if b.strip() else None
        out.append([a, b])
    return out


def _fmt(a, b=None):
    return "%.3f" % a if b is None else "%.3f-%.3f" % (a, b)


class InkTimeline(QWidget):
    """The strip. ``changed`` carries the output keys to write."""

    changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.inks = []
        self.swaps = []          # [[a, b or None], ...] in file order
        self.holidays = []       # [[h0, h1], ...]
        self.advance = 0.0
        self._press = None       # (x, t) of a press on a band
        self._grab = None        # ("swap"|"holiday", index, 0|1) edge in hand
        self._rubber = None      # (t0, t1) of a holiday being drawn
        self.setFixedHeight(HEIGHT)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setToolTip(
            "The pens over the draw. Drag across a band to lift the pen for "
            "that stretch; drag a gap's edge to move it; double-click a gap "
            "to close it; Ctrl-click a band to choose its pen's colour.")

    # -- the plan ---------------------------------------------------------------- #

    def set_output(self, output):
        """Read the plan from a document's ``output`` dict."""
        output = output or {}
        self.inks = [c.strip() for c in str(output.get("inks", "")).split(",") if c.strip()]
        if not self.inks:
            self.inks = [str(output.get("stroke_color", theme.TEXT))]
        self.swaps = _spans(output.get("ink_changes", ""))[:max(len(self.inks) - 1, 0)]
        if len(self.inks) > 1 and not self.swaps:
            self.swaps = [[k / len(self.inks), None] for k in range(1, len(self.inks))]
        self.holidays = _spans(output.get("holidays", ""))
        self.advance = float(output.get("ink_advance", 0) or 0)
        self.update()

    def plan(self):
        return ink_plan(self.inks, self._changes_text(), self._holidays_text(), self.advance)

    def _changes_text(self):
        return ", ".join(_fmt(a, b) for a, b in self.swaps)

    def _holidays_text(self):
        return ", ".join(_fmt(a, b) for a, b in self.holidays if b is not None and b > a)

    def _emit(self):
        values = {"ink_changes": self._changes_text() if len(self.inks) > 1 else "",
                  "holidays": self._holidays_text()}
        if len(self.inks) > 1:
            values["inks"] = ", ".join(self.inks)
        self.changed.emit(values)
        self.update()

    def gaps(self):
        """Every stretch with the pen up: ``(kind, index, t0, t1)``."""
        out = []
        for i, (a, b) in enumerate(self.swaps):
            end = b if b is not None else min(a + self.advance, 1.0)
            out.append(("swap", i, a, end))
        for i, (a, b) in enumerate(self.holidays):
            if b is not None:
                out.append(("holiday", i, a, b))
        return out

    # -- geometry ------------------------------------------------------------------ #

    def _x(self, t):
        return MARGIN + t * (self.width() - 2 * MARGIN)

    def _t(self, x):
        span = max(self.width() - 2 * MARGIN, 1)
        return min(max((x - MARGIN) / span, 0.0), 1.0)

    def _edge_at(self, x):
        """The gap edge within reach of x, nearest first."""
        best = None
        for kind, index, t0, t1 in self.gaps():
            for side, t in ((0, t0), (1, t1)):
                d = abs(self._x(t) - x)
                if d <= GRAB and (best is None or d < best[0]):
                    best = (d, kind, index, side)
        return best[1:] if best else None

    def _gap_at(self, x):
        t = self._t(x)
        for kind, index, t0, t1 in self.gaps():
            if t0 <= t <= t1 and t1 > t0:
                return kind, index
        return None

    def _ink_at(self, x):
        t = self._t(x)
        for t0, t1, k in self.plan():
            if t0 <= t <= t1:
                return k
        return None

    # -- painting ------------------------------------------------------------------- #

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        top, h = 3, self.height() - 6
        p.fillRect(QRectF(MARGIN, top, self.width() - 2 * MARGIN, h), QColor(theme.PANEL_HI))
        for t0, t1, k in self.plan():
            color = QColor(self.inks[k] if k < len(self.inks) else theme.TEXT)
            p.fillRect(QRectF(self._x(t0), top, self._x(t1) - self._x(t0), h), color)
        # the pen-up stretches, with their edges
        p.setPen(QPen(QColor(theme.MUTED), 1))
        for kind, index, t0, t1 in self.gaps():
            if t1 > t0:
                p.drawLine(int(self._x(t0)), top, int(self._x(t0)), top + h)
                p.drawLine(int(self._x(t1)), top, int(self._x(t1)), top + h)
        if self._rubber:
            t0, t1 = sorted(self._rubber)
            p.fillRect(QRectF(self._x(t0), top, self._x(t1) - self._x(t0), h),
                       QColor(theme.PANEL_HI))
            p.setPen(QPen(QColor(theme.ACCENT), 1))
            p.drawRect(QRectF(self._x(t0), top, self._x(t1) - self._x(t0), h))
        p.end()

    # -- the hand ------------------------------------------------------------------- #

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        x = event.position().x()
        if event.modifiers() & Qt.ControlModifier:
            k = self._ink_at(x)
            if k is not None:
                chosen = QColorDialog.getColor(QColor(self.inks[k]), self, "Pen colour")
                if chosen.isValid():
                    self.inks[k] = chosen.name()
                    self._emit()
            return
        edge = self._edge_at(x)
        if edge:
            kind, index, side = edge
            if kind == "swap" and self.swaps[index][1] is None:
                # taking hold of it makes the gap the file's own, not the default
                self.swaps[index][1] = min(self.swaps[index][0] + self.advance, 1.0)
            self._grab = edge
            return
        self._press = (x, self._t(x))

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self._grab:
            kind, index, side = self._grab
            t = self._t(x)
            span = self.swaps[index] if kind == "swap" else self.holidays[index]
            if side == 0:
                span[0] = min(t, span[1])
            else:
                span[1] = max(t, span[0])
            self.update()
            return
        if self._press:
            if abs(x - self._press[0]) >= DRAG_MIN:
                self._rubber = (self._press[1], self._t(x))
                self.update()
            return
        self.setCursor(Qt.SizeHorCursor if self._edge_at(x) else Qt.CrossCursor)

    def mouseReleaseEvent(self, event):
        if self._grab:
            self._grab = None
            self._emit()
            return
        if self._rubber:
            t0, t1 = sorted(self._rubber)
            self._rubber = None
            self._press = None
            if t1 - t0 > 1e-4:
                self.holidays.append([t0, t1])
                self.holidays.sort()
                self._emit()
            return
        self._press = None

    def mouseDoubleClickEvent(self, event):
        hit = self._gap_at(event.position().x())
        if not hit:
            return
        kind, index = hit
        if kind == "holiday":
            del self.holidays[index]
        else:
            self.swaps[index][1] = self.swaps[index][0]      # shut: no pen-up at the swap
        self._emit()
