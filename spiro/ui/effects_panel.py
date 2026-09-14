"""Symmetry, pen lift, moiré — the things done to a whole pattern.

These are not modules in the pipeline; they are sections of the INI that the
engine applies after it. Symmetry mirrors and rotates the finished curve, pen
lift chops it into separately drawn fragments, and moiré runs the whole
pipeline several times with one parameter nudged so the copies interfere.

Each is a checkbox and a few numbers, and each writes straight into the
document's own dict, because the INI is the document.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFrame,
                               QGroupBox, QLabel, QScrollArea, QSpinBox,
                               QVBoxLayout, QWidget)

from spiro.ui import theme
from spiro.ui.widgets import row

PEN_LIFT_MODES = [
    ("periodic", "Periodic — draw a while, skip a while"),
    ("threshold", "Threshold — lift where the pen moves too far in one step"),
    ("angular", "Angular — draw in wedges around a centre"),
]


class EffectsPanel(QWidget):
    """Whole-pattern effects, written into the document as INI sections."""

    documentChanged = Signal()

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self._loading = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        area.setWidget(host)
        outer.addWidget(area)

        # -- symmetry ---------------------------------------------------------- #
        box = QGroupBox("Symmetry")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        inner.setSpacing(4)
        inner.addWidget(theme.muted(
            "Repeat the finished curve around a centre, and optionally mirror "
            "it. The copies share one bounding box, so the pattern keeps its "
            "shape.", wrap=True))
        self.n_fold = QSpinBox()
        self.n_fold.setRange(1, 64)
        self.n_fold.setToolTip("1 leaves the curve alone")
        inner.addWidget(row(QLabel("Fold"), 1, self.n_fold))
        self.mirror = QCheckBox("Mirror as well as rotate")
        inner.addWidget(self.mirror)
        self.sym_x = self._spin(inner, "Centre x", -5000, 5000)
        self.sym_y = self._spin(inner, "Centre y", -5000, 5000)
        layout.addWidget(box)

        # -- pen lift ------------------------------------------------------------ #
        box = QGroupBox("Pen lift")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        inner.setSpacing(4)
        self.lift_on = QCheckBox("Break the line into separate strokes")
        inner.addWidget(self.lift_on)
        self.lift_mode = QComboBox()
        for value, label in PEN_LIFT_MODES:
            self.lift_mode.addItem(label, value)
        inner.addWidget(self.lift_mode)
        self.draw_length = self._spin(inner, "Draw for", 1, 100000, integer=True,
                                      suffix=" points")
        self.skip_length = self._spin(inner, "Then skip", 1, 100000, integer=True,
                                      suffix=" points")
        self.threshold = self._spin(inner, "Lift beyond", 0.01, 10000)
        self.angle_draw = self._spin(inner, "Draw wedge", 0.1, 360, suffix="°")
        self.angle_skip = self._spin(inner, "Skip wedge", 0.0, 360, suffix="°")
        self.lift_x = self._spin(inner, "Centre x", -5000, 5000)
        self.lift_y = self._spin(inner, "Centre y", -5000, 5000)
        layout.addWidget(box)

        # -- moiré ----------------------------------------------------------------- #
        box = QGroupBox("Moiré")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        inner.setSpacing(4)
        self.moire_on = QCheckBox("Overlay near-copies of the whole pattern")
        inner.addWidget(self.moire_on)
        inner.addWidget(theme.muted(
            "Each copy runs the pipeline again with one parameter nudged; "
            "where the copies nearly agree they interfere.", wrap=True))
        self.copies = QSpinBox()
        self.copies.setRange(2, 40)
        inner.addWidget(row(QLabel("Copies"), 1, self.copies))
        self.vary_param = QComboBox()
        self.vary_param.setToolTip(
            "Only a step that is one module can be varied — a group's sections "
            "are named by branch and position.")
        inner.addWidget(self.vary_param)
        self.vary_range = self._spin(inner, "Spread ±", 0.0001, 10000)
        self.vary_range.setDecimals(4)
        layout.addWidget(box)

        # -- output ------------------------------------------------------------------- #
        box = QGroupBox("Framing")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        self.margin = self._spin(inner, "Margin", 0.0, 0.45)
        self.margin.setSingleStep(0.01)
        self.margin.setToolTip(
            "Blank space kept inside the pattern's own box, as a fraction. "
            "It travels with the pattern; the paper's margin is separate.")
        layout.addWidget(box)

        layout.addStretch(1)

        for widget in (self.n_fold, self.sym_x, self.sym_y, self.draw_length,
                       self.skip_length, self.threshold, self.angle_draw,
                       self.angle_skip, self.lift_x, self.lift_y, self.copies,
                       self.vary_range, self.margin):
            widget.valueChanged.connect(self._apply)
        for widget in (self.mirror, self.lift_on, self.moire_on):
            widget.toggled.connect(self._apply)
        for widget in (self.lift_mode, self.vary_param):
            widget.currentIndexChanged.connect(self._apply)

        self.reload()

    def _spin(self, layout, label, low, high, integer=False, suffix=""):
        widget = QSpinBox() if integer else QDoubleSpinBox()
        widget.setRange(int(low) if integer else low, int(high) if integer else high)
        if not integer:
            widget.setDecimals(2)
        if suffix:
            widget.setSuffix(suffix)
        widget.setFixedWidth(120)
        layout.addWidget(row(QLabel(label), 1, widget))
        return widget

    # -- document -> widgets ------------------------------------------------------- #

    def reload(self):
        """Pull the document's state into the widgets — after a file is opened,
        or after the pipeline changes and the moiré targets are different."""
        self._loading = True
        try:
            symmetry = self.document.symmetry or {}
            self.n_fold.setValue(int(symmetry.get("n_fold", 1) or 1))
            self.mirror.setChecked(bool(symmetry.get("mirror", False)))
            self.sym_x.setValue(float(symmetry.get("center_x", 0) or 0))
            self.sym_y.setValue(float(symmetry.get("center_y", 0) or 0))

            lift = self.document.extras.get("pen_lift") or {}
            self.lift_on.setChecked(bool(lift))
            index = self.lift_mode.findData(lift.get("mode", "periodic"))
            self.lift_mode.setCurrentIndex(max(index, 0))
            self.draw_length.setValue(int(lift.get("draw_length", 100)))
            self.skip_length.setValue(int(lift.get("skip_length", 50)))
            self.threshold.setValue(float(lift.get("threshold", 20.0)))
            self.angle_draw.setValue(float(lift.get("angle_draw", 30.0)))
            self.angle_skip.setValue(float(lift.get("angle_skip", 10.0)))
            self.lift_x.setValue(float(lift.get("center_x", 0.0)))
            self.lift_y.setValue(float(lift.get("center_y", 0.0)))

            moire = self.document.extras.get("moire") or {}
            self.moire_on.setChecked(bool(moire))
            self.copies.setValue(int(moire.get("copies", 5)))
            self.vary_range.setValue(float(moire.get("vary_range", 0.05)))
            self._fill_vary(moire.get("vary_param"))

            self.margin.setValue(float(self.document.output.get("margin", 0.08)))
        finally:
            self._loading = False
        self._update_enabled()

    def _fill_vary(self, current):
        self.vary_param.clear()
        for section, label, key in self.document.single_step_params():
            self.vary_param.addItem(label, "%s.%s" % (section, key))
        if self.vary_param.count() == 0:
            self.vary_param.addItem("nothing a moiré pass can vary", None)
        if current:
            index = self.vary_param.findData(current)
            if index >= 0:
                self.vary_param.setCurrentIndex(index)

    def _update_enabled(self):
        mode = self.lift_mode.currentData()
        for widget, modes in ((self.draw_length, ("periodic",)),
                              (self.skip_length, ("periodic",)),
                              (self.threshold, ("threshold",)),
                              (self.angle_draw, ("angular",)),
                              (self.angle_skip, ("angular",)),
                              (self.lift_x, ("angular",)),
                              (self.lift_y, ("angular",))):
            widget.parentWidget().setVisible(self.lift_on.isChecked()
                                             and mode in modes)
        self.lift_mode.setVisible(self.lift_on.isChecked())
        for widget in (self.copies, self.vary_param, self.vary_range):
            widget.setEnabled(self.moire_on.isChecked())
        self.sym_x.parentWidget().setVisible(self.n_fold.value() > 1
                                             or self.mirror.isChecked())
        self.sym_y.parentWidget().setVisible(self.sym_x.parentWidget().isVisible())

    # -- widgets -> document ------------------------------------------------------------ #

    def _apply(self, *_args):
        if self._loading:
            return
        self._update_enabled()

        if self.n_fold.value() > 1 or self.mirror.isChecked():
            self.document.symmetry = {
                "n_fold": self.n_fold.value(), "mirror": self.mirror.isChecked(),
                "center_x": self.sym_x.value(), "center_y": self.sym_y.value()}
        else:
            self.document.symmetry = {}

        if self.lift_on.isChecked():
            mode = self.lift_mode.currentData()
            lift = {"mode": mode}
            if mode == "periodic":
                lift.update(draw_length=self.draw_length.value(),
                            skip_length=self.skip_length.value())
            elif mode == "threshold":
                lift.update(threshold=self.threshold.value())
            else:
                lift.update(angle_draw=self.angle_draw.value(),
                            angle_skip=self.angle_skip.value(),
                            center_x=self.lift_x.value(),
                            center_y=self.lift_y.value())
            self.document.extras["pen_lift"] = lift
        else:
            self.document.drop_effect("pen_lift")

        target = self.vary_param.currentData()
        if self.moire_on.isChecked() and target:
            self.document.extras["moire"] = {
                "copies": self.copies.value(), "vary_param": target,
                "vary_range": self.vary_range.value()}
        else:
            self.document.drop_effect("moire")

        self.document.output["margin"] = round(self.margin.value(), 4)
        self.documentChanged.emit()
