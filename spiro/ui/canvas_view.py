"""The paper, on screen, at a real scale.

This widget's whole job is to be honest. It draws the sheet at a known number
of pixels per millimetre, and it draws each item through the very transform
that :meth:`PlacedItem.affine` hands the SVG writer — so a pattern 90 mm wide
sitting 120 mm from the left edge is *drawn* 90 mm wide, 120 mm from the left
edge, and plots there. Dragging moves the item by the millimetres the pointer
moved across the paper, not by a percentage of a widget. Arrow keys nudge,
``[`` and ``]`` turn.

The curves are cached in the item's own frame (a box `aspect` wide and 1 tall)
and placed with a QTransform, so a drag costs a matrix multiply rather than
re-fitting a hundred thousand points.
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QPainter, QPainterPath, QPen,
                           QPolygonF, QTransform)
from PySide6.QtWidgets import QWidget

from spiro.ui import theme

# Above this many points a drag draws a decimated copy instead. 8000 points is
# already past what a screen can show on a 600 mm sheet; the full path comes
# back the moment the mouse is released.
FAST_POINTS = 8000

HANDLE_PX = 7.0           # the corner grab square
MIN_SIZE_MM = 2.0


class PaperCanvas(QWidget):
    """Pan, zoom, select, move and resize — on a sheet measured in mm."""

    selectionChanged = Signal(object)     # item_id or None
    itemChanged = Signal(object)          # item_id whose geometry moved
    statusMessage = Signal(str)

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.selected_id = None
        self.px_per_mm = 1.0
        self.origin = QPointF(0, 0)       # top-left of the paper, in widget px
        self._paths = {}                  # id(drawing) -> (full, fast)
        self._drag = None
        self._interacting = False
        self.show_grid = True
        self.show_margin = True
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(320, 240)

    # -- coordinates ---------------------------------------------------------- #

    def to_mm(self, pos):
        return QPointF((pos.x() - self.origin.x()) / self.px_per_mm,
                       (pos.y() - self.origin.y()) / self.px_per_mm)

    def to_px(self, x_mm, y_mm):
        return QPointF(self.origin.x() + x_mm * self.px_per_mm,
                       self.origin.y() + y_mm * self.px_per_mm)

    def view_transform(self):
        return (QTransform().translate(self.origin.x(), self.origin.y())
                .scale(self.px_per_mm, self.px_per_mm))

    def fit(self, padding_px=28):
        """Zoom so the whole sheet is visible, and centre it."""
        paper = self.scene.paper
        if paper.width_mm <= 0 or paper.height_mm <= 0:
            return
        avail_w = max(self.width() - 2 * padding_px, 40)
        avail_h = max(self.height() - 2 * padding_px, 40)
        self.px_per_mm = min(avail_w / paper.width_mm, avail_h / paper.height_mm)
        self.center_paper()
        self.update()

    def center_paper(self):
        paper = self.scene.paper
        self.origin = QPointF(
            (self.width() - paper.width_mm * self.px_per_mm) / 2,
            (self.height() - paper.height_mm * self.px_per_mm) / 2)

    def zoom_by(self, factor, anchor=None):
        """Zoom about a point, so what is under the pointer stays there."""
        anchor = anchor or QPointF(self.width() / 2, self.height() / 2)
        before = self.to_mm(anchor)
        self.px_per_mm = max(0.05, min(40.0, self.px_per_mm * factor))
        after = self.to_mm(anchor)
        self.origin += QPointF((after.x() - before.x()) * self.px_per_mm,
                               (after.y() - before.y()) * self.px_per_mm)
        self.update()

    # -- the cached geometry ---------------------------------------------------- #

    def invalidate(self, item=None):
        """Forget the cached curves — for one item's drawing, or all of them."""
        if item is None:
            self._paths.clear()
        else:
            self._paths.pop(id(item.drawing), None)
        self.update()

    def _painter_paths(self, item):
        key = id(item.drawing)
        cached = self._paths.get(key)
        if cached is None:
            unit = item.unit_paths()
            full = QPainterPath()
            fast = QPainterPath()
            total = sum(len(p) for p in unit)
            stride = max(1, total // FAST_POINTS)
            for points in unit:
                if len(points) < 2:
                    continue
                _append(full, points, 1)
                _append(fast, points, stride)
            cached = (full, fast if stride > 1 else full)
            self._paths[key] = cached
        return cached

    # -- painting ---------------------------------------------------------------- #

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, not self._interacting)
        painter.fillRect(self.rect(), theme.CANVAS_BG)

        paper = self.scene.paper
        sheet = QRectF(self.to_px(0, 0),
                       self.to_px(paper.width_mm, paper.height_mm))

        painter.fillRect(sheet.translated(3, 4), QColor(0, 0, 0, 90))   # shadow
        painter.fillRect(sheet, theme.PAPER)

        if self.show_grid:
            self._paint_grid(painter, sheet)
        if self.show_margin and paper.margin_mm > 0:
            x0, y0, w, h = paper.drawable
            painter.setPen(QPen(theme.MARGIN_LINE, 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(self.to_px(x0, y0), self.to_px(x0 + w, y0 + h)))

        painter.setPen(QPen(QColor(0, 0, 0, 120), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(sheet)

        painter.setClipRect(sheet)
        view = self.view_transform()
        out_of_bounds = {i.item_id for i in self.scene.out_of_bounds()}
        for item in self.scene.items:
            if not item.visible:
                continue
            self._paint_item(painter, item, view, item.item_id in out_of_bounds)
        painter.setClipping(False)

        selected = self.scene.find(self.selected_id) if self.selected_id else None
        if selected is not None:
            self._paint_selection(painter, selected)

        self._paint_scale_bar(painter)
        painter.end()

    def _paint_grid(self, painter, sheet):
        """10 mm minor, 50 mm major — but only while they are far enough apart
        to be a grid rather than a grey wash."""
        step = 10.0
        while step * self.px_per_mm < 6:
            step *= 5
        paper = self.scene.paper
        minor = QPen(theme.GRID, 1)
        major = QPen(theme.GRID_MAJOR, 1)
        x = 0.0
        while x <= paper.width_mm + 1e-6:
            painter.setPen(major if abs(x % (step * 5)) < 1e-6 else minor)
            px = self.origin.x() + x * self.px_per_mm
            painter.drawLine(QPointF(px, sheet.top()), QPointF(px, sheet.bottom()))
            x += step
        y = 0.0
        while y <= paper.height_mm + 1e-6:
            painter.setPen(major if abs(y % (step * 5)) < 1e-6 else minor)
            py = self.origin.y() + y * self.px_per_mm
            painter.drawLine(QPointF(sheet.left(), py), QPointF(sheet.right(), py))
            y += step

    def _paint_item(self, painter, item, view, flagged):
        full, fast = self._painter_paths(item)
        scale, rotation, tx, ty = item.affine()
        placement = (QTransform().translate(tx, ty).rotate(rotation)
                     .scale(scale, scale))
        painter.save()
        painter.setTransform(placement * view)
        color = QColor(self.scene.pen_of(item).color)
        if flagged:
            color = QColor(theme.ERR)
        # The stroke is set in device pixels, not paper units, so a hairline
        # stays a hairline at every zoom.
        pen = QPen(color, 0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(fast if self._interacting else full)
        painter.restore()

    def _paint_selection(self, painter, item):
        painter.save()
        painter.setPen(QPen(theme.SELECT, 1.2, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(QPolygonF([self.to_px(x, y)
                                       for x, y in _corners(item)]))
        painter.setPen(QPen(theme.SELECT, 1))
        painter.setBrush(QBrush(theme.SELECT))
        handle = self.to_px(*_corners(item)[2])
        painter.drawRect(QRectF(handle.x() - HANDLE_PX / 2, handle.y() - HANDLE_PX / 2,
                                HANDLE_PX, HANDLE_PX))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(theme.MUTED), 1))
        font = QFont("monospace", 8)
        painter.setFont(font)
        label = "%s   %.0f x %.0f mm   @ %.0f, %.0f" % (
            item.name, item.w_mm, item.h_mm, item.x_mm, item.y_mm)
        if item.rotation_deg % 360:
            label += "   %.0f°" % item.rotation_deg
        painter.drawText(self._caption_at(item, painter.fontMetrics(), label),
                         label)
        painter.restore()

    def _caption_at(self, item, metrics, label):
        """Where the caption goes: above the item's box, but kept on screen.

        An item near the right edge would otherwise write off the side of the
        sheet, and one near the top would write above it. Both are nudged back
        rather than clipped, because the caption is how you read off where the
        thing actually is."""
        x0, y0 = item.bounds_mm()[:2]
        point = self.to_px(x0, y0) + QPointF(0, -5)
        width = metrics.horizontalAdvance(label)
        right = self.to_px(self.scene.paper.width_mm, 0).x()
        if point.x() + width > right:
            point.setX(max(self.to_px(0, 0).x(), right - width))
        if point.y() < metrics.height():
            point.setY(self.to_px(0, 0).y() + metrics.height() + 2)
        return point

    def _paint_scale_bar(self, painter):
        """A bar of a round number of millimetres — the only honest way to say
        how big the thing on screen is."""
        span = 10.0
        while span * self.px_per_mm < 60:
            span *= 5 if span < 50 else 2
        while span * self.px_per_mm > 220:
            span /= 2
        length = span * self.px_per_mm
        y = self.height() - 18
        x = 14
        painter.setPen(QPen(QColor(theme.MUTED), 1))
        painter.drawLine(QPointF(x, y), QPointF(x + length, y))
        painter.drawLine(QPointF(x, y - 4), QPointF(x, y + 4))
        painter.drawLine(QPointF(x + length, y - 4), QPointF(x + length, y + 4))
        painter.setFont(QFont("monospace", 8))
        painter.drawText(QPointF(x + length + 8, y + 4), "%g mm" % span)

    # -- interaction ---------------------------------------------------------------- #

    def mousePressEvent(self, event):
        pos = event.position()
        mm = self.to_mm(pos)
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag = {"mode": "pan", "from": pos}
            self.setCursor(Qt.ClosedHandCursor)
            return
        if event.button() != Qt.LeftButton:
            return

        selected = self.scene.find(self.selected_id) if self.selected_id else None
        if selected is not None and self._on_handle(pos, selected):
            self._drag = {"mode": "resize", "item": selected,
                          "start": mm, "w0": selected.w_mm}
            self._interacting = True
            return

        item = self.scene.item_at(mm.x(), mm.y())
        self._select(item.item_id if item else None)
        if item is not None:
            self._drag = {"mode": "move", "item": item, "start": mm,
                          "x0": item.x_mm, "y0": item.y_mm}
            self._interacting = True
            self.setCursor(Qt.ClosedHandCursor)
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._drag is None:
            selected = self.scene.find(self.selected_id) if self.selected_id else None
            if selected is not None and self._on_handle(pos, selected):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                mm = self.to_mm(pos)
                over = self.scene.item_at(mm.x(), mm.y())
                self.setCursor(Qt.OpenHandCursor if over else Qt.ArrowCursor)
                self.statusMessage.emit("%.1f, %.1f mm" % (mm.x(), mm.y()))
            return

        if self._drag["mode"] == "pan":
            self.origin += pos - self._drag["from"]
            self._drag["from"] = pos
            self.update()
            return

        mm = self.to_mm(pos)
        item = self._drag["item"]
        if self._drag["mode"] == "move":
            dx = mm.x() - self._drag["start"].x()
            dy = mm.y() - self._drag["start"].y()
            if event.modifiers() & Qt.ShiftModifier:      # lock to one axis
                if abs(dx) > abs(dy):
                    dy = 0
                else:
                    dx = 0
            item.move_to(self._drag["x0"] + dx, self._drag["y0"] + dy)
            self.statusMessage.emit("%s at %.1f, %.1f mm"
                                    % (item.name, item.x_mm, item.y_mm))
        else:
            # Resize from the centre: the corner follows the pointer, so the
            # width is twice the pointer's distance from the centre along the
            # item's own x axis — its own, so a turned item resizes along its
            # turned edge rather than the sheet's.
            rad = math.radians(-item.rotation_deg)
            dx, dy = mm.x() - item.x_mm, mm.y() - item.y_mm
            along = dx * math.cos(rad) - dy * math.sin(rad)
            item.set_width(max(2 * abs(along), MIN_SIZE_MM))
            self.statusMessage.emit("%s %.1f x %.1f mm"
                                    % (item.name, item.w_mm, item.h_mm))
        self.itemChanged.emit(item.item_id)
        self.update()

    def mouseReleaseEvent(self, _event):
        was = self._drag
        self._drag = None
        self._interacting = False
        self.setCursor(Qt.ArrowCursor)
        if was and was.get("item") is not None:
            self.itemChanged.emit(was["item"].item_id)
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta:
            self.zoom_by(1.0015 ** delta, event.position())

    def keyPressEvent(self, event):
        item = self.scene.find(self.selected_id) if self.selected_id else None
        step = 0.1 if event.modifiers() & Qt.ShiftModifier else 1.0
        moves = {Qt.Key_Left: (-step, 0), Qt.Key_Right: (step, 0),
                 Qt.Key_Up: (0, -step), Qt.Key_Down: (0, step)}
        turns = {Qt.Key_BracketLeft: -1, Qt.Key_BracketRight: 1}
        if item is not None and event.key() in moves:
            item.move_by(*moves[event.key()])
            self.itemChanged.emit(item.item_id)
            self.update()
        elif item is not None and event.key() in turns:
            # [ and ] turn by a degree; with shift, by fifteen — the angles a
            # person actually wants are multiples of fifteen.
            item.rotate_by(turns[event.key()]
                           * (15.0 if event.modifiers() & Qt.ShiftModifier else 1.0))
            self.statusMessage.emit("%s at %.0f°" % (item.name, item.rotation_deg))
            self.itemChanged.emit(item.item_id)
            self.update()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_by(1.15)
        elif event.key() == Qt.Key_Minus:
            self.zoom_by(1 / 1.15)
        elif event.key() == Qt.Key_0:
            self.fit()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.oldSize().width() <= 0:
            self.fit()

    # -- selection ------------------------------------------------------------------- #

    def select(self, item_id):
        if item_id != self.selected_id:
            self.selected_id = item_id
            self.update()

    def _select(self, item_id):
        if item_id != self.selected_id:
            self.selected_id = item_id
            self.selectionChanged.emit(item_id)

    def _on_handle(self, pos, item):
        handle = self.to_px(*_corners(item)[2])
        return (abs(pos.x() - handle.x()) <= HANDLE_PX
                and abs(pos.y() - handle.y()) <= HANDLE_PX)


def _append(path, points, stride):
    """One polyline into a QPainterPath, keeping the last point whatever the
    stride — an open end is a visible gap."""
    path.moveTo(points[0].real, points[0].imag)
    for i in range(stride, len(points), stride):
        path.lineTo(points[i].real, points[i].imag)
    last = points[-1]
    path.lineTo(last.real, last.imag)


def _corners(item):
    """The item's four corners in paper mm, clockwise from the top-left."""
    rad = math.radians(item.rotation_deg)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    half_w, half_h = item.w_mm / 2, item.h_mm / 2
    out = []
    for dx, dy in ((-half_w, -half_h), (half_w, -half_h),
                   (half_w, half_h), (-half_w, half_h)):
        out.append((item.x_mm + dx * cos_r - dy * sin_r,
                    item.y_mm + dx * sin_r + dy * cos_r))
    return out
