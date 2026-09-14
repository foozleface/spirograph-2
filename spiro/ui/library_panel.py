"""Every pattern file in the project, one click away.

The web UI had a file browser and it was the fastest way to get somewhere
interesting; a modal Open dialog is not. This is the list, always there: every
`.ini` under the project, what its pipeline actually is, filtered as you type.
Sheet files (`*.sheet.json`, a whole arrangement on paper) are listed beside
them; opening one is the window's call, on the file's suffix.

Reading a hundred INI files to summarise them is cheap — they are a few hundred
bytes each — but it is done once and cached against the file's modification
time, so switching to this tab is instant and an edit still shows up.
"""

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QHeaderView,
                               QLabel, QLineEdit, QMessageBox, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                               QWidget)

from spiro.pipeline.document import Document
from spiro.scene import SHEET_SUFFIX, Scene
from spiro.ui import theme
from spiro.ui.widgets import row

# Where not to look. .venv alone holds tens of thousands of files.
SKIP = {".venv", "venv", ".git", "__pycache__", "node_modules", "test-results",
        ".idea", ".vscode", "docs"}


class LibraryPanel(QWidget):
    """A filtered tree of the project's `.ini` files, grouped by folder."""

    openRequested = Signal(str)          # a path to load
    statusMessage = Signal(str)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self._summaries = {}             # path -> (mtime, one-line summary)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        layout.addWidget(theme.h2("Patterns and sheets"))
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter by name or module…")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["File", "Pipeline"])
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Interactive, not ResizeToContents: one long filename would otherwise
        # take the whole panel and leave no room for what the pattern IS.
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.setColumnWidth(0, 148)
        self.tree.setTextElideMode(Qt.ElideRight)
        self.tree.itemActivated.connect(self._activated)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.setStyleSheet(
            "QTreeWidget { background: %s; border: 1px solid %s; border-radius: 4px; }"
            "QTreeWidget::item { padding: 2px 3px; }"
            "QTreeWidget::item:selected { background: %s; color: white; }"
            "QHeaderView::section { background: %s; border: none; color: %s;"
            "  padding: 3px 4px; }"
            % (theme.PANEL_HI, theme.LINE, theme.ACCENT_DIM, theme.PANEL,
               theme.MUTED))
        layout.addWidget(self.tree, 1)

        self.open_button = QPushButton("Open")
        self.open_button.setObjectName("primary")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self._open_selected)
        self.reveal = QPushButton("Elsewhere…")
        self.reveal.setToolTip("Open a pattern from outside the project")
        self.reveal.clicked.connect(self._open_elsewhere)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(row(self.open_button, self.reveal, 1,
                             self.refresh_button, spacing=4))

        self.count = theme.muted("")
        layout.addWidget(self.count)

        self.refresh()

    # -- scanning ------------------------------------------------------------ #

    def _files(self):
        found = []
        for folder, dirs, names in os.walk(self.root):
            dirs[:] = sorted(d for d in dirs
                             if d not in SKIP and not d.startswith("."))
            for name in sorted(names):
                if name.startswith("_"):
                    continue
                if name.endswith(".ini") or name.endswith(SHEET_SUFFIX):
                    found.append(Path(folder) / name)
        return found

    def _summary(self, path):
        """The pipeline in a line, cached against the file's own timestamp."""
        try:
            stamp = path.stat().st_mtime
        except OSError:
            return "unreadable"
        cached = self._summaries.get(path)
        if cached and cached[0] == stamp:
            return cached[1]
        try:
            if path.name.endswith(SHEET_SUFFIX):
                return self._sheet_summary(path, stamp)
            document = Document.load(path)
            steps = [document.describe_step(i) for i in range(len(document.steps))]
            text = " → ".join(steps) or "empty"
            if document.symmetry.get("n_fold", 1) > 1:
                text += "   ⟲%s" % document.symmetry["n_fold"]
            if "moire" in document.extras:
                text += "   moiré"
        except Exception as exc:
            text = "could not read it: %s" % exc
        self._summaries[path] = (stamp, text)
        return text

    def _sheet_summary(self, path, stamp):
        """A sheet in a line: how many patterns, on what paper."""
        try:
            data = Scene.read(path)
            items = data.get("items", [])
            paper = data.get("paper", {})
            text = "sheet · %d pattern%s on %s" % (
                len(items), "" if len(items) == 1 else "s",
                paper.get("label") or "%g x %g mm" % (paper.get("width_mm", 0),
                                                       paper.get("height_mm", 0)))
            names = ", ".join(entry.get("name", "?") for entry in items[:6])
            if names:
                text += " — " + names + (", …" if len(items) > 6 else "")
        except Exception as exc:
            text = "could not read it: %s" % exc
        self._summaries[path] = (stamp, text)
        return text

    def refresh(self):
        self.tree.clear()
        folders = {}
        total = 0
        for path in self._files():
            relative = path.relative_to(self.root)
            folder = str(relative.parent) if str(relative.parent) != "." else ""
            parent = folders.get(folder)
            if parent is None:
                if folder:
                    parent = QTreeWidgetItem(self.tree, [folder + "/", ""])
                    parent.setFirstColumnSpanned(False)
                    parent.setExpanded(True)
                    parent.setForeground(0, theme.SELECT)
                else:
                    parent = self.tree.invisibleRootItem()
                folders[folder] = parent
            is_sheet = path.name.endswith(SHEET_SUFFIX)
            stem = path.name[:-len(SHEET_SUFFIX)] if is_sheet else path.stem
            entry = QTreeWidgetItem(parent, [stem, self._summary(path)])
            entry.setData(0, Qt.UserRole, str(path))
            if is_sheet:
                entry.setForeground(0, theme.SELECT)
                entry.setToolTip(0, "A sheet: patterns placed on paper")
            entry.setToolTip(1, entry.text(1))
            total += 1
        self.count.setText("%d pattern%s" % (total, "" if total == 1 else "s"))
        self._apply_filter(self.filter.text())

    # -- filtering ------------------------------------------------------------- #

    def _apply_filter(self, text):
        needle = text.strip().lower()
        shown = 0
        for index in range(self.tree.topLevelItemCount()):
            shown += self._filter_item(self.tree.topLevelItem(index), needle)
        if needle:
            self.count.setText("%d match%s" % (shown, "" if shown == 1 else "es"))
        else:
            self.count.setText("%d pattern%s" % (shown, "" if shown == 1 else "s"))

    def _filter_item(self, item, needle):
        path = item.data(0, Qt.UserRole)
        if path is None:                     # a folder: shown if a child is
            visible = 0
            for index in range(item.childCount()):
                visible += self._filter_item(item.child(index), needle)
            item.setHidden(visible == 0)
            return visible
        match = (not needle
                 or needle in item.text(0).lower()
                 or needle in item.text(1).lower())
        item.setHidden(not match)
        return 1 if match else 0

    # -- opening ------------------------------------------------------------------ #

    def _selected_path(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _selection_changed(self):
        self.open_button.setEnabled(self._selected_path() is not None)

    def _activated(self, item, _column):
        path = item.data(0, Qt.UserRole)
        if path:
            self.openRequested.emit(path)
        else:
            item.setExpanded(not item.isExpanded())

    def _open_selected(self):
        path = self._selected_path()
        if path:
            self.openRequested.emit(path)

    def _open_elsewhere(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open a pattern or a sheet", str(self.root),
            "Patterns and sheets (*.ini *%s);;Pattern files (*.ini);;"
            "Sheet files (*%s)" % (SHEET_SUFFIX, SHEET_SUFFIX))
        if path:
            self.openRequested.emit(path)

    def select(self, path):
        """Highlight a file, if it is in the list — after it has been opened."""
        if not path:
            return
        wanted = str(Path(path).resolve())
        iterator = [self.tree.topLevelItem(i)
                    for i in range(self.tree.topLevelItemCount())]
        while iterator:
            item = iterator.pop()
            iterator += [item.child(i) for i in range(item.childCount())]
            stored = item.data(0, Qt.UserRole)
            if stored and str(Path(stored).resolve()) == wanted:
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
                return
