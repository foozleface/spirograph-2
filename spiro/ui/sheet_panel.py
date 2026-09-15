"""The sheet: which paper, what is on it, and which pen draws each thing.

Two lists side by side in one panel, because they are two views of the same
decision. The items list says *what* is on the paper and lets each one pick a
pen; the pens list says what a pen number means — the colour it draws in on
screen and the ink a person is expected to put in the holder when the plot
stops to ask.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QHeaderView, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from spiro.scene import PAPER_PRESETS, Paper
from spiro.scene.paper import AXIDRAW_MODELS
from spiro.scene.scene import DEFAULT_PEN_COLORS, Pen
from spiro.ui import theme
from spiro.ui.widgets import Swatch, row

MAX_PENS = len(DEFAULT_PEN_COLORS)


class SheetPanel(QWidget):
    """Paper size, the placed items, and the pen list."""

    sceneChanged = Signal()               # redraw the canvas
    selectionChanged = Signal(object)     # item_id or None
    paperChanged = Signal()
    cleared = Signal()
    saveSheetRequested = Signal()
    openSheetRequested = Signal()

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # -- paper ----------------------------------------------------------- #
        layout.addWidget(theme.h2("Paper"))
        self.model = QComboBox()
        for model, spec in sorted(AXIDRAW_MODELS.items()):
            self.model.addItem("%s  —  %.0f x %.0f mm"
                               % (spec["label"], spec["width_in"] * 25.4,
                                  spec["height_in"] * 25.4), model)
        self.model.setCurrentIndex(2)     # the XLX, the wide one
        self.model.currentIndexChanged.connect(self._model_changed)
        layout.addWidget(self.model)

        self.preset = QComboBox()
        self.preset.addItem("Use the machine's full bed", None)
        for name in PAPER_PRESETS:
            self.preset.addItem(name + " portrait", (name, False))
            self.preset.addItem(name + " landscape", (name, True))
        self.preset.currentIndexChanged.connect(self._preset_changed)
        layout.addWidget(self.preset)

        self.margin = QDoubleSpinBox()
        self.margin.setRange(0, 100000)      # a number box is not the place for limits
        self.margin.setSuffix(" mm")
        self.margin.setDecimals(1)
        self.margin.valueChanged.connect(self._margin_changed)
        layout.addWidget(row(QLabel("Margin"), 1, self.margin))
        self.paper_note = theme.muted("", wrap=True)
        layout.addWidget(self.paper_note)

        # -- items ------------------------------------------------------------ #
        layout.addWidget(theme.hline())
        layout.addWidget(theme.h2("On the paper"))
        self.items = QTableWidget(0, 5)
        self.items.setHorizontalHeaderLabels(["", "Pattern", "Size", "At", "Pen"])
        self.items.verticalHeader().setVisible(False)
        self.items.setShowGrid(False)
        self.items.setSelectionBehavior(QTableWidget.SelectRows)
        self.items.setSelectionMode(QTableWidget.SingleSelection)
        self.items.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items.setStyleSheet(
            "QTableWidget { background: %s; border: 1px solid %s; border-radius: 4px; }"
            "QHeaderView::section { background: %s; border: none; color: %s;"
            "  padding: 3px 4px; }"
            "QTableWidget::item { padding: 2px 4px; }"
            "QTableWidget::item:selected { background: %s; color: white; }"
            % (theme.PANEL_HI, theme.LINE, theme.PANEL, theme.MUTED, theme.ACCENT_DIM))
        header = self.items.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for column in (2, 3, 4):
            header.setSectionResizeMode(column, QHeaderView.Fixed)
        self.items.setColumnWidth(0, 24)
        self.items.setColumnWidth(2, 62)
        self.items.setColumnWidth(3, 62)
        self.items.setColumnWidth(4, 92)
        self.items.itemSelectionChanged.connect(self._row_selected)
        layout.addWidget(self.items, 1)

        self.remove = QPushButton("Remove")
        self.remove.setObjectName("danger")
        self.remove.clicked.connect(self._remove_selected)
        self.duplicate = QPushButton("Copy")
        self.duplicate.setToolTip("Place another of this pattern, on the next pen")
        self.duplicate.clicked.connect(self._duplicate_selected)
        self.centre = QPushButton("Centre")
        self.centre.clicked.connect(self._centre_selected)
        self.fit = QPushButton("Fit")
        self.fit.setToolTip("Make it as large as the drawable area allows")
        self.fit.clicked.connect(self._fit_selected)
        self.clear = QPushButton("Clear")
        self.clear.setObjectName("danger")
        self.clear.setToolTip("Take everything off the sheet (Ctrl+Shift+Backspace)")
        self.clear.clicked.connect(self.clear_paper)
        layout.addWidget(row(self.centre, self.fit, self.duplicate, 1,
                             self.remove, self.clear, spacing=4))
        layout.addWidget(theme.muted(
            "Selecting a pattern brings its parameters into Build.", wrap=True))

        # -- the selected item, in numbers ----------------------------------- #
        # Dragging is for roughly; these are for exactly. Centre in mm from
        # the sheet's top-left, width in mm (the height follows the pattern's
        # own shape), and the angle about the centre.
        # Wide on purpose: a pattern may be parked off the sheet while an
        # arrangement is worked out, and a big one tiled down later. What is
        # actually off the drawable area is said in the status bar, which is
        # the honest place for it.
        self.sel_x = _mm_box(-100000, 100000)
        self.sel_y = _mm_box(-100000, 100000)
        self.sel_w = _mm_box(0.1, 100000)
        self.sel_rot = QDoubleSpinBox()
        self.sel_rot.setRange(0, 360)
        self.sel_rot.setDecimals(1)
        self.sel_rot.setSingleStep(1)       # a degree an arrow; type any tenth
        self.sel_rot.setToolTip(
            "Turn, in degrees. The arrows step one degree; type a tenth if you "
            "need one. On the paper, drag the knob above the item — shift "
            "snaps to fifteen — or press [ and ].")
        self.sel_rot.setSuffix("°")
        self.sel_rot.setWrapping(True)
        for box in (self.sel_x, self.sel_y, self.sel_w, self.sel_rot):
            box.valueChanged.connect(self._selected_edited)
        self.selected_box = QWidget()
        sel = QVBoxLayout(self.selected_box)
        sel.setContentsMargins(0, 0, 0, 0)
        sel.setSpacing(3)
        sel.addWidget(row(QLabel("Centre"), 1, self.sel_x, self.sel_y, spacing=4))
        sel.addWidget(row(QLabel("Width"), 1, self.sel_w, QLabel("Turn"),
                          self.sel_rot, spacing=4))
        layout.addWidget(self.selected_box)
        self.selected_box.setEnabled(False)

        # -- the sheet as a file ---------------------------------------------- #
        self.save_sheet = QPushButton("Save sheet…")
        self.save_sheet.setToolTip(
            "Write the paper, the pens and every pattern with its position, "
            "size and angle to a file (Ctrl+Shift+S)")
        self.save_sheet.clicked.connect(self.saveSheetRequested.emit)
        self.open_sheet = QPushButton("Open sheet…")
        self.open_sheet.setToolTip("Bring back a saved arrangement (Ctrl+Shift+O)")
        self.open_sheet.clicked.connect(self.openSheetRequested.emit)
        layout.addWidget(row(self.open_sheet, self.save_sheet, 1, spacing=4))

        # -- pens --------------------------------------------------------------- #
        layout.addWidget(theme.hline())
        layout.addWidget(theme.h2("Pens"))
        layout.addWidget(theme.muted(
            "One layer per pen, in this order. The plot stops between layers "
            "so the nib can be changed.", wrap=True))
        self.pens_host = QWidget()
        self.pens_layout = QVBoxLayout(self.pens_host)
        self.pens_layout.setContentsMargins(0, 0, 0, 0)
        self.pens_layout.setSpacing(3)
        layout.addWidget(self.pens_host)

        self.add_pen = QPushButton("Add pen")
        self.add_pen.clicked.connect(self._add_pen)
        layout.addWidget(row(1, self.add_pen))

        self.refresh()

    # -- paper ------------------------------------------------------------------ #

    def current_model(self):
        return self.model.currentData()

    def _apply_paper(self):
        model = self.current_model()
        choice = self.preset.currentData()
        if choice is None:
            paper = Paper.from_axidraw(model, self.margin.value())
        else:
            name, landscape = choice
            paper = Paper.preset(name, landscape, self.margin.value())
        self.scene.set_paper(paper, rescale=False)
        bed = Paper.from_axidraw(model)
        if paper.width_mm > bed.width_mm + 0.5 or paper.height_mm > bed.height_mm + 0.5:
            self.paper_note.setText(
                "⚠ %s is larger than the %s's travel (%.0f x %.0f mm). "
                "Anything past that will not be drawn."
                % (paper.describe(), bed.label, bed.width_mm, bed.height_mm))
            self.paper_note.setStyleSheet("color: %s;" % theme.WARN)
        else:
            self.paper_note.setText("Drawable area %.0f x %.0f mm."
                                    % (paper.drawable[2], paper.drawable[3]))
            self.paper_note.setStyleSheet("color: %s;" % theme.MUTED)
        self.paperChanged.emit()
        self.refresh()

    def paper_setup(self):
        """How the paper was chosen — what a sheet file has to remember so
        the combos come back the way they were, not just the millimetres."""
        choice = self.preset.currentData()
        return {"model": self.current_model(),
                "preset": list(choice) if choice else None,
                "margin_mm": self.margin.value()}

    def restore_paper_setup(self, setup):
        """Put the combos back the way :meth:`paper_setup` found them and
        apply the paper. Missing keys keep what is there."""
        self._syncing = True
        try:
            model = setup.get("model")
            for index in range(self.model.count()):
                if self.model.itemData(index) == model:
                    self.model.setCurrentIndex(index)
                    break
            preset = setup.get("preset")
            wanted = tuple(preset) if preset else None
            for index in range(self.preset.count()):
                if self.preset.itemData(index) == wanted:
                    self.preset.setCurrentIndex(index)
                    break
            if "margin_mm" in setup:
                self.margin.setValue(float(setup["margin_mm"]))
        finally:
            self._syncing = False
        self._apply_paper()

    def _model_changed(self, _index):
        if not self._syncing:
            self._apply_paper()

    def _preset_changed(self, _index):
        if not self._syncing:
            self._apply_paper()

    def _margin_changed(self, _value):
        if not self._syncing:
            self._apply_paper()

    # -- items --------------------------------------------------------------------- #

    def refresh(self, select=None):
        self._syncing = True
        try:
            self._refresh_items(select)
            self._refresh_pens()
        finally:
            self._syncing = False

    def _refresh_items(self, select=None):
        out_of_bounds = {i.item_id for i in self.scene.out_of_bounds()}
        self.items.setRowCount(len(self.scene.items))
        for index, item in enumerate(self.scene.items):
            visible = QCheckBox()
            visible.setChecked(item.visible)
            visible.setToolTip("Draw this one")
            visible.toggled.connect(
                lambda on, target=item: self._set_visible(target, on))
            self.items.setCellWidget(index, 0, visible)

            name = QTableWidgetItem(item.name)
            if item.item_id in out_of_bounds:
                name.setText("⚠ " + item.name)
                name.setToolTip("Reaches outside the drawable area")
            name.setData(Qt.UserRole, item.item_id)
            self.items.setItem(index, 1, name)
            size = QTableWidgetItem("%.0f×%.0f" % (item.w_mm, item.h_mm))
            size.setToolTip("%.1f x %.1f mm" % (item.w_mm, item.h_mm))
            self.items.setItem(index, 2, size)
            at = QTableWidgetItem("%.0f,%.0f" % (item.x_mm, item.y_mm))
            at.setToolTip("centre at %.1f, %.1f mm from the sheet's top-left"
                          % (item.x_mm, item.y_mm))
            self.items.setItem(index, 3, at)

            pen = QComboBox()
            for pen_index, entry in enumerate(self.scene.pens):
                pen.addItem("%d · %s" % (pen_index + 1, entry.label), pen_index)
            pen.setCurrentIndex(min(item.pen, len(self.scene.pens) - 1))
            pen.currentIndexChanged.connect(
                lambda _i, target=item, box=pen: self._set_pen(target, box))
            self.items.setCellWidget(index, 4, pen)

            if select is not None and item.item_id == select:
                self.items.selectRow(index)
        self._refresh_selected()

    def _refresh_selected(self):
        """The numeric editors follow the selection, without echoing back."""
        item = self._selected_item()
        was = self._syncing
        self._syncing = True
        try:
            self.selected_box.setEnabled(item is not None)
            if item is None:
                return
            for box, value in ((self.sel_x, item.x_mm), (self.sel_y, item.y_mm),
                               (self.sel_w, item.w_mm),
                               (self.sel_rot, item.rotation_deg)):
                box.blockSignals(True)
                box.setValue(value)
                box.blockSignals(False)
        finally:
            self._syncing = was

    def _selected_edited(self, _value):
        if self._syncing:
            return
        item = self._selected_item()
        if item is None:
            return
        item.move_to(self.sel_x.value(), self.sel_y.value())
        item.set_width(self.sel_w.value())
        item.rotate_to(self.sel_rot.value())
        self._refresh_items(item.item_id)
        self.sceneChanged.emit()

    def _set_visible(self, item, on):
        item.visible = on
        self.sceneChanged.emit()

    def _set_pen(self, item, box):
        if self._syncing:
            return
        item.pen = box.currentData()
        self.sceneChanged.emit()

    def _row_selected(self):
        if self._syncing:
            return
        self._refresh_selected()
        self.selectionChanged.emit(self.selected_id())

    def selected_id(self):
        rows = self.items.selectionModel().selectedRows()
        if not rows:
            return None
        cell = self.items.item(rows[0].row(), 1)
        return cell.data(Qt.UserRole) if cell else None

    def select(self, item_id):
        self._syncing = True
        try:
            if item_id is None:
                self.items.clearSelection()
            for index in range(self.items.rowCount()):
                if self.items.item(index, 1).data(Qt.UserRole) == item_id:
                    self.items.selectRow(index)
                    break
        finally:
            self._syncing = False
        self._refresh_selected()

    def _selected_item(self):
        item_id = self.selected_id()
        return self.scene.find(item_id) if item_id else None

    def _remove_selected(self):
        item = self._selected_item()
        if item and self.scene.remove(item.item_id):
            self.refresh()
            self.selectionChanged.emit(None)
            self.sceneChanged.emit()

    def _duplicate_selected(self):
        import copy
        item = self._selected_item()
        if not item:
            return
        clone = copy.copy(item)
        clone.item_id = max((i.item_id for i in self.scene.items), default=0) + 1
        clone.name = item.name + " copy"
        clone.move_by(10, 10)
        clone.pen = min(item.pen + 1, len(self.scene.pens) - 1)
        self.scene.items.append(clone)
        self.refresh(select=clone.item_id)
        self.selectionChanged.emit(clone.item_id)
        self.sceneChanged.emit()

    def _centre_selected(self):
        item = self._selected_item()
        if item:
            item.move_to(*self.scene.paper.center)
            self.refresh(select=item.item_id)
            self.sceneChanged.emit()

    def _fit_selected(self):
        item = self._selected_item()
        if item:
            _, _, width, height = self.scene.paper.drawable
            item.fit_into(width, height)
            item.move_to(*self.scene.paper.center)
            self.refresh(select=item.item_id)
            self.sceneChanged.emit()

    # -- pens ------------------------------------------------------------------------ #

    def clear_paper(self, confirm=True):
        """Empty the sheet.

        Asks first, because there is no undo and re-placing a pattern that was
        nudged into position is a nuisance. Nothing else is touched: the
        pattern being built, the pens and the paper all stay as they are.
        """
        if not self.scene.items:
            self.selectionChanged.emit(None)
            return False
        if confirm:
            count = len(self.scene.items)
            answer = QMessageBox.question(
                self, "Clear the paper",
                "Take %d pattern%s off the sheet?"
                % (count, "" if count == 1 else "s"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return False
        self.scene.items = []
        self.refresh()
        self.selectionChanged.emit(None)
        self.cleared.emit()
        self.sceneChanged.emit()
        return True

    def _refresh_pens(self):
        while self.pens_layout.count():
            child = self.pens_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        used = {index for index, _ in self.scene.pens_in_use()}
        for index, pen in enumerate(self.scene.pens):
            swatch = Swatch(pen.color)
            swatch.colorPicked.connect(
                lambda color, target=pen: self._set_pen_color(target, color))
            label = QLineEdit(pen.label)
            label.textChanged.connect(lambda text, target=pen:
                                      self._set_pen_label(target, text))
            include = QCheckBox()
            include.setChecked(pen.include)
            include.setToolTip("Plot this pen's layer")
            include.toggled.connect(lambda on, target=pen:
                                    self._set_pen_include(target, on))
            count = len(self.scene.items_for_pen(index))
            note = theme.muted("%d" % count if count else "—")
            note.setFixedWidth(18)
            note.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if index in used:
                note.setStyleSheet("color: %s;" % theme.OK)
            self.pens_layout.addWidget(
                row(QLabel("%d" % (index + 1)), swatch, label, note, include,
                    stretch_last=False))
        self.add_pen.setEnabled(len(self.scene.pens) < MAX_PENS)

    def _set_pen_color(self, pen, color):
        pen.color = color
        self.sceneChanged.emit()

    def _set_pen_label(self, pen, text):
        pen.label = text
        if not self._syncing:
            self._refresh_items(self.selected_id())

    def _set_pen_include(self, pen, on):
        pen.include = on
        self.sceneChanged.emit()

    def _add_pen(self):
        index = len(self.scene.pens)
        if index >= MAX_PENS:
            return
        color, label = DEFAULT_PEN_COLORS[index]
        self.scene.pens.append(Pen(color, label))
        self.refresh(select=self.selected_id())
        self.sceneChanged.emit()


def _mm_box(low, high):
    box = QDoubleSpinBox()
    box.setRange(low, high)
    box.setDecimals(1)
    box.setSuffix(" mm")
    box.setFixedWidth(88)
    return box
