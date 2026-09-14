"""Small widgets the panels share: a parameter row, a colour swatch, a section.

The parameter row is the interesting one. Every module parameter in the
registry has a type, a default and often a range, and half of them have an
``end_*`` twin that makes the value *drift* over the draw. Rather than write a
form per module, one row reads the registry and builds itself — which is why
adding a module to the registry is all it takes to make it editable.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox,
                               QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)

from spiro.ui import theme


class ParamRow(QWidget):
    """One parameter: a label, an editor, and (when it has one) its drift twin.

    ``valueChanged`` carries ``(name, value)``; the drift twin reports under
    its own ``end_*`` name, so the caller never has to know which is which.
    """

    valueChanged = Signal(str, object)

    def __init__(self, name, spec, value, drift_name=None, drift_spec=None,
                 drift_value=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.drift_name = drift_name
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(6)
        label = QLabel(spec.get("desc") or name.replace("_", " "))
        label.setToolTip("%s — %s" % (name, spec.get("desc", "")))
        label.setMinimumWidth(120)
        row.addWidget(label, 1)
        self.editor = _editor(spec, value)
        _connect(self.editor, lambda v: self.valueChanged.emit(self.name, v))
        row.addWidget(self.editor, 0)
        layout.addLayout(row)

        self.drift_editor = None
        if drift_name:
            drift_row = QHBoxLayout()
            drift_row.setSpacing(6)
            self.drift_toggle = QPushButton("drift →")
            self.drift_toggle.setObjectName("flat")
            self.drift_toggle.setCheckable(True)
            self.drift_toggle.setChecked(drift_value != value)
            self.drift_toggle.setToolTip(
                "Interpolate this parameter from its value to the end value "
                "over the course of the draw")
            drift_row.addStretch(1)
            drift_row.addWidget(self.drift_toggle)
            self.drift_editor = _editor(drift_spec, drift_value)
            _connect(self.drift_editor,
                     lambda v: self.valueChanged.emit(self.drift_name, v))
            drift_row.addWidget(self.drift_editor)
            layout.addLayout(drift_row)
            self.drift_toggle.toggled.connect(self._toggle_drift)
            self._toggle_drift(self.drift_toggle.isChecked())

    def _toggle_drift(self, on):
        self.drift_editor.setVisible(on)
        if not on:
            # Off means "no drift", which in the INI is the end value equalling
            # the start — not a missing key, which would mean the default.
            value = _value_of(self.editor)
            _set_value(self.drift_editor, value)
            self.valueChanged.emit(self.drift_name, value)

    def set_value(self, value):
        _set_value(self.editor, value)


def _editor(spec, value):
    kind = spec.get("type", "float")
    if kind == "bool":
        box = QCheckBox()
        box.setChecked(bool(value))
        return box
    if kind == "choice":
        combo = QComboBox()
        combo.addItems([str(c) for c in spec.get("choices", [])])
        combo.setCurrentText(str(value))
        return combo
    if kind == "int":
        box = QSpinBox()
        box.setRange(int(spec.get("min", -10 ** 6)), int(spec.get("max", 10 ** 6)))
        box.setValue(int(value if value is not None else spec.get("default", 0)))
        box.setFixedWidth(96)
        return box
    if kind == "float":
        box = QDoubleSpinBox()
        box.setRange(float(spec.get("min", -10 ** 6)), float(spec.get("max", 10 ** 6)))
        box.setDecimals(4)
        box.setSingleStep(float(spec.get("step", 0.1)))
        box.setValue(float(value if value is not None else spec.get("default", 0)))
        box.setFixedWidth(96)
        return box
    line = QLineEdit(str(value if value is not None else spec.get("default", "")))
    line.setFixedWidth(140)
    return line


def _connect(editor, fn):
    if isinstance(editor, QCheckBox):
        editor.toggled.connect(fn)
    elif isinstance(editor, QComboBox):
        editor.currentTextChanged.connect(fn)
    elif isinstance(editor, (QSpinBox, QDoubleSpinBox)):
        editor.valueChanged.connect(fn)
    else:
        editor.textChanged.connect(fn)


def _value_of(editor):
    if isinstance(editor, QCheckBox):
        return editor.isChecked()
    if isinstance(editor, QComboBox):
        return editor.currentText()
    if isinstance(editor, (QSpinBox, QDoubleSpinBox)):
        return editor.value()
    return editor.text()


def _set_value(editor, value):
    editor.blockSignals(True)
    try:
        if isinstance(editor, QCheckBox):
            editor.setChecked(bool(value))
        elif isinstance(editor, QComboBox):
            editor.setCurrentText(str(value))
        elif isinstance(editor, QSpinBox):
            editor.setValue(int(value))
        elif isinstance(editor, QDoubleSpinBox):
            editor.setValue(float(value))
        else:
            editor.setText(str(value))
    finally:
        editor.blockSignals(False)


class Swatch(QPushButton):
    """A colour button that opens a colour picker. Emits ``colorPicked``."""

    colorPicked = Signal(str)

    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 18)
        self.setCursor(Qt.PointingHandCursor)
        self.set_color(color)
        self.clicked.connect(self._pick)

    def set_color(self, color):
        self.color = color
        self.setStyleSheet(
            "background: %s; border: 1px solid %s; border-radius: 3px;"
            % (color, theme.LINE))

    def _pick(self):
        chosen = QColorDialog.getColor(QColor(self.color), self, "Pen colour")
        if chosen.isValid():
            self.set_color(chosen.name())
            self.colorPicked.emit(self.color)


def row(*widgets, spacing=6, margins=(0, 0, 0, 0), stretch_last=False):
    """A horizontal strip. An int in the list becomes a stretch of that size."""
    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    for index, widget in enumerate(widgets):
        if isinstance(widget, int):
            layout.addStretch(widget)
        else:
            layout.addWidget(widget, 1 if stretch_last and index == len(widgets) - 1 else 0)
    return holder
