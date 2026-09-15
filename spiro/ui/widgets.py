"""Small widgets the panels share: a parameter row, a colour swatch, a section.

The parameter row is the interesting one. Every module parameter in the
registry has a type, a default and often a range, and half of them have an
``end_*`` twin that makes the value *drift* over the draw. Rather than write a
form per module, one row reads the registry and builds itself — which is why
adding a module to the registry is all it takes to make it editable.
"""

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox,
                               QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSlider, QSpinBox, QVBoxLayout,
                               QWidget)

from spiro.ui import theme

SLIDER_STEPS = 1000
# What a number box will take, whatever its slider sweeps. The registry's
# min and max say which range is worth having under a slider — they were
# never a law about the value, and a gear asked for sixty repetitions is a
# real thing to want. So only a floor survives, and only where a count below
# one has no meaning.
TYPED_CEILING = 1e6


def typed_range(spec, kind):
    """(floor, ceiling) for a number box — see TYPED_CEILING.

    ``hard_min``/``hard_max`` in a registry entry override it, for the day a
    parameter really does have a limit.
    """
    ceiling = float(spec.get("hard_max", TYPED_CEILING))
    low = float(spec.get("min", 0.0))
    if "hard_min" in spec:
        floor = float(spec["hard_min"])
    elif low < 0:
        floor = -ceiling
    elif kind == "int" and low >= 1:
        floor = 1.0                  # teeth, sides, points, folds: counts
    else:
        floor = 0.0
    return floor, ceiling


def slider_span(spec, value):
    """The range a slider sweeps: the registry's, widened to hold a value
    that has been typed past it, so the slider never becomes a lie."""
    if "min" not in spec or "max" not in spec:
        return None
    low, high = float(spec["min"]), float(spec["max"])
    if abs(high - low) > 1e5:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return (low, high)
    return (min(low, value), max(high, value))
LABEL_WIDTH = 118          # the name column; longer names elide, the tooltip has the rest


def name_label(text, tooltip=""):
    """A fixed-width label for a parameter name, elided if it is long."""
    label = QLabel()
    label.setFixedWidth(LABEL_WIDTH)
    label.setText(label.fontMetrics().elidedText(text, Qt.ElideRight, LABEL_WIDTH))
    label.setToolTip(tooltip or text)
    return label


class ParamRow(QWidget):
    """One parameter: a label, a slider where the range allows one, an
    editor, and (when it has one) its drift twin.

    ``valueChanged`` carries ``(name, value)``; the drift twin reports under
    its own ``end_*`` name, so the caller never has to know which is which.
    A drift can also oscillate — ``osc_<name> = speed, irregularity`` in the
    file — which is reported under that key.
    """

    valueChanged = Signal(str, object)
    hovered = Signal(str)               # the parameter under the pointer

    def __init__(self, name, spec, value, drift_name=None, drift_spec=None,
                 drift_value=None, osc_value=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.drift_name = drift_name
        self.spec = spec
        self.drift_spec = drift_spec
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(6)
        label = name_label(spec.get("desc") or name.replace("_", " "),
                           "%s — %s" % (name, spec.get("desc", "")))
        row.addWidget(label, 0)
        self.editor = _editor(spec, value)
        _connect(self.editor, self._editor_changed)
        self.span = slider_span(spec, value)
        self.slider = _slider_for(spec) if self.span else None
        if self.slider is not None:
            self.slider.setValue(_to_slider(self.span, _value_of(self.editor)))
            self.slider.valueChanged.connect(self._slider_moved)
            row.addWidget(self.slider, 2)
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
            self.drift_editor.installEventFilter(self)
            drift_row.addWidget(self.drift_editor)
            # Once there is a drift, it can slide once or go there and back.
            self.osc_mode = QComboBox()
            self.osc_mode.addItem("once", None)
            self.osc_mode.addItem("there and back", "osc")
            self.osc_mode.setToolTip(
                "Once: slide from the value to the end value over the draw.\n"
                "There and back: oscillate between them — speed is how many "
                "times, wander mixes in two incommensurate rhythms so it does "
                "not tick.")
            self.osc_speed = QDoubleSpinBox()
            self.osc_speed.setRange(0.0, TYPED_CEILING)
            self.osc_speed.setDecimals(1)
            self.osc_speed.setSuffix("×")
            self.osc_speed.setFixedWidth(64)
            self.osc_wander = QDoubleSpinBox()
            self.osc_wander.setRange(0, 1)
            self.osc_wander.setSingleStep(0.1)
            self.osc_wander.setDecimals(1)
            self.osc_wander.setFixedWidth(52)
            self.osc_wander.setToolTip("wander, 0 to 1")
            speed, wander = _parse_osc(osc_value)
            self.osc_speed.setValue(speed)
            self.osc_wander.setValue(wander)
            self.osc_mode.setCurrentIndex(1 if osc_value else 0)
            osc_row = QHBoxLayout()
            osc_row.setSpacing(6)
            osc_row.addStretch(1)
            osc_row.addWidget(self.osc_mode)
            osc_row.addWidget(self.osc_speed)
            osc_row.addWidget(self.osc_wander)
            self.osc_host = QWidget()
            self.osc_host.setLayout(osc_row)
            layout.addLayout(drift_row)
            layout.addWidget(self.osc_host)
            for widget in (self.osc_speed, self.osc_wander):
                widget.valueChanged.connect(self._osc_changed)
            self.osc_mode.currentIndexChanged.connect(self._osc_changed)
            self.drift_toggle.toggled.connect(self._toggle_drift)
            self._toggle_drift(self.drift_toggle.isChecked())
            self._osc_changed(emit=False)

    def enterEvent(self, event):
        self.hovered.emit(self.name)
        super().enterEvent(event)

    def eventFilter(self, obj, event):
        if obj is self.drift_editor and event.type() == QEvent.Enter:
            self.hovered.emit(self.drift_name)
        return super().eventFilter(obj, event)

    def _editor_changed(self, value):
        self._sync_slider(value)
        self.valueChanged.emit(self.name, value)

    def _sync_slider(self, value):
        """Put the slider where the number is, growing its span if the number
        has been typed past the end of it."""
        if self.slider is None:
            return
        self.span = slider_span(self.spec, value) or self.span
        self.slider.blockSignals(True)
        self.slider.setValue(_to_slider(self.span, value))
        self.slider.blockSignals(False)

    def _slider_moved(self, position):
        value = _from_slider(self.spec, self.span, position)
        _set_value(self.editor, value)
        self.valueChanged.emit(self.name, _value_of(self.editor))

    def _toggle_drift(self, on):
        self.drift_editor.setVisible(on)
        self.osc_host.setVisible(on)
        if not on:
            # Off means "no drift", which in the INI is the end value equalling
            # the start — not a missing key, which would mean the default.
            value = _value_of(self.editor)
            _set_value(self.drift_editor, value)
            self.valueChanged.emit(self.drift_name, value)
            if self.osc_mode.currentData():
                self.osc_mode.setCurrentIndex(0)

    def _osc_changed(self, *_args, emit=True):
        on = self.osc_mode.currentData() is not None
        self.osc_speed.setVisible(on)
        self.osc_wander.setVisible(on)
        if emit:
            value = ("%g,%g" % (self.osc_speed.value(), self.osc_wander.value())
                     if on else None)
            self.valueChanged.emit("osc_" + self.name, value)

    def set_value(self, value):
        _set_value(self.editor, value)
        self._sync_slider(value)


def _parse_osc(text):
    """'speed,wander' -> (speed, wander), with the module's own defaults."""
    if not text:
        return 3.0, 0.3
    parts = [p.strip() for p in str(text).split(",")]
    try:
        speed = float(parts[0]) if parts and parts[0] else 3.0
        wander = float(parts[1]) if len(parts) > 1 and parts[1] else 0.3
    except ValueError:
        return 3.0, 0.3
    return speed, wander


def _slider_for(spec):
    """A slider for a bounded number; None for anything else."""
    if spec.get("type") not in ("int", "float"):
        return None
    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, SLIDER_STEPS)
    slider.setMinimumWidth(40)
    slider.setFocusPolicy(Qt.NoFocus)
    return slider


def _to_slider(span, value):
    low, high = span
    if high <= low:
        return 0
    frac = (float(value) - low) / (high - low)
    return int(round(max(0.0, min(1.0, frac)) * SLIDER_STEPS))


def _from_slider(spec, span, position):
    low, high = span
    value = low + (high - low) * position / SLIDER_STEPS
    if spec.get("type") == "int":
        return int(round(value))
    step = float(spec.get("step", 0)) or 0
    if step:
        value = round(value / step) * step
    return round(value, 4)


class ScopeRow(QWidget):
    """What a table move acts on: everything so far, or the last few arms.

    ``valueChanged`` carries ``("scope", "all" | int)``.
    """

    valueChanged = Signal(str, object)

    def __init__(self, value="all", arms_available=0, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)
        label = name_label(
            "Acts on",
            "Everything: the paper moves under all the arms drawn so far.\n"
            "The last arm(s): only those arms ride the moving table — like "
            "spinning one arm's pivot instead of the whole paper.")
        layout.addWidget(label, 0)
        layout.addStretch(1)
        self.mode = QComboBox()
        self.mode.addItem("everything so far", "all")
        self.mode.addItem("the last arm", 1)
        self.mode.addItem("the last N arms", "n")
        self.count = QSpinBox()
        self.count.setRange(2, max(2, arms_available))
        self.count.setFixedWidth(56)
        self.count.setSuffix(" arms")
        layout.addWidget(self.mode)
        layout.addWidget(self.count)
        self.set_value(value)
        self.mode.currentIndexChanged.connect(self._changed)
        self.count.valueChanged.connect(self._changed)

    def set_value(self, value):
        self.mode.blockSignals(True)
        self.count.blockSignals(True)
        try:
            if value in ("all", None, ""):
                self.mode.setCurrentIndex(0)
            elif int(value) == 1:
                self.mode.setCurrentIndex(1)
            else:
                self.mode.setCurrentIndex(2)
                self.count.setValue(max(2, int(value)))
        finally:
            self.mode.blockSignals(False)
            self.count.blockSignals(False)
        self.count.setVisible(self.mode.currentData() == "n")

    def value(self):
        data = self.mode.currentData()
        if data == "n":
            return self.count.value()
        return data

    def _changed(self, *_args):
        self.count.setVisible(self.mode.currentData() == "n")
        self.valueChanged.emit("scope", self.value())


def _editor(spec, value):
    kind = spec.get("type", "float")
    if kind == "bool":
        box = QCheckBox()
        box.setChecked(bool(value))
        return box
    if kind == "choice":
        combo = QComboBox()
        for choice in spec.get("choices", []):
            combo.addItem(str(choice), choice)
        combo.setCurrentText(str(value))
        return combo
    if kind in ("int", "float"):
        return number_box(spec, value, kind)
    line = QLineEdit(str(value if value is not None else spec.get("default", "")))
    line.setFixedWidth(140)
    return line


def _connect(editor, fn):
    if isinstance(editor, QCheckBox):
        editor.toggled.connect(fn)
    elif isinstance(editor, QComboBox):
        # Report the choice as it was declared (an int stays an int), not
        # its label.
        editor.currentIndexChanged.connect(
            lambda index: fn(editor.itemData(index)
                             if editor.itemData(index) is not None
                             else editor.currentText()))
    elif isinstance(editor, (QSpinBox, QDoubleSpinBox)):
        editor.valueChanged.connect(fn)
    else:
        editor.textChanged.connect(fn)


def _value_of(editor):
    if isinstance(editor, QCheckBox):
        return editor.isChecked()
    if isinstance(editor, QComboBox):
        data = editor.currentData()
        return data if data is not None else editor.currentText()
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


def number_box(spec, value, kind=None, width=90):
    """A spin box that takes what a person types.

    The registry's range steers the slider beside it; this takes anything
    from the floor up to the ceiling, and a value already outside even that
    is shown rather than clamped — a file is allowed to be stranger than the
    table.
    """
    kind = kind or spec.get("type", "float")
    floor, ceiling = typed_range(spec, kind)
    if kind == "int":
        box = QSpinBox()
        current = int(value if value is not None else spec.get("default", 0))
        box.setRange(int(min(floor, current)), int(max(ceiling, current)))
    else:
        box = QDoubleSpinBox()
        current = float(value if value is not None else spec.get("default", 0))
        box.setRange(min(floor, current), max(ceiling, current))
        box.setDecimals(4 if float(spec.get("max", 1)) > 1 else 4)
        box.setSingleStep(float(spec.get("step", 0.1)))
    box.setValue(current)
    box.setFixedWidth(width)
    box.setKeyboardTracking(False)      # a number is read when it is finished
    return box


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
