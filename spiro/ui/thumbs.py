"""Small pictures of curves.

The step strip, the gallery and the ideas panel all want the same thing: a
curve, or a list of curves, fitted into a square a few dozen pixels across
and drawn as a hairline. One place makes them, from complex point arrays,
so they all fit and stroke the same way.
"""

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

from spiro.ui import theme

MAX_POINTS = 2500        # a thumbnail cannot show more than this anyway


def painter_path(paths, box=1.0, max_points=MAX_POINTS):
    """One QPainterPath for a list of complex arrays, fitted into a
    ``box`` x ``box`` square with the origin at its top-left, y down."""
    arrays = [np.asarray(p) for p in paths if len(p) > 1]
    if not arrays:
        return QPainterPath(), 1.0
    combined = np.concatenate(arrays)
    x0, x1 = float(combined.real.min()), float(combined.real.max())
    y0, y1 = float(combined.imag.min()), float(combined.imag.max())
    w, h = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    scale = box / max(w, h)
    ox = (box - w * scale) / 2
    oy = (box - h * scale) / 2
    total = sum(len(a) for a in arrays)
    stride = max(1, total // max_points)
    path = QPainterPath()
    for a in arrays:
        pts = a[::stride]
        if len(pts) < 2:
            continue
        xs = ox + (pts.real - x0) * scale
        ys = oy + (y1 - pts.imag) * scale          # generators are y-up
        path.moveTo(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(x, y)
        last = a[-1]
        path.lineTo(ox + (last.real - x0) * scale, oy + (y1 - last.imag) * scale)
    return path, scale


def pixmap(paths, size=48, color=None, background=None, pad=4, width=1.0):
    """A ``size`` x ``size`` pixmap of the curves."""
    pix = QPixmap(size, size)
    pix.fill(background or QColor(theme.PANEL_HI))
    path, _ = painter_path(paths, box=size - 2 * pad)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(pad, pad)
    pen = QPen(color or QColor(theme.TEXT), width)
    pen.setCosmetic(True)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)
    painter.end()
    return pix


def draw_into(painter, rect, paths, color, pad=3, width=1.0):
    """Draw the curves fitted into ``rect`` with an existing painter."""
    rect = QRectF(rect)
    box = min(rect.width(), rect.height()) - 2 * pad
    path, _ = painter_path(paths, box=box)
    painter.save()
    painter.translate(rect.left() + (rect.width() - box) / 2,
                      rect.top() + (rect.height() - box) / 2)
    pen = QPen(color, width)
    pen.setCosmetic(True)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)
    painter.restore()
