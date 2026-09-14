"""The pattern being built, on its own — and the machine that draws it.

Before this the only place a pattern appeared was the paper, and only once it
had been placed there — so building one meant placing it, looking, taking it
off, and placing it again. This is the view for *building*: the current
drawing, alone, as large as the widget allows, redrawn every time the pipeline
changes. It has no millimetres. Size and position are the paper's business,
and this widget deliberately knows nothing about either; it shows the shape.

Under it runs a scrubber. The engine keeps where the pen was after every
step at every sample (``Drawing.stages``), so the view can draw the machine
at any moment of the draw: each arm as a segment from where the previous one
ended, a table move as a dashed jump, the pen at the end, and the ink laid
down so far. Play it and the arms turn. Pick a step on the left and its own
curve — the drawing as it stood after that step — is drawn over the finished
one in that step's colour.

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

from spiro.ui import glyphs, theme

PADDING_PX = 36
PLAY_SECONDS = 12          # one pass of the scrubber when playing
FRAME_MS = 33


def _polygon(points):
    """A QPolygonF from a complex array, without a Python loop per point."""
    pts = np.asarray(points)
    return QPolygonF([QPointF(x, y) for x, y in zip(pts.real, pts.imag)])


class RenderView(QWidget):
    """The current drawing, fitted to the widget. Wheel zooms, drag pans,
    ``0`` fits it again."""

    statusMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = None
        self.caption = ""
        self.kinds = []              # one kind per stage, from the document
        self.highlight = None        # a step index whose stage curve to show
        self.time_index = None       # scrubber position, None = the end
        self.show_machine = True
        self._path = None            # QPainterPath in drawing units
        self._stage_paths = {}       # step index -> QPainterPath
        self._scale = 1.0            # widget px per drawing unit
        self._origin = QPointF(0, 0)  # where the drawing's min corner lands
        self._fitted = False
        self._drag = None
        self.stroke = QColor(theme.TEXT)
        self.setMinimumSize(320, 240)
        self.setFocusPolicy(Qt.StrongFocus)

    # -- content ---------------------------------------------------------------- #

    def set_drawing(self, drawing, caption="", kinds=None):
        """Show a drawing, or clear the view with ``None``. The zoom is kept
        across an edit — the pattern being tuned should not jump — and reset
        for a different-sized one, which is a different pattern."""
        previous = self.drawing
        self.drawing = drawing
        self.caption = caption
        self.kinds = list(kinds or [])
        self._path = None
        self._stage_paths = {}
        if drawing is None or previous is None or not self._fitted \
                or abs(previous.aspect - drawing.aspect) > 1e-3 \
                or abs(previous.width - drawing.width) > 1e-3 * drawing.width:
            self.fit()
        self.update()

    def set_highlight(self, index):
        """Show the drawing as it stood after step ``index`` (or None)."""
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
                and len(self.kinds) == len(self.drawing.stages))

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

    def _stage_path(self, index):
        if index not in self._stage_paths:
            path = QPainterPath()
            stage = self.drawing.stages[index]
            if len(stage) > 1:
                path.addPolygon(_polygon(stage))
            self._stage_paths[index] = path
        return self._stage_paths[index]

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

        painter.setRenderHint(QPainter.Antialiasing, self._drag is None)
        machine = self.show_machine and self.machine_ready()
        scrubbing = machine and self.time_index is not None \
            and self.time_index < self.sample_count() - 1

        painter.save()
        painter.setTransform(self.transform())
        stroke = QColor(self.stroke)
        if scrubbing or self.highlight is not None:
            stroke.setAlpha(70)          # the finished curve, behind
        pen = QPen(stroke, 0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self._painter_path())

        if self.highlight is not None and self.drawing.stages \
                and 0 <= self.highlight < len(self.drawing.stages) \
                and self.highlight < len(self.kinds):
            color = QColor(glyphs.KIND_COLORS[self.kinds[self.highlight]])
            color.setAlpha(80 if scrubbing else 200)
            pen = QPen(color, 1.2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawPath(self._stage_path(self.highlight))

        if scrubbing:
            ink = self.drawing.stages[-1][:self.time_index + 1]
            if len(ink) > 1:
                pen = QPen(self.stroke, 1.4)
                pen.setCosmetic(True)
                painter.setPen(pen)
                painter.drawPolyline(_polygon(ink))
        painter.restore()

        if machine:
            self._paint_machine(painter, self.time_index
                                if self.time_index is not None
                                else self.sample_count() - 1)

        if self.caption:
            painter.setPen(QColor(theme.MUTED))
            painter.setFont(QFont("monospace", 8))
            painter.drawText(QRectF(12, self.height() - 26, self.width() - 24, 18),
                             Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        painter.end()

    def _paint_machine(self, painter, i):
        """The linkage at sample ``i``: arm after arm from the origin, the
        table moves as dashed jumps, the pen at the end."""
        stages = self.drawing.stages
        i = max(0, min(i, len(stages[-1]) - 1))
        to_px = self.transform()
        previous = to_px.map(QPointF(0.0, 0.0))
        painter.setRenderHint(QPainter.Antialiasing, True)
        for k, stage in enumerate(stages):
            kind = self.kinds[k]
            point = to_px.map(QPointF(stage[i].real, stage[i].imag))
            color = QColor(glyphs.KIND_COLORS[kind])
            if kind == "clock":
                continue                 # a clock moves nothing
            pen = QPen(color, 2.0 if kind != "transform" else 1.2)
            if kind == "transform":
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(previous, point)
            # a pivot at the joint
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            radius = 3.0 if kind != "transform" else 2.0
            painter.drawEllipse(point, radius, radius)
            previous = point
        # the pen
        painter.setBrush(QColor(theme.TEXT))
        painter.setPen(QPen(QColor(theme.CANVAS_BG), 1.5))
        painter.drawEllipse(previous, 4.5, 4.5)

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
        delta = event.angleDelta().y()
        if delta:
            self.zoom_by(1.0015 ** delta, event.position())

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
            "Draw the arms, the table moves and the pen over the pattern — "
            "each in the colour of its kind")
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

    def set_drawing(self, drawing, caption="", kinds=None):
        self.view.set_drawing(drawing, caption, kinds)
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
