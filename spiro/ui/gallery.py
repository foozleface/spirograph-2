"""Add a step: a gallery of what every module draws.

A combo box of names told nobody what a Guilloche or a Geneva was. This is
a grid: each module drawn at its defaults, under its name, grouped by
kind — arms, carriage paths, table moves, clocks — with a line of plain
words on hover. Paths and moves are shown acting on a circle, since on
their own they draw nothing.

The thumbnails come from the engine itself at a small sampling — thirty
modules in well under a second, once, the first time the gallery opens.
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QScrollArea, QVBoxLayout,
                               QWidget)

from spiro.pipeline import build_ini, defaults_for, run
from spiro.pipeline.registry import CATEGORIES, MODULE_DEFS
from spiro.ui import glyphs, theme, thumbs

THUMB = 64
SAMPLING = {"initial_samples": 6000, "output_samples": 1500}
KIND_ORDER = ["generator", "path", "transform", "clock"]

_cache = {}          # module type -> Drawing


def drawing_for(module_type):
    """The module at its defaults, carrying a circle if it is not an arm."""
    if module_type not in _cache:
        params = defaults_for(module_type)
        steps = [{"kind": "single", "params": params}]
        if MODULE_DEFS[module_type]["category"] != "generator":
            steps = [{"kind": "single", "params": {"type": "circle", "radius": 40,
                                                   "cycles": 5}}] + steps
        _cache[module_type] = run(build_ini(steps=steps, sampling=SAMPLING))
    return _cache[module_type]


class GalleryDialog(QDialog):
    """Pick a module by its picture."""

    chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add a step")
        self.resize(760, 820)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter…")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        host = QWidget()
        self.host_layout = QVBoxLayout(host)
        self.host_layout.setContentsMargins(0, 0, 0, 0)
        self.host_layout.setSpacing(4)
        area.setWidget(host)
        layout.addWidget(area, 1)

        self.lists = {}
        self.headers = {}
        for kind in KIND_ORDER:
            word, what = glyphs.KIND_WORDS[kind]
            header = theme.h2("%s %s — %s" % (glyphs.KIND_GLYPHS[kind],
                                              CATEGORIES[kind]["label"], what))
            header.setStyleSheet("color: %s;" % glyphs.KIND_COLORS[kind].name())
            self.host_layout.addWidget(header)
            grid = QListWidget()
            grid.setViewMode(QListWidget.IconMode)
            grid.setIconSize(QSize(THUMB, THUMB))
            grid.setResizeMode(QListWidget.Adjust)
            grid.setMovement(QListWidget.Static)
            grid.setSpacing(6)
            grid.setWordWrap(True)
            grid.setUniformItemSizes(True)
            grid.setGridSize(QSize(THUMB + 52, THUMB + 38))
            grid.setStyleSheet(
                "QListWidget { background: %s; border: none; }"
                "QListWidget::item { color: %s; }"
                "QListWidget::item:selected { background: %s; border-radius: 4px; }"
                % (theme.PANEL, theme.TEXT, theme.ACCENT_DIM))
            grid.itemActivated.connect(self._pick)
            grid.itemClicked.connect(self._pick)
            self.host_layout.addWidget(grid)
            self.lists[kind] = grid
            self.headers[kind] = header
        self.host_layout.addStretch(1)

        self.note = theme.muted("Click a picture to add it after the selected step.", wrap=True)
        layout.addWidget(self.note)
        self._filled = False

    def showEvent(self, event):
        if not self._filled:
            self._fill()
        super().showEvent(event)

    def _fill(self):
        for kind, grid in self.lists.items():
            grid.clear()
            for name, spec in sorted(MODULE_DEFS.items(), key=lambda kv: kv[1]["label"]):
                if spec["category"] != kind:
                    continue
                drawing = drawing_for(name)
                pix = thumbs.pixmap(drawing.paths, THUMB, glyphs.KIND_COLORS[kind],
                                    background=theme.CANVAS_BG, width=0.9)
                item = QListWidgetItem(QIcon(pix), spec["label"])
                item.setData(Qt.UserRole, name)
                item.setToolTip("%s\n%s" % (spec["label"], glyphs.plain(name)))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
                grid.addItem(item)
            grid.setFixedHeight(self._height_for(grid))
        self._filled = True

    def _height_for(self, grid):
        count = grid.count()
        if not count:
            return 0
        columns = max(1, (self.width() - 40) // (THUMB + 58))
        rows = (count + columns - 1) // columns
        return rows * (THUMB + 44) + 8

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._filled:
            for grid in self.lists.values():
                grid.setFixedHeight(self._height_for(grid))

    def _apply_filter(self, text):
        needle = text.strip().lower()
        for kind, grid in self.lists.items():
            shown = 0
            for index in range(grid.count()):
                item = grid.item(index)
                match = (not needle or needle in item.text().lower()
                         or needle in glyphs.plain(item.data(Qt.UserRole)).lower())
                item.setHidden(not match)
                shown += match
            self.headers[kind].setVisible(shown > 0)
            grid.setVisible(shown > 0)

    def _pick(self, item):
        self.chosen.emit(item.data(Qt.UserRole))
        self.accept()
