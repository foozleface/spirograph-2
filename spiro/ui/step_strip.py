"""The machine, step by step.

Each step is a card: a bar in the colour of its kind, a glyph, its name and
the numbers that matter, and a thumbnail of the drawing *as it stands
after that step* — so the effect of every arm and every table move is
visible where it is made, not inferred from the final curve.

Down the left runs the bracket that says what a table move acts on. A
transform whose scope is "everything so far" brackets every card above
it; one whose scope is "the last arm" brackets just that arm. It is the
same thing a group used to say with nesting, drawn instead of typed.

Painted by hand rather than assembled from list items, because the bracket
crosses card boundaries and a list widget cannot draw between its rows.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from spiro.pipeline.registry import MODULE_DEFS, is_arm
from spiro.ui import glyphs, theme, thumbs

ROW = 48
GUTTER = 18          # where the brackets live
BAR = 4              # the kind-coloured bar
THUMB = 40
PAD = 6


def summarise(params, limit=3):
    """The numbers a person would say out loud for a step."""
    spec = MODULE_DEFS.get(params.get("type"))
    if not spec:
        return ""
    bits = []
    for name, p in spec["params"].items():
        if name in params and not p.get("hidden") and not p.get("advanced") \
                and "drift_for" not in p and name != "cycles":
            value = params[name]
            if isinstance(value, bool):
                if value:
                    bits.append(name.replace("_", " "))
                continue
            if isinstance(value, float):
                value = "%g" % value
            bits.append("%s %s" % ((p.get("desc") or name).split(" (")[0].lower(), value))
        if len(bits) >= limit:
            break
    drifting = [p["drift_for"] for n, p in spec["params"].items()
                if "drift_for" in p and n in params
                and params.get(n) != params.get(p["drift_for"])]
    if drifting:
        bits.append("drifts " + ", ".join(d.replace("_", " ") for d in drifting[:2]))
    cycles = params.get("cycles")
    if cycles and float(cycles) != 1:
        bits.append("×%g" % float(cycles))
    return " · ".join(bits)


class StepStrip(QWidget):
    """The steps of the pipeline as cards, with scope brackets."""

    selected = Signal(object)       # index or None
    hovered = Signal(object)        # index or None
    moveRequested = Signal(int, int)
    removeRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps = []             # the document's step dicts (singles)
        self.stage_paths = []       # per step, a list of complex arrays, or None
        self.selection = None
        self.hover = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._relayout()

    # -- content ---------------------------------------------------------------- #

    def set_steps(self, steps, stage_paths=None, select=None):
        self.steps = list(steps)
        self.stage_paths = list(stage_paths or [])
        if select is not None or self.selection is None or self.selection >= len(self.steps):
            self.selection = select if select is not None and 0 <= select < len(self.steps) else (
                None if not self.steps else min(self.selection or 0, len(self.steps) - 1))
        self._relayout()
        self.update()

    def set_stages(self, stage_paths):
        self.stage_paths = list(stage_paths or [])
        self.update()

    def select(self, index):
        index = index if index is not None and 0 <= index < len(self.steps) else None
        if index != self.selection:
            self.selection = index
            self.update()

    def _relayout(self):
        self.setMinimumHeight(max(ROW * len(self.steps), ROW) + 4)
        self.setMaximumHeight(max(ROW * len(self.steps), ROW) + 4)

    def row_at(self, y):
        index = int(y // ROW)
        return index if 0 <= index < len(self.steps) else None

    # -- geometry helpers ------------------------------------------------------- #

    def _kind(self, index):
        return glyphs.kind_of(self.steps[index]["params"]["type"])

    def _arms_before(self, index):
        """Indices of the arms above a step, nearest first."""
        out = []
        for i in range(index - 1, -1, -1):
            if is_arm(self.steps[i]["params"]["type"]):
                out.append(i)
        return out

    def bracket_span(self, index):
        """(top row, bottom row) a transform's scope covers, or None."""
        params = self.steps[index]["params"]
        if self._kind(index) != "transform":
            return None
        scope = params.get("scope", "all")
        if scope == "all":
            return (0, index) if index > 0 else None
        k = int(scope)
        arms = self._arms_before(index)
        if k == 0 or not arms:
            return None
        top = arms[min(k, len(arms)) - 1]
        return (top, index)

    # -- painting ------------------------------------------------------------------ #

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(theme.PANEL))
        if not self.steps:
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "No steps yet — add an arm to start the machine.")
            painter.end()
            return

        width = self.width()
        for index, step in enumerate(self.steps):
            top = index * ROW
            rect = QRectF(GUTTER, top + 2, width - GUTTER - 2, ROW - 4)
            kind = self._kind(index)
            color = glyphs.KIND_COLORS[kind]

            if index == self.selection:
                painter.fillRect(rect, QColor(theme.ACCENT_DIM).darker(130))
                painter.setPen(QPen(QColor(theme.ACCENT), 1))
                painter.drawRoundedRect(rect, 4, 4)
            elif index == self.hover:
                painter.fillRect(rect, QColor(theme.PANEL_HI))
            else:
                painter.fillRect(rect, QColor(theme.PANEL_HI).darker(108))

            # the kind bar and glyph
            painter.fillRect(QRectF(rect.left(), rect.top(), BAR, rect.height()), color)
            painter.setPen(color)
            painter.setFont(QFont("sans", 13))
            painter.drawText(QRectF(rect.left() + BAR + 4, rect.top(), 22, rect.height()),
                             Qt.AlignCenter, glyphs.KIND_GLYPHS[kind])

            # name and the numbers
            params = step["params"]
            spec = MODULE_DEFS.get(params["type"], {})
            text_left = rect.left() + BAR + 30
            text_width = rect.right() - THUMB - PAD * 2 - text_left
            painter.setPen(QColor(theme.TEXT))
            painter.setFont(QFont("sans", 10, QFont.DemiBold))
            painter.drawText(QRectF(text_left, rect.top() + 4, text_width, 16),
                             Qt.AlignLeft | Qt.AlignVCenter,
                             "%d.  %s" % (index + 1, spec.get("label", params["type"])))
            painter.setPen(QColor(theme.MUTED))
            painter.setFont(QFont("sans", 8))
            summary = summarise(params)
            if kind == "transform":
                scope = params.get("scope", "all")
                summary = ("on everything" if scope == "all" else
                           "on the last arm" if int(scope) == 1 else
                           "on the last %d arms" % int(scope)) + (" · " + summary if summary else "")
            metrics = painter.fontMetrics()
            painter.drawText(QRectF(text_left, rect.top() + 22, text_width, 16),
                             Qt.AlignLeft | Qt.AlignVCenter,
                             metrics.elidedText(summary, Qt.ElideRight, int(text_width)))

            # the drawing after this step
            thumb = QRectF(rect.right() - THUMB - PAD, rect.top() + (rect.height() - THUMB) / 2,
                           THUMB, THUMB)
            painter.fillRect(thumb, QColor(theme.BG))
            paths = self.stage_paths[index] if index < len(self.stage_paths) else None
            if paths:
                thumbs.draw_into(painter, thumb, paths, color if kind != "clock" else QColor(theme.TEXT))
            else:
                painter.setPen(QColor(theme.LINE))
                painter.drawRect(thumb)

        # scope brackets, drawn last so they sit over the cards' left edge;
        # when brackets nest, the wider one sits further out
        spans = [(index, self.bracket_span(index)) for index in range(len(self.steps))]
        spans = [(index, span) for index, span in spans if span is not None]
        lengths = sorted({span[1] - span[0] for _, span in spans}, reverse=True)
        for index, span in spans:
            top_row, bottom_row = span
            rank = min(lengths.index(bottom_row - top_row), 3)
            x = 3 + 4 * rank
            y0 = top_row * ROW + 6
            y1 = bottom_row * ROW + ROW - 6
            color = QColor(glyphs.KIND_COLORS["transform"])
            if self.steps[index]["params"].get("scope", "all") == "all":
                color.setAlpha(150)
            pen = QPen(color, 2.2 if index == self.selection else 1.5)
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y0), QPointF(x, y1))
            painter.drawLine(QPointF(x, y0), QPointF(x + 5, y0))
            painter.drawLine(QPointF(x, y1), QPointF(x + 5, y1))
        painter.end()

    # -- interaction ------------------------------------------------------------------ #

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            index = self.row_at(event.position().y())
            self.selection = index
            self.update()
            self.selected.emit(index)

    def mouseMoveEvent(self, event):
        index = self.row_at(event.position().y())
        if index != self.hover:
            self.hover = index
            self.update()
            self.hovered.emit(index)
            if index is not None:
                params = self.steps[index]["params"]
                kind = self._kind(index)
                word, what = glyphs.KIND_WORDS[kind]
                self.setToolTip("%s — %s\n%s" % (word, what, glyphs.plain(params["type"])))
            else:
                self.setToolTip("")

    def leaveEvent(self, event):
        self.hover = None
        self.update()
        self.hovered.emit(None)
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        if self.selection is None:
            return super().keyPressEvent(event)
        if event.key() == Qt.Key_Up and event.modifiers() & Qt.AltModifier:
            self.moveRequested.emit(self.selection, -1)
        elif event.key() == Qt.Key_Down and event.modifiers() & Qt.AltModifier:
            self.moveRequested.emit(self.selection, 1)
        elif event.key() == Qt.Key_Up:
            self.select(max(self.selection - 1, 0))
            self.selected.emit(self.selection)
        elif event.key() == Qt.Key_Down:
            self.select(min(self.selection + 1, len(self.steps) - 1))
            self.selected.emit(self.selection)
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.removeRequested.emit(self.selection)
        else:
            super().keyPressEvent(event)
