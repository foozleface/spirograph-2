"""The pattern being built, on its own — and the machine that draws it.

Before this the only place a pattern appeared was the paper, and only once it
had been placed there — so building one meant placing it, looking, taking it
off, and placing it again. This is the view for *building*: the current
drawing, alone, as large as the widget allows, redrawn every time the pipeline
changes. It has no millimetres. Size and position are the paper's business,
and this widget deliberately knows nothing about either; it shows the shape.

Under it runs a scrubber. The engine keeps where the pen was after every
step at every sample (``Drawing.stages``), so the view can draw the machine
at any moment of the draw:

* an **arm** is a segment from where the previous one ended, in amber;
* a **carriage path** is the track it runs on — the path's own curve,
  drawn in teal from the point the carriage carries — with the carriage as
  a small square on it, and the arms hanging from the carriage (arms add
  vectors, so within a run of arms the carriage may honestly go first);
* a **table move** is the paper itself: a violet frame, drawn where the
  paper was and where the move has put it at this moment, so a rotation
  turns it, a scale grows it, a bend bends it. The frame is asked of the
  module that did the move, at the time it did it; the jump it gave the pen
  is a dashed line;
* the **pen** is the dot at the end, and the ink laid so far is drawn solid
  over the finished curve, which is dimmed.

Pick a step on the left and what it *contributes* is drawn over the
finished curve in its colour: an arm's own curve, a path's track, a table
move's frame.

The curves are cached as one QPainterPath in the drawing's own units and
scaled with a QTransform, so a zoom or a resize costs a matrix, not a re-walk
of a hundred thousand points.
"""

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QFont, QPainter, QPainterPath, QPen,
                           QPolygonF, QTransform)
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QPushButton,
                               QSlider, QVBoxLayout, QWidget)

from spiro.pipeline.registry import is_arm  # noqa: F401  (kinds come from the window)
from spiro.ui import glyphs, theme
from spiro.ui.zooming import WheelZoom

PADDING_PX = 36
PLAY_SECONDS = 12          # one pass of the scrubber when playing
FRAME_MS = 33
FRAME_SIDE = 0.35          # the table frame's side, as a fraction of the drawing
FRAME_POINTS = 12          # samples per side, so a bend shows as a curve
ARM_KINDS = ("generator", "path")


def _polygon(points):
    """A QPolygonF from a complex array."""
    pts = np.asarray(points)
    return QPolygonF([QPointF(x, y) for x, y in zip(pts.real, pts.imag)])


def square_frame(centre, side, per_side=FRAME_POINTS):
    """The outline of a sheet of paper: a 4:3 rectangle with its top-right
    corner folded off, ``per_side`` points a side so a bend shows as a
    curve. A square turned a quarter is the same square; this is not."""
    w, h = side / 2.0, side * 0.375
    ear = side * 0.18
    corners = [centre + complex(w - ear, h), centre + complex(-w, h),
               centre + complex(-w, -h), centre + complex(w, -h),
               centre + complex(w, h - ear)]
    out = []
    for a, b in zip(corners, corners[1:] + corners[:1]):
        for k in range(per_side):
            out.append(a + (b - a) * (k / per_side))
    return np.array(out, dtype=complex)


def frame_cross(centre, side):
    """A small cross at the paper's centre: two short strokes."""
    r = side * 0.06
    return (np.array([centre - r, centre + r]),
            np.array([centre - 1j * r, centre + 1j * r]))


def retimed(drawing, k, i):
    """The t module ``k`` saw at sample ``i`` — the drawing's t, passed
    through every clock before ``k``."""
    t = np.asarray([drawing.t_values[i]], dtype=float)
    for module in drawing.modules[:k]:
        if getattr(module, "is_clock", False):
            t = module.retime(t)
    return t


def scope_base(drawing, kinds, scopes, k, i):
    """Where a table move's frame sits: the origin for ``scope = all``, or
    the pen's position before the last ``scope`` arms."""
    scope = scopes[k]
    if scope == "all":
        return 0j, "all"
    arms = [j for j in range(k) if kinds[j] in ARM_KINDS]
    n = min(int(scope), len(arms))
    if n == 0:
        return complex(drawing.stages[k - 1][i]) if k else 0j, 0
    first = arms[-n]
    return (complex(drawing.stages[first - 1][i]) if first else 0j), n


def moved(drawing, kinds, scopes, k, i, points, base, n):
    """``points`` as table move ``k`` leaves them at sample ``i``."""
    module = drawing.modules[k]
    t = np.full(points.shape, retimed(drawing, k, i)[0])
    if n == "all":
        out = module.transform(points, t)
    else:
        out = base + module.transform(points - base, t)
    return np.asarray(out, dtype=complex)


def table_frame(drawing, kinds, scopes, k, i):
    """The paper before and after table move ``k`` at sample ``i``:
    ``(before, after)``, two complex arrays of the frame outline."""
    side = FRAME_SIDE * max(drawing.width, drawing.height)
    base, n = scope_base(drawing, kinds, scopes, k, i)
    before = square_frame(base, side)
    return before, moved(drawing, kinds, scopes, k, i, before, base, n)


def table_trail(drawing, kinds, scopes, k, i, count=5):
    """The paper at ``count`` moments from the start of the draw to sample
    ``i`` — the move as a motion trail, for a still picture of it."""
    side = FRAME_SIDE * max(drawing.width, drawing.height)
    out = []
    for j in np.linspace(0, i, count).astype(int):
        base, n = scope_base(drawing, kinds, scopes, k, int(j))
        frame = square_frame(base, side)
        cross = frame_cross(base, side)
        out.append((moved(drawing, kinds, scopes, k, int(j), frame, base, n),
                    tuple(moved(drawing, kinds, scopes, k, int(j), c, base, n)
                          for c in cross)))
    return out


def contribution(drawing, k):
    """What step ``k`` adds on its own, over the whole draw: the vector an
    arm or a carriage path contributes at every sample."""
    stage = drawing.stages[k]
    previous = drawing.stages[k - 1] if k else np.zeros_like(stage)
    return stage - previous


def machine_links(drawing, kinds, i, start=0j):
    """The linkage at sample ``i`` as ``[(kind, index, from, to)]`` in
    drawing units. Within a run of arms the carriage paths come first, so
    the arms hang from the carriage; the sum is the same either way."""
    stages = drawing.stages
    links = []
    current = complex(start)
    k = 0
    n = len(stages)
    while k < n:
        kind = kinds[k]
        if kind in ARM_KINDS:
            run = []
            while k < n and kinds[k] in ARM_KINDS:
                run.append(k)
                k += 1
            ordered = [j for j in run if kinds[j] == "path"] + \
                      [j for j in run if kinds[j] == "generator"]
            for j in ordered:
                previous = stages[j - 1][i] if j else start
                vec = complex(stages[j][i]) - complex(previous)
                links.append((kinds[j], j, current, current + vec))
                current += vec
            current = complex(stages[run[-1]][i])     # exact, not summed
        elif kind == "clock":
            k += 1
        else:
            target = complex(stages[k][i])
            links.append((kind, k, current, target))
            current = target
            k += 1
    return links


class RenderView(QWidget):
    """The current drawing, fitted to the widget. Wheel zooms, drag pans,
    ``0`` fits it again."""

    statusMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = None
        self.caption = ""
        self.kinds = []              # one kind per stage, from the document
        self.scopes = []             # one scope per stage
        self.highlight = None        # a step index whose contribution to show
        self.time_index = None       # scrubber position, None = the end
        self.show_machine = True
        self.interacting = False     # zooming or dragging: paint cheaply
        self._path = None            # QPainterPath in drawing units
        self._contributions = {}     # step index -> QPainterPath of its own curve
        self._scale = 1.0            # widget px per drawing unit
        self._origin = QPointF(0, 0)  # where the drawing's min corner lands
        self._fitted = False
        self._drag = None
        self._wheel = WheelZoom(self)
        self.stroke = QColor(theme.TEXT)
        self.setMinimumSize(320, 240)
        self.setFocusPolicy(Qt.StrongFocus)

    # -- content ---------------------------------------------------------------- #

    def set_drawing(self, drawing, caption="", kinds=None, scopes=None):
        """Show a drawing, or clear the view with ``None``. The zoom is kept
        across an edit — the pattern being tuned should not jump — and reset
        for a different-sized one, which is a different pattern."""
        previous = self.drawing
        self.drawing = drawing
        self.caption = caption
        self.kinds = list(kinds or [])
        self.scopes = list(scopes or ["all"] * len(self.kinds))
        self._path = None
        self._contributions = {}
        if drawing is None or previous is None or not self._fitted \
                or abs(previous.aspect - drawing.aspect) > 1e-3 \
                or abs(previous.width - drawing.width) > 1e-3 * drawing.width:
            self.fit()
        self.update()

    def set_highlight(self, index):
        """Show what step ``index`` contributes (or None)."""
        self.highlight = index
        self.update()

    def set_time_index(self, index):
        """Where in the draw the machine is shown; None means the end."""
        self.time_index = index
        self.update()

    def set_show_machine(self, on):
        self.show_machine = bool(on)
        self.update()

    def sample_count(self):
        """How many moments the scrubber can stop at."""
        if self.drawing is None or not self.drawing.stages:
            return 0
        return len(self.drawing.stages[-1])

    def machine_ready(self):
        """Is there a machine to draw — stages for every step, one kind each?"""
        return (self.drawing is not None and bool(self.drawing.stages)
                and len(self.kinds) == len(self.drawing.stages)
                and len(self.drawing.modules) == len(self.drawing.stages))

    def current_index(self):
        count = self.sample_count()
        if count == 0:
            return None
        if self.time_index is None:
            return count - 1
        return max(0, min(self.time_index, count - 1))

    def fit(self):
        """Scale so the whole drawing is visible, centred."""
        if self.drawing is None:
            self._fitted = False
            self.update()
            return
        avail_w = max(self.width() - 2 * PADDING_PX, 20)
        avail_h = max(self.height() - 2 * PADDING_PX, 20)
        self._scale = min(avail_w / self.drawing.width, avail_h / self.drawing.height)
        self._center()
        self._fitted = True
        self.update()

    def _center(self):
        d = self.drawing
        self._origin = QPointF((self.width() - d.width * self._scale) / 2,
                               (self.height() - d.height * self._scale) / 2)

    def zoom_by(self, factor, anchor=None):
        if self.drawing is None:
            return
        anchor = anchor or QPointF(self.width() / 2, self.height() / 2)
        new_scale = max(self._scale * factor, 1e-6)
        # Keep what is under the anchor where it is.
        self._origin = anchor - (anchor - self._origin) * (new_scale / self._scale)
        self._scale = new_scale
        self.update()

    # -- the transform ------------------------------------------------------------ #

    def _painter_path(self):
        if self._path is None and self.drawing is not None:
            path = QPainterPath()
            for points in self.drawing.paths:
                if len(points) < 2:
                    continue
                path.addPolygon(_polygon(points))
            self._path = path
        return self._path

    def _contribution_path(self, index):
        if index not in self._contributions:
            path = QPainterPath()
            own = contribution(self.drawing, index)
            if len(own) > 1:
                path.addPolygon(_polygon(own))
            self._contributions[index] = path
        return self._contributions[index]

    def transform(self):
        """Drawing units to widget pixels. y is flipped: the generators work
        y-up, the screen y-down, and the paper canvas flips the same way — so
        what is shown here is the way up it will be drawn."""
        d = self.drawing
        return (QTransform()
                .translate(self._origin.x(), self._origin.y() + d.height * self._scale)
                .scale(self._scale, -self._scale)
                .translate(-d.min_x, -d.min_y))

    # -- painting ------------------------------------------------------------------ #

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), theme.CANVAS_BG)
        if self.drawing is None:
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "Nothing generated yet.\nAdd a step in Build, "
                             "or press Surprise me.")
            painter.end()
            return

        quick = self.interacting or self._drag is not None
        painter.setRenderHint(QPainter.Antialiasing, not quick)
        machine = self.show_machine and self.machine_ready() and not quick
        i = self.current_index()
        scrubbing = machine and i is not None and i < self.sample_count() - 1
        showing = (self.highlight is not None and self.machine_ready()
                   and 0 <= self.highlight < len(self.kinds))
        kind_shown = self.kinds[self.highlight] if showing else None

        painter.save()
        painter.setTransform(self.transform())
        stroke = QColor(self.stroke)
        if scrubbing or kind_shown in ARM_KINDS:
            stroke.setAlpha(70)          # the finished curve, behind
        pen = QPen(stroke, 0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self._painter_path())

        if kind_shown in ARM_KINDS and not quick:
            # what this arm or carriage contributes on its own
            color = QColor(glyphs.KIND_COLORS[kind_shown])
            color.setAlpha(80 if scrubbing else 200)
            pen = QPen(color, 1.2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawPath(self._contribution_path(self.highlight))

        if scrubbing:
            ink = self.drawing.stages[-1][:i + 1]
            if len(ink) > 1:
                pen = QPen(self.stroke, 1.4)
                pen.setCosmetic(True)
                painter.setPen(pen)
                painter.drawPolyline(_polygon(ink))
        painter.restore()

        if machine:
            self._paint_machine(painter, i)
        if kind_shown == "transform" and self.machine_ready() and not quick:
            self._paint_table(painter, self.highlight, i)

        if self.caption:
            painter.setPen(QColor(theme.MUTED))
            painter.setFont(QFont("monospace", 8))
            painter.drawText(QRectF(12, self.height() - 26, self.width() - 24, 18),
                             Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        painter.end()

    def _paint_machine(self, painter, i):
        """The linkage at sample ``i``: carriages on their tracks, arms from
        the carriage, table moves as dashed jumps, the pen at the end."""
        to_px = self.transform()
        painter.setRenderHint(QPainter.Antialiasing, True)

        def px(z):
            return to_px.map(QPointF(z.real, z.imag))

        links = machine_links(self.drawing, self.kinds, i)
        for kind, k, start, end in links:
            color = QColor(glyphs.KIND_COLORS[kind])
            if kind == "path":
                # the track, from where the carriage is carried
                track = contribution(self.drawing, k) + start
                dim = QColor(color)
                chosen = self.highlight == k
                dim.setAlpha(255 if chosen else 190)
                painter.save()
                painter.setTransform(to_px)
                pen = QPen(dim, 2.2 if chosen else 1.3)
                pen.setCosmetic(True)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(_polygon(track))
                painter.restore()
                painter.setPen(QPen(color, 1.5))
                painter.drawLine(px(start), px(end))
                painter.setBrush(color)
                painter.setPen(QPen(QColor(theme.CANVAS_BG), 1.0))
                p = px(end)
                painter.drawRect(QRectF(p.x() - 5, p.y() - 5, 10, 10))   # the carriage
            elif kind == "generator":
                painter.setPen(QPen(color, 2.0))
                painter.drawLine(px(start), px(end))
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(px(start), 3.0, 3.0)                # the pivot
            else:
                pen = QPen(color, 1.2)
                pen.setStyle(Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(px(start), px(end))
        # the pen
        end = px(links[-1][3]) if links else px(complex(self.drawing.stages[-1][i]))
        painter.setBrush(QColor(theme.TEXT))
        painter.setPen(QPen(QColor(theme.CANVAS_BG), 1.5))
        painter.drawEllipse(end, 4.5, 4.5)

    def _paint_table(self, painter, k, i):
        """The paper under table move ``k``: where it started, ghosts of it
        on the way, and where the move has it at sample ``i``."""
        before, _ = table_frame(self.drawing, self.kinds, self.scopes, k, i)
        trail = table_trail(self.drawing, self.kinds, self.scopes, k, i)
        to_px = self.transform()
        color = QColor(glyphs.KIND_COLORS["transform"])
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setTransform(to_px)
        painter.setBrush(Qt.NoBrush)
        dim = QColor(color)
        dim.setAlpha(110)
        pen = QPen(dim, 1.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawPolygon(_polygon(before))          # the paper before any move
        count = len(trail)
        for index, (frame, cross) in enumerate(trail):
            last = index == count - 1
            ghost = QColor(color)
            ghost.setAlpha(255 if last else 50 + 110 * index // max(count - 1, 1))
            pen = QPen(ghost, 1.8 if last else 1.0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawPolygon(_polygon(frame))
            for stroke in cross:
                painter.drawPolyline(_polygon(stroke))
        painter.restore()

    # -- interaction ----------------------------------------------------------------- #

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._drag = event.position()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self._origin += event.position() - self._drag
            self._drag = event.position()
            self.update()

    def mouseReleaseEvent(self, _event):
        self._drag = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def mouseDoubleClickEvent(self, _event):
        self.fit()

    def wheelEvent(self, event):
        if not self._wheel.wheel(event):
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_by(1.15)
        elif event.key() == Qt.Key_Minus:
            self.zoom_by(1 / 1.15)
        elif event.key() == Qt.Key_0:
            self.fit()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.drawing is not None and (not self._fitted or event.oldSize().width() <= 0):
            self.fit()
        elif self.drawing is not None and self._fitted:
            # A fitted view stays fitted through a resize — the window being
            # dragged wider should give the pattern the room, not a margin.
            self.fit()


class RenderPanel(QWidget):
    """The render view with the scrubber under it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = RenderView()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view, 1)

        bar = QWidget()
        bar.setObjectName("panel")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(10, 4, 10, 4)
        bar_layout.setSpacing(8)
        self.play = QPushButton("▶")
        self.play.setCheckable(True)
        self.play.setFixedWidth(34)
        self.play.setToolTip("Watch the machine draw it (Space)")
        self.play.toggled.connect(self._play_toggled)
        self.scrubber = QSlider(Qt.Horizontal)
        self.scrubber.setRange(0, 0)
        self.scrubber.setToolTip("Where in the draw the machine is shown — "
                                 "drag it to see the arms at any moment")
        self.scrubber.valueChanged.connect(self._scrubbed)
        self.time_label = QLabel("")
        self.time_label.setMinimumWidth(64)
        self.time_label.setObjectName("muted")
        self.machine_box = QCheckBox("Show the machine")
        self.machine_box.setChecked(True)
        self.machine_box.setToolTip(
            "Draw the arms, the carriages on their tracks, the table moves "
            "and the pen over the pattern — each in the colour of its kind")
        self.machine_box.toggled.connect(self.view.set_show_machine)
        bar_layout.addWidget(self.play)
        bar_layout.addWidget(self.scrubber, 1)
        bar_layout.addWidget(self.time_label)
        bar_layout.addWidget(self.machine_box)
        layout.addWidget(bar)
        self.bar = bar

        self._timer = QTimer(self)
        self._timer.setInterval(FRAME_MS)
        self._timer.timeout.connect(self._tick)

    def set_drawing(self, drawing, caption="", kinds=None, scopes=None):
        self.view.set_drawing(drawing, caption, kinds, scopes)
        count = self.view.sample_count()
        at_end = self.scrubber.value() >= self.scrubber.maximum()
        self.scrubber.blockSignals(True)
        self.scrubber.setRange(0, max(count - 1, 0))
        if at_end or count == 0:
            self.scrubber.setValue(max(count - 1, 0))
        else:
            # keep the same moment through an edit
            self.scrubber.setValue(min(self.scrubber.value(), max(count - 1, 0)))
        self.scrubber.blockSignals(False)
        self._scrubbed(self.scrubber.value())
        self.bar.setEnabled(self.view.machine_ready())

    def set_highlight(self, index):
        self.view.set_highlight(index)

    def _scrubbed(self, value):
        count = self.view.sample_count()
        if count == 0:
            self.view.set_time_index(None)
            self.time_label.setText("")
            return
        self.view.set_time_index(None if value >= count - 1 else value)
        self.time_label.setText("%d%%" % round(100 * value / max(count - 1, 1)))

    def _play_toggled(self, on):
        self.play.setText("⏸" if on else "▶")
        if on:
            if self.scrubber.value() >= self.scrubber.maximum():
                self.scrubber.setValue(0)
            self._timer.start()
        else:
            self._timer.stop()

    def _tick(self):
        count = self.view.sample_count()
        if count < 2:
            self.play.setChecked(False)
            return
        step = max(1, int(count * FRAME_MS / (PLAY_SECONDS * 1000)))
        value = self.scrubber.value() + step
        if value >= count - 1:
            value = 0
        self.scrubber.setValue(value)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.play.toggle()
        else:
            super().keyPressEvent(event)
