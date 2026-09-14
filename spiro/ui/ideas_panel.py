"""Ideas: the combinations that turned out well, as pictures.

A list of file names says nothing about what is worth opening. This is the
same files as pictures — every pattern in the project drawn small, with
what it is made of underneath in the machine's own words: which arms,
which moves, what finishing. The hand-made ones (``joe_fun/``, the tests at
the top of the tree, ``claude_autogen/``) come first because they are the
ones a person liked enough to keep; the examples follow.

The pictures are rendered by the window's worker thread after the window
is up, so opening the tab costs nothing; until they arrive the cards show
their words.
"""

import os
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (QLineEdit, QListWidget, QListWidgetItem,
                               QVBoxLayout, QWidget)

from spiro.pipeline.document import Document
from spiro.pipeline.registry import MODULE_DEFS
from spiro.ui import glyphs, theme, thumbs

THUMB = 80
SAMPLING = {"initial_samples": 16000, "output_samples": 3000}
SKIP = {".venv", "venv", ".git", "__pycache__", "node_modules", "test-results",
        ".idea", ".vscode", "docs", "tests", "output", "axiplot", "spiro"}
# Folders in the order they should appear; anything else after, alphabetically.
FIRST = ["joe_fun", "", "claude_autogen", "compositions", "examples"]


def describe(document):
    """What a pattern is made of, in the machine's words."""
    arms, paths, moves, clocks = [], [], [], []
    for step in document.steps:
        if step.get("kind") != "single":
            continue
        module_type = step["params"]["type"]
        label = MODULE_DEFS.get(module_type, {}).get("label", module_type)
        {"generator": arms, "path": paths, "transform": moves,
         "clock": clocks}[glyphs.kind_of(module_type)].append(label)
    parts = []
    if arms:
        parts.append("%s %s" % (glyphs.KIND_GLYPHS["generator"], " + ".join(arms)))
    if paths:
        parts.append("%s %s" % (glyphs.KIND_GLYPHS["path"], ", ".join(paths)))
    if moves:
        parts.append("%s %s" % (glyphs.KIND_GLYPHS["transform"], ", ".join(moves)))
    if clocks:
        parts.append("%s %s" % (glyphs.KIND_GLYPHS["clock"], ", ".join(clocks)))
    finishing = []
    fold = int(document.symmetry.get("n_fold", 1) or 1) if document.symmetry else 1
    if fold > 1:
        finishing.append("%d-fold" % fold)
    for name in ("pen_lift", "moire", "tile", "clip"):
        if name in document.extras:
            finishing.append(name.replace("_", " "))
    if finishing:
        parts.append("%s %s" % (glyphs.KIND_GLYPHS["finish"], ", ".join(finishing)))
    return "\n".join(parts)


class IdeasPanel(QWidget):
    """A gallery of the project's patterns."""

    openRequested = Signal(str)
    thumbnailsWanted = Signal(object)     # [(path, ini_text)] to render

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self.items = {}                   # path -> QListWidgetItem

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.addWidget(theme.h2("Ideas"))
        layout.addWidget(theme.muted(
            "Combinations that turned out well. Click one to load it into "
            "Build and take it somewhere else.", wrap=True))
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter by name or part…")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter)

        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(THUMB, THUMB))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setSpacing(0)
        self.grid.setWordWrap(True)
        # The list has 6 px of stylesheet padding a side and a scrollbar;
        # three of these fit the 320 px panel.
        self.grid.setGridSize(QSize(THUMB + 16, THUMB + 40))
        self.grid.setStyleSheet(
            "QListWidget { background: %s; border: 1px solid %s; border-radius: 4px; }"
            "QListWidget::item { color: %s; }"
            "QListWidget::item:selected { background: %s; border-radius: 4px; }"
            % (theme.PANEL_HI, theme.LINE, theme.TEXT, theme.ACCENT_DIM))
        self.grid.itemActivated.connect(self._open)
        self.grid.itemDoubleClicked.connect(self._open)
        layout.addWidget(self.grid, 1)
        self.count = theme.muted("")
        layout.addWidget(self.count)
        self._requested = False
        self.refresh()

    # -- scanning ------------------------------------------------------------------ #

    def _files(self):
        found = []
        for folder, dirs, names in os.walk(self.root):
            dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith("."))
            for name in sorted(names):
                if name.endswith(".ini") and not name.startswith("_"):
                    found.append(Path(folder) / name)

        def key(path):
            rel = str(path.relative_to(self.root).parent)
            rel = "" if rel == "." else rel.split("/")[0]
            order = FIRST.index(rel) if rel in FIRST else len(FIRST)
            return (order, rel, path.name)
        return sorted(found, key=key)

    def refresh(self):
        self.grid.clear()
        self.items = {}
        wanted = []
        for path in self._files():
            try:
                document = Document.load(path)
                words = describe(document)
                ini = document.to_ini(SAMPLING)
            except Exception as exc:
                words = "could not read it: %s" % exc
                ini = None
            item = QListWidgetItem(path.stem)
            item.setData(Qt.UserRole, str(path))
            item.setData(Qt.UserRole + 1, words)
            item.setToolTip("%s\n%s" % (path.relative_to(self.root), words))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            placeholder = QPixmap(THUMB, THUMB)
            placeholder.fill(theme.CANVAS_BG)
            item.setIcon(QIcon(placeholder))
            self.grid.addItem(item)
            self.items[str(path)] = item
            if ini:
                wanted.append((str(path), ini))
        self.count.setText("%d pattern%s" % (len(self.items), "" if len(self.items) == 1 else "s"))
        self._wanted = wanted
        self._requested = False
        self._arrived = 0

    def request_thumbnails(self):
        """Ask (once) for the pictures; the window renders them off-thread."""
        if not self._requested and self._wanted:
            self._requested = True
            self.thumbnailsWanted.emit(list(self._wanted))

    def set_thumbnail(self, path, drawing):
        item = self.items.get(str(path))
        if item is None:
            return
        ink = QColor(theme.TEXT)
        ink.setAlpha(150)               # dense patterns shade rather than fill
        item.setIcon(QIcon(thumbs.pixmap(drawing.paths, THUMB, ink,
                                         background=theme.CANVAS_BG, width=0.7)))
        self._arrived += 1
        self.count.setText("%d pattern%s · %d picture%s so far" % (
            len(self.items), "" if len(self.items) == 1 else "s",
            self._arrived, "" if self._arrived == 1 else "s")
            if self._arrived < len(self._wanted) else
            "%d pattern%s" % (len(self.items), "" if len(self.items) == 1 else "s"))

    def set_failure(self, path, message):
        """A pattern the engine refused: say so on its card."""
        item = self.items.get(str(path))
        if item is None:
            return
        item.setText(item.text() + " ✗")
        item.setToolTip("%s\ncould not draw it: %s" % (item.toolTip(), message))
        self._arrived += 1

    # -- filtering, opening ----------------------------------------------------------- #

    def _apply_filter(self, text):
        needle = text.strip().lower()
        shown = 0
        for index in range(self.grid.count()):
            item = self.grid.item(index)
            words = (item.text() + " " + (item.data(Qt.UserRole + 1) or "")).lower()
            match = not needle or needle in words
            item.setHidden(not match)
            shown += match
        self.count.setText("%d pattern%s" % (shown, "" if shown == 1 else "s"))

    def _open(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self.openRequested.emit(path)

    def select(self, path):
        item = self.items.get(str(Path(path))) if path else None
        if item is not None:
            self.grid.setCurrentItem(item)
