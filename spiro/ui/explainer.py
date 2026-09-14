"""What a knob does, as pictures.

Two hundred parameters is too many to draw an icon for by hand, and a
hand-drawn icon would be wrong the day the module changed. So the explainer
asks the engine: the selected step, on its own (a circle carries a path,
a table move or a clock, as in the gallery), rendered at a sweep of values
of one parameter — lower, current, higher — in a row of small pictures with
the value under each and the current one marked. Hover any row in the
parameter list and the card shows that knob. A bool shows off and on; a
choice shows every choice; a drift end shows the drift to each value.

The renders run on the window's thumbnail thread and are cached by the INI
text they came from, so a knob you have looked at costs nothing to look at
again.
"""

from collections import OrderedDict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

import math

from spiro.pipeline import build_ini
from spiro.ui import glyphs, theme, thumbs
from spiro.ui.gallery import carried

THUMB = 52
SAMPLING = {"initial_samples": 5000, "output_samples": 1200}
STEPS = 5                  # pictures per numeric sweep
CACHE = 400                # renders remembered


def sweep_values(spec, current):
    """The values to show for one parameter, current included."""
    kind = spec.get("type", "float")
    if kind == "bool":
        return [False, True]
    if kind == "choice":
        return list(spec.get("choices", []))[:8]
    if kind not in ("int", "float"):
        return [current]
    low = float(spec.get("min", -1e6))
    high = float(spec.get("max", 1e6))
    span = high - low
    if span > 1e5:                       # an open-ended range: sweep around the value
        span = max(abs(float(current)) * 4, 4 * float(spec.get("step", 1) or 1))
    current = float(current)
    offsets = [-span / 4, -span / 12, 0, span / 12, span / 4]
    values = []
    for offset in offsets:
        value = current + offset
        if offset:
            value = nice(value)
        value = min(max(value, low), high)
        if kind == "int":
            value = int(round(value))
        else:
            value = float("%.4g" % value)
        if value not in values:
            values.append(value)
    return values


def nice(value):
    """A round number near ``value``: 0.525 -> 0.5, 3.825 -> 4, 2160 -> 2000."""
    if value == 0:
        return 0.0
    magnitude = 10 ** math.floor(math.log10(abs(value)))
    unit = magnitude / 2.0
    return round(value / unit) * unit


def explain_steps(params, name, value):
    """The steps to render: the step alone with ``name`` set to ``value``,
    carried the way the gallery carries it."""
    trial = dict(params)
    trial[name] = value
    return carried(trial)


def explain_jobs(params, name, spec):
    """``[(value, ini_text)]`` for the sweep of one parameter."""
    current = params.get(name, spec.get("default"))
    out = []
    for value in sweep_values(spec, current):
        try:
            ini = build_ini(steps=explain_steps(params, name, value),
                            sampling=SAMPLING)
        except ValueError:
            continue                     # a value the module refuses
        out.append((value, ini))
    return out


def _label(value):
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, float):
        return "%g" % value
    return str(value)


class ExplainerCard(QWidget):
    """One parameter, as a row of pictures."""

    renderWanted = Signal(object)        # [(key, ini)] for the thumbnail thread

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache = OrderedDict()       # ini text -> Drawing
        self.pending = {}                # ini text -> (slot index)
        self.params = None
        self.name = None
        self.spec = None
        self.jobs = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(3)
        self.title = QLabel("")
        self.title.setObjectName("muted")
        self.title.setWordWrap(True)
        layout.addWidget(self.title)
        self.row_host = QWidget()
        self.row = QHBoxLayout(self.row_host)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(4)
        layout.addWidget(self.row_host)
        self.slots = []
        self.setVisible(False)

    # -- showing a parameter ------------------------------------------------- #

    def show_param(self, params, name, spec, kind):
        """Show the sweep for ``name`` of the step ``params`` describes."""
        if spec.get("type") == "scope":
            return
        self.params, self.name, self.spec = params, name, spec
        self.jobs = explain_jobs(params, name, spec)
        current = params.get(name, spec.get("default"))
        what = spec.get("desc") or name.replace("_", " ")
        self.title.setText("%s — %s from low to high, now %s"
                           % (glyphs.KIND_GLYPHS[kind], what, _label(current)))
        self._lay_out(len(self.jobs))
        wanted = []
        for index, (value, ini) in enumerate(self.jobs):
            slot = self.slots[index]
            slot.set_value(_label(value), value == current)
            if ini in self.cache:
                self.cache.move_to_end(ini)
                slot.set_drawing(self.cache[ini], glyphs.KIND_COLORS[kind])
            else:
                slot.set_drawing(None, glyphs.KIND_COLORS[kind])
                self.pending[ini] = (index, kind)
                wanted.append((("explain", ini), ini))
        self.setVisible(bool(self.jobs))
        if wanted:
            self.renderWanted.emit(wanted)

    def refresh(self):
        """The value changed under us: re-show the same knob."""
        if self.params is not None and self.name is not None:
            kind = glyphs.kind_of(self.params["type"])
            self.show_param(self.params, self.name, self.spec, kind)

    def deliver(self, ini, drawing):
        """A render came back from the thread."""
        self.cache[ini] = drawing
        while len(self.cache) > CACHE:
            self.cache.popitem(last=False)
        entry = self.pending.pop(ini, None)
        if entry is None:
            return
        index, kind = entry
        if index < len(self.jobs) and self.jobs[index][1] == ini:
            self.slots[index].set_drawing(drawing, glyphs.KIND_COLORS[kind])

    def fail(self, ini, message):
        entry = self.pending.pop(ini, None)
        if entry is not None:
            index, _ = entry
            if index < len(self.slots):
                self.slots[index].set_failed(message)

    def _lay_out(self, count):
        while len(self.slots) < count:
            slot = Slot()
            self.slots.append(slot)
            self.row.addWidget(slot)
        for index, slot in enumerate(self.slots):
            slot.setVisible(index < count)


class Slot(QWidget):
    """One picture and its value."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.picture = QLabel()
        self.picture.setFixedSize(THUMB, THUMB)
        self.picture.setAlignment(Qt.AlignCenter)
        self.value = QLabel("")
        self.value.setAlignment(Qt.AlignHCenter)
        self.value.setObjectName("muted")
        layout.addWidget(self.picture, 0, Qt.AlignHCenter)
        layout.addWidget(self.value)
        self.current = False

    def set_value(self, text, current):
        self.current = current
        self.value.setText(text)
        self.value.setStyleSheet("color: %s; font-weight: %s;"
                                 % (theme.TEXT if current else theme.MUTED,
                                    "600" if current else "400"))

    def set_drawing(self, drawing, color):
        if drawing is None:
            pix = QPixmap(THUMB, THUMB)
            pix.fill(theme.CANVAS_BG)
        else:
            pix = thumbs.pixmap(drawing.paths, THUMB, color,
                                background=theme.CANVAS_BG, pad=5, width=0.9)
        if self.current:
            painter = QPainter(pix)
            painter.setPen(QPen(QColor(theme.ACCENT), 2))
            painter.drawRect(1, 1, THUMB - 2, THUMB - 2)
            painter.end()
        self.picture.setPixmap(pix)
        self.picture.setToolTip("")

    def set_failed(self, message):
        pix = QPixmap(THUMB, THUMB)
        pix.fill(theme.CANVAS_BG)
        painter = QPainter(pix)
        painter.setPen(QColor(theme.ERR))
        painter.drawText(pix.rect(), Qt.AlignCenter, "✗")
        painter.end()
        self.picture.setPixmap(pix)
        self.picture.setToolTip("could not draw it: %s" % message)
