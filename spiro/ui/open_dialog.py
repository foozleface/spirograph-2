"""File -> Open, as pictures.

A file name says little about what a pattern looks like, and the newest one
— the one just saved — was the last line of a long list. This shows every
pattern and sheet in the project drawn, newest first, with when it was
saved under each; a filter narrows it by name or by what it is made of.
A sheet is drawn as its paper with every pattern on it in its pen's ink.

The pictures are rendered on the window's thumbnail thread and kept for the
session, keyed by the file and its timestamp, so opening the dialog a
second time is instant and a file saved since is drawn again.
"""

import datetime
import os
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout)

from spiro.pipeline.document import Document
from spiro.scene import SHEET_SUFFIX, Scene
from spiro.scene.item import PlacedItem
from spiro.ui import theme, thumbs
from spiro.ui.ideas_panel import describe
from spiro.ui.widgets import row

THUMB = 150
SAMPLING = {"initial_samples": 16000, "output_samples": 3000}
SKIP = {".venv", "venv", ".git", "__pycache__", "node_modules", "test-results",
        ".idea", ".vscode", "docs", "tests", "output", "axiplot", "spiro"}
SHEET_POINTS = 3000        # per pattern on a sheet's picture

_pictures = {}             # (path, mtime) -> QPixmap, for the session


def project_files(root):
    """Every pattern and sheet under ``root``, as ``[(path, mtime)]``."""
    found = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith("."))
        for name in names:
            if name.startswith("_"):
                continue
            if name.endswith(".ini") or name.endswith(SHEET_SUFFIX):
                path = Path(folder) / name
                try:
                    found.append((path, path.stat().st_mtime))
                except OSError:
                    pass
    return found


def when(mtime, now=None):
    """'today 08:20', 'yesterday', 'Mon', '26 Jun', '26 Jun 2024'."""
    now = now or datetime.datetime.now()
    then = datetime.datetime.fromtimestamp(mtime)
    days = (now.date() - then.date()).days
    if days == 0:
        return "today %s" % then.strftime("%H:%M")
    if days == 1:
        return "yesterday"
    if 1 < days < 7:
        return then.strftime("%a")
    if then.year == now.year:
        return then.strftime("%-d %b")
    return then.strftime("%-d %b %Y")


def sheet_picture(data, drawings, size=THUMB):
    """The sheet as a small picture: the paper, and every pattern on it in
    its pen's colour, where it was placed."""
    paper = data.get("paper", {})
    pw = float(paper.get("width_mm", 297) or 297)
    ph = float(paper.get("height_mm", 210) or 210)
    pens = data.get("pens", [])
    pix = QPixmap(size, size)
    pix.fill(theme.CANVAS_BG)
    scale = (size - 8) / max(pw, ph)
    ox = (size - pw * scale) / 2
    oy = (size - ph * scale) / 2
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.fillRect(int(ox), int(oy), int(pw * scale), int(ph * scale),
                     QColor("#f4f1ea"))
    for entry, drawing in zip(data.get("items", []), drawings):
        if drawing is None or not entry.get("visible", True):
            continue
        item = PlacedItem.from_dict(entry, drawing)
        pen_index = int(entry.get("pen", 0))
        color = QColor(pens[pen_index]["color"]) if pen_index < len(pens) else QColor("#000")
        line = QPen(color, 0.8)
        line.setCosmetic(True)
        painter.setPen(line)
        paths = item.paths_mm()
        total = sum(len(p) for p in paths)
        stride = max(1, total // SHEET_POINTS)
        outline = QPainterPath()
        for points in paths:
            points = np.asarray(points)[::stride]
            if len(points) < 2:
                continue
            outline.moveTo(QPointF(ox + points[0].real * scale, oy + points[0].imag * scale))
            for p in points[1:]:
                outline.lineTo(QPointF(ox + p.real * scale, oy + p.imag * scale))
        painter.drawPath(outline)
    painter.end()
    return pix


class OpenDialog(QDialog):
    """Every pattern and sheet in the project, as pictures."""

    thumbnailsWanted = Signal(object)    # [(key, ini_text)] for the thumbnail thread

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self.chosen = None
        self.items = {}                  # str(path) -> QListWidgetItem
        self.waiting = {}                # str(path) -> what it still needs
        self.setWindowTitle("Open a pattern or a sheet")
        self.resize(1040, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter by name or part…")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply_filter)
        self.order = QComboBox()
        self.order.addItems(["Newest first", "By name"])
        self.order.currentIndexChanged.connect(lambda _i: self._sort())
        layout.addWidget(row(self.filter, self.order, spacing=6, stretch_last=False))

        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(THUMB, THUMB))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setSpacing(4)
        self.grid.setWordWrap(True)
        self.grid.setUniformItemSizes(True)
        self.grid.setGridSize(QSize(THUMB + 24, THUMB + 48))
        self.grid.setStyleSheet(
            "QListWidget { background: %s; border: 1px solid %s; border-radius: 4px; }"
            "QListWidget::item { color: %s; }"
            "QListWidget::item:selected { background: %s; border-radius: 4px; }"
            % (theme.PANEL_HI, theme.LINE, theme.TEXT, theme.ACCENT_DIM))
        self.grid.itemActivated.connect(self._open_item)
        self.grid.itemDoubleClicked.connect(self._open_item)
        self.grid.itemSelectionChanged.connect(
            lambda: self.open_button.setEnabled(bool(self.grid.selectedItems())))
        layout.addWidget(self.grid, 1)

        self.count = theme.muted("")
        elsewhere = QPushButton("Other location…")
        elsewhere.setToolTip("Open a pattern or sheet from outside the project")
        elsewhere.clicked.connect(self._elsewhere)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.open_button = QPushButton("Open")
        self.open_button.setObjectName("primary")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(
            lambda: self._open_item(self.grid.currentItem()))
        layout.addWidget(row(self.count, 1, elsewhere, cancel, self.open_button,
                             spacing=6))
        self._wanted = []
        self.refresh()

    # -- filling ------------------------------------------------------------------ #

    def refresh(self):
        """Read the project again: the window keeps one of these for the
        session, so renders still arriving after it closed are kept."""
        self.chosen = None
        self.grid.clear()
        self.items = {}
        wanted = []
        for path, mtime in project_files(self.root):
            is_sheet = path.name.endswith(SHEET_SUFFIX)
            stem = path.name[:-len(SHEET_SUFFIX)] if is_sheet else path.stem
            relative = path.relative_to(self.root)
            folder = "" if str(relative.parent) == "." else str(relative.parent) + "/"
            item = QListWidgetItem("%s\n%s%s" % (stem, "sheet · " if is_sheet else "",
                                                 when(mtime)))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            item.setData(Qt.UserRole, str(path))
            item.setData(Qt.UserRole + 2, mtime)
            item.setData(Qt.UserRole + 3, stem.lower())
            key = (str(path), mtime)
            words = ""
            try:
                if is_sheet:
                    data = Scene.read(path)
                    names = [entry.get("name", "?") for entry in data.get("items", [])]
                    words = "sheet · %d pattern%s: %s" % (
                        len(names), "" if len(names) == 1 else "s", ", ".join(names))
                    if key not in _pictures and not self._asked(path, mtime):
                        inis = [Document.from_ini(entry["ini"]).to_ini(SAMPLING)
                                for entry in data.get("items", [])]
                        self.waiting[str(path)] = {"data": data, "mtime": mtime,
                                                   "drawings": [None] * len(inis),
                                                   "left": len(inis)}
                        wanted += [(("open", (str(path), index)), ini)
                                   for index, ini in enumerate(inis)]
                else:
                    document = Document.load(path)
                    words = describe(document)
                    if key not in _pictures and not self._asked(path, mtime):
                        self.waiting[str(path)] = {"mtime": mtime}
                        wanted.append((("open", (str(path), None)),
                                       document.to_ini(SAMPLING)))
            except Exception as exc:
                words = "could not read it: %s" % exc
                item.setText(item.text() + " ✗")
            item.setData(Qt.UserRole + 1, words)
            item.setToolTip("%s%s\n%s" % (folder, path.name, words))
            item.setIcon(QIcon(_pictures.get(key) or self._blank()))
            self.grid.addItem(item)
            self.items[str(path)] = item
        self._sort()
        self._apply_filter(self.filter.text())
        self._wanted = wanted

    def _asked(self, path, mtime):
        """Already on its way from the thumbnail thread?"""
        state = self.waiting.get(str(path))
        return state is not None and state["mtime"] == mtime

    def request_thumbnails(self):
        """Ask for the pictures not already kept. Called once the window has
        connected thumbnailsWanted."""
        if self._wanted:
            # newest first, so the file just saved is drawn before the rest
            order = {path: self.items[path].data(Qt.UserRole + 2) for path in self.items}
            self._wanted.sort(key=lambda job: -order.get(job[0][1][0], 0))
            self.thumbnailsWanted.emit(list(self._wanted))
            self._wanted = []

    @staticmethod
    def _blank():
        pix = QPixmap(THUMB, THUMB)
        pix.fill(theme.CANVAS_BG)
        return pix

    def deliver(self, ref, drawing):
        """A render came back: ``ref`` is ``(path, None)`` for a pattern or
        ``(path, index)`` for one pattern of a sheet."""
        path, index = ref
        state = self.waiting.get(path)
        if state is None:
            return
        if index is None:
            ink = QColor(theme.TEXT)
            ink.setAlpha(170)
            picture = thumbs.pixmap(drawing.paths, THUMB, ink,
                                    background=theme.CANVAS_BG, pad=8, width=0.7)
        else:
            state["drawings"][index] = drawing
            state["left"] -= 1
            if state["left"] > 0:
                return
            picture = sheet_picture(state["data"], state["drawings"])
        self._show(path, state, picture)

    def failed(self, ref, message):
        path, index = ref
        state = self.waiting.get(path)
        if state is None:
            return
        if index is not None:
            # a sheet is drawn without the one pattern that would not draw
            state["left"] -= 1
            if state["left"] <= 0:
                self._show(path, state, sheet_picture(state["data"], state["drawings"]))
            return
        del self.waiting[path]
        item = self.items.get(path)
        if item is not None:
            item.setToolTip(item.toolTip() + "\ncould not draw it: %s" % message)

    def _show(self, path, state, picture):
        del self.waiting[path]
        _pictures[(path, state["mtime"])] = picture
        item = self.items.get(path)
        if item is not None:
            item.setIcon(QIcon(picture))

    # -- arranging ------------------------------------------------------------------ #

    def _sort(self):
        items = [self.grid.takeItem(0) for _ in range(self.grid.count())]
        if self.order.currentIndex() == 0:
            items.sort(key=lambda it: -it.data(Qt.UserRole + 2))
        else:
            items.sort(key=lambda it: it.data(Qt.UserRole + 3))
        for item in items:
            self.grid.addItem(item)
        self._apply_filter(self.filter.text())

    def _apply_filter(self, text):
        needle = text.strip().lower()
        shown = 0
        for index in range(self.grid.count()):
            item = self.grid.item(index)
            words = (item.text() + " " + (item.data(Qt.UserRole + 1) or "")).lower()
            match = not needle or needle in words
            item.setHidden(not match)
            shown += match
        self.count.setText("%d file%s" % (shown, "" if shown == 1 else "s"))

    # -- choosing ------------------------------------------------------------------ #

    def _open_item(self, item):
        if item is not None and item.data(Qt.UserRole):
            self.chosen = item.data(Qt.UserRole)
            self.accept()

    def _elsewhere(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open a pattern or a sheet", str(self.root),
            "Patterns and sheets (*.ini *%s);;Pattern files (*.ini);;"
            "Sheet files (*%s)" % (SHEET_SUFFIX, SHEET_SUFFIX))
        if path:
            self.chosen = path
            self.accept()
