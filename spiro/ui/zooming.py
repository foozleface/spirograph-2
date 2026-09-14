"""Wheel zoom that behaves on a trackpad and a Magic Mouse.

Those devices send a stream of small scroll events, then a tail of
*momentum* events after the finger has lifted. Treated as plain wheel
clicks that is a zoom that keeps going after you stop, and — because every
event asked for a repaint of a hundred-thousand-point path — one that lags
behind the hand. So: momentum events are ignored, the zoom factor is
accumulated, and the view is repainted once per frame at most, with
antialiasing off until the hand is still.
"""

from PySide6.QtCore import QPointF, Qt, QTimer

FRAME_MS = 16
SETTLE_MS = 160


class WheelZoom:
    """Attach to a widget with ``zoom_by(factor, anchor)`` and an
    ``interacting`` attribute the paint code reads."""

    def __init__(self, widget, attr="interacting"):
        self.widget = widget
        self.attr = attr
        self._factor = 1.0
        self._anchor = None
        self._frame = QTimer(widget)
        self._frame.setSingleShot(True)
        self._frame.setInterval(FRAME_MS)
        self._frame.timeout.connect(self._apply)
        self._settle = QTimer(widget)
        self._settle.setSingleShot(True)
        self._settle.setInterval(SETTLE_MS)
        self._settle.timeout.connect(self._settled)

    def wheel(self, event):
        """Handle a wheel event. Returns True if it was consumed."""
        if event.phase() in (Qt.ScrollMomentum, Qt.ScrollEnd):
            event.accept()
            return True
        pixels = event.pixelDelta().y()
        delta = pixels * 2.0 if pixels else event.angleDelta().y() / 4.0
        if not delta:
            return False
        self._factor *= 1.006 ** delta
        self._anchor = QPointF(event.position())
        setattr(self.widget, self.attr, True)
        if not self._frame.isActive():
            self._frame.start()
        self._settle.start()
        event.accept()
        return True

    def _apply(self):
        if self._factor != 1.0:
            self.widget.zoom_by(self._factor, self._anchor)
            self._factor = 1.0

    def _settled(self):
        self._apply()
        setattr(self.widget, self.attr, False)
        self.widget.update()
