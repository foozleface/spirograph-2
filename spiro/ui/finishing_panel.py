"""Finishing: what happens after the ink is dry.

Symmetry, pen lift, moiré, tile and clip act on the finished curve, not
inside the machine, which is why they are not steps. They used to have a
tab of their own; that made them look unrelated to the pipeline they
finish. Now they sit under the steps, built from FINISHING_DEFS in the
registry — one switch and a few numbers each — so adding a finishing pass
to the engine is a table entry, not a form.

Symmetry lives in the document's own ``symmetry`` slot; the rest are in
``extras`` under their section name. Both are written straight back into
the document, because the INI is the document.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QGroupBox,
                               QLabel, QSpinBox, QVBoxLayout, QWidget)

from spiro.pipeline.registry import FINISHING_DEFS
from spiro.ui import theme
from spiro.ui.widgets import number_box, row

ORDER = ["symmetry", "pen_lift", "moire", "tile", "clip"]


class FinishingPanel(QWidget):
    """Every finishing pass, as a switch and its numbers."""

    documentChanged = Signal()

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self._loading = False
        self.boxes = {}          # section -> QGroupBox (checkable)
        self.editors = {}        # section -> {key: widget}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        for section in ORDER:
            spec = FINISHING_DEFS[section]
            box = QGroupBox("Use %s" % spec["label"].lower())
            box.setCheckable(True)
            box.setChecked(False)
            box.setObjectName("finishing")
            box.setToolTip("%s — tick to switch it on; editing a number inside "
                           "switches it on too" % spec["desc"])
            inner = QVBoxLayout(box)
            inner.setContentsMargins(8, 4, 8, 6)
            inner.setSpacing(3)
            inner.addWidget(theme.muted(spec["desc"], wrap=True))
            editors = {}
            for key, p in spec["params"].items():
                if p.get("hidden"):
                    continue
                widget = self._editor(section, key, p)
                editors[key] = widget
                inner.addWidget(row(QLabel(p.get("desc") or key), 1, widget))
            self.boxes[section] = box
            self.editors[section] = editors
            box.toggled.connect(self._apply)
            layout.addWidget(box)

        box = QGroupBox("Framing")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        self.margin = QDoubleSpinBox()
        self.margin.setRange(0.0, 0.45)
        self.margin.setSingleStep(0.01)
        self.margin.setDecimals(2)
        self.margin.setFixedWidth(100)
        self.margin.setToolTip(
            "Blank space kept inside the pattern's own box, as a fraction. "
            "It travels with the pattern; the paper's margin is separate.")
        self.margin.valueChanged.connect(self._apply)
        inner.addWidget(row(QLabel("Margin"), 1, self.margin))
        layout.addWidget(box)

        self.reload()

    def _editor(self, section, key, p):
        kind = p.get("type")
        if kind == "bool":
            widget = QCheckBox()
            widget.toggled.connect(self._apply)
        elif kind == "choice":
            widget = QComboBox()
            for choice in p["choices"]:
                widget.addItem(str(choice), choice)
            widget.currentIndexChanged.connect(self._apply)
        elif kind == "param":
            # Moiré's target: one of the pipeline's own parameters.
            widget = QComboBox()
            widget.setToolTip("Which number the copies are nudged on")
            widget.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            widget.setMinimumContentsLength(8)
            widget.currentIndexChanged.connect(self._apply)
        else:
            widget = number_box(p, p.get("default"), kind, width=100)
            if kind != "int":
                widget.setDecimals(4 if float(p.get("max", 1)) <= 1 else 2)
            widget.valueChanged.connect(self._apply)
        return widget

    # -- document -> widgets ------------------------------------------------------- #

    def _values_of(self, section):
        if section == "symmetry":
            return self.document.symmetry or {}
        return self.document.extras.get(section) or {}

    def reload(self):
        """Pull the document's state into the widgets."""
        self._loading = True
        try:
            for section in ORDER:
                values = self._values_of(section)
                spec = FINISHING_DEFS[section]
                on = bool(values) and (section != "symmetry"
                                       or int(values.get("n_fold", 1) or 1) > 1
                                       or bool(values.get("mirror")))
                self.boxes[section].setChecked(on)
                for key, widget in self.editors[section].items():
                    p = spec["params"][key]
                    if p.get("type") == "param":
                        self._fill_vary(widget, values.get(key))
                        continue
                    value = values.get(key, p["default"])
                    _set(widget, value)
            self.margin.setValue(float(self.document.output.get("margin", 0.08)))
        finally:
            self._loading = False
        self._show_relevant()

    def _fill_vary(self, widget, current):
        widget.clear()
        for section, label, key in self.document.single_step_params():
            widget.addItem(label, "%s.%s" % (section, key))
        if widget.count() == 0:
            widget.addItem("nothing a moiré pass can vary", None)
        if current:
            index = widget.findData(current)
            if index >= 0:
                widget.setCurrentIndex(index)

    def _show_relevant(self):
        """Hide the numbers a chosen mode does not use."""
        for section in ORDER:
            spec = FINISHING_DEFS[section]
            editors = self.editors[section]
            mode = None
            for key, p in spec["params"].items():
                if p.get("type") == "choice" and key in editors:
                    mode = editors[key].currentData()
                    break
            for key, widget in editors.items():
                when = spec["params"][key].get("when")
                widget.parentWidget().setVisible(when is None or when == mode)

    # -- widgets -> document ------------------------------------------------------------ #

    def _apply(self, *_args):
        if self._loading:
            return
        # Editing a number inside a pass means you want the pass: switch
        # its box on rather than throw the edit away.
        sender = self.sender()
        for section, editors in self.editors.items():
            if sender in editors.values() and not self.boxes[section].isChecked():
                self.boxes[section].blockSignals(True)
                self.boxes[section].setChecked(True)
                self.boxes[section].blockSignals(False)
        self._show_relevant()
        for section in ORDER:
            spec = FINISHING_DEFS[section]
            box = self.boxes[section]
            values = {}
            if box.isChecked():
                mode = None
                for key, p in spec["params"].items():
                    if p.get("type") == "choice" and key in self.editors[section]:
                        mode = self.editors[section][key].currentData()
                        break
                for key, widget in self.editors[section].items():
                    when = spec["params"][key].get("when")
                    if when is not None and when != mode:
                        continue
                    value = _get(widget)
                    if value is None:
                        continue
                    values[key] = value
            if section == "symmetry":
                self.document.symmetry = values if box.isChecked() else {}
            elif values:
                self.document.extras[section] = values
            else:
                self.document.drop_effect(section)
        self.document.output["margin"] = round(self.margin.value(), 4)
        self.documentChanged.emit()


def _set(widget, value):
    widget.blockSignals(True)
    try:
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QComboBox):
            index = widget.findData(value)
            if index < 0:
                index = widget.findText(str(value))
            widget.setCurrentIndex(max(index, 0))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(float(value)))
        else:
            widget.setValue(float(value))
    finally:
        widget.blockSignals(False)


def _get(widget):
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QComboBox):
        return widget.currentData()
    return widget.value()
