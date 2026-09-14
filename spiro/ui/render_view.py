"""The pattern being built, on its own.

Before this the only place a pattern appeared was the paper, and only once it
had been placed there — so building one meant placing it, looking, taking it
off, and placing it again. This is the view for *building*: the current
drawing, alone, as large as the widget allows, redrawn every time the pipeline
changes. It has no millimetres. Size and position are the paper's business,
and this widget deliberately knows nothing about either; it shows the shape.

The curves are cached as one QPainterPath in the drawing's own units and
scaled with a QTransform, so a zoom or a resize costs a matrix, not a re-walk
of a hundred thousand points.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import QWidget

from spiro.ui import theme

PADDING_PX = 36


class RenderView(QWidget):
    """The current drawing, fitted to the widget. Wheel zooms, drag pans,
    ``0`` fits it again."""

    statusMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = None
        self.caption = ""
        self._path = None            # QPainterPath in drawing units
        self._scale = 1.0            # widget px per drawing unit
        self._origin = QPointF(0, 0)  # where the drawing's min corner lands
        self._fitted = False
        self._drag = None
        self.stroke = QColor(theme.TEXT)
        self.setMinimumSize(320, 240)
        self.setFocusPolicy(Qt.StrongFocus)

    # -- content ---------------------------------------------------------------- #

    def set_drawing(self, drawing, caption=""):
        """Show a drawing, or clear the view with ``None``. The zoom is kept
        across an edit — the pattern being tuned should not jump — and reset
        for a different-sized one, which is a different pattern."""
        previous = self.drawing
        self.drawing = drawing
        self.caption = caption
        self._path = None
        if drawing is None or previous is None or not self._fitted \
                or abs(previous.aspect - drawing.aspect) > 1e-3 \
                or abs(previous.width - drawing.width) > 1e-3 * drawing.width:
            self.fit()
        self.update()

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
                path.moveTo(points[0].real, points[0].imag)
                for p in points[1:]:
                    path.lineTo(p.real, p.imag)
            self._path = path
        return self._path

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
                             "Nothing generated yet.\nAdd a module in Build, "
                             "or press Surprise me.")
            painter.end()
            return

        painter.setRenderHint(QPainter.Antialiasing, self._drag is None)
        painter.save()
        painter.setTransform(self.transform())
        pen = QPen(self.stroke, 0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self._painter_path())
        painter.restore()

        if self.caption:
            painter.setPen(QColor(theme.MUTED))
            painter.setFont(QFont("monospace", 8))
            painter.drawText(QRectF(12, self.height() - 26, self.width() - 24, 18),
                             Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        painter.end()

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
