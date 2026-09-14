"""The machine side: settings, the manual controls, and the plot itself.

Nothing here talks to the AxiDraw directly. The panel gathers options and emits
what the operator asked for; the window owns the worker thread, because the
serial port must have exactly one owner in the process and a panel is the wrong
place for that.
"""

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFrame,
                               QGridLayout, QGroupBox, QLabel, QLineEdit,
                               QProgressBar, QPushButton, QScrollArea,
                               QSpinBox, QVBoxLayout, QWidget)

from axiplot import driver as axidriver
from spiro.ui import theme
from spiro.ui.widgets import row

# name -> (label, minimum, maximum, default, suffix). These are the AxiDraw's
# own option names as axiplot spells them, so what the panel collects can be
# handed to the driver unchanged.
SETTINGS = [
    ("speedPenDown", "Pen-down speed", 1, 110, 25, " %"),
    ("speedPenUp", "Pen-up speed", 1, 110, 75, " %"),
    ("accel", "Acceleration", 1, 100, 75, " %"),
    ("penPosDown", "Pen down position", 0, 100, 30, " %"),
    ("penPosUp", "Pen up position", 0, 100, 60, " %"),
    ("penRateLower", "Lowering rate", 1, 100, 50, " %"),
    ("penRateRaise", "Raising rate", 1, 100, 75, " %"),
]


class PlotPanel(QWidget):
    """AxiDraw options, manual jogging, and the plot controls."""

    plotRequested = Signal(bool)          # dry_run
    previewRequested = Signal()
    stopRequested = Signal()
    manualRequested = Signal(str)
    penChangeAcknowledged = Signal(bool)  # go on / abort
    resetLayersRequested = Signal()

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings or QSettings("spirograph-2", "plotter")

        scroll = QVBoxLayout(self)
        scroll.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        area.setWidget(host)
        scroll.addWidget(area)

        # -- connection --------------------------------------------------------- #
        layout.addWidget(theme.h2("Machine"))
        self.port = QLineEdit(self.settings.value("port", "/dev/ttyACM0"))
        self.port.setToolTip("Serial port. Leave blank to let the AxiDraw find itself.")
        layout.addWidget(row(QLabel("Port"), 1, self.port))

        self.penlift = QComboBox()
        for value, label in ((1, "1 · standard servo"), (2, "2 · narrow-band servo"),
                             (3, "3 · brushless (AxiDraw SE/A1, A2)")):
            self.penlift.addItem(label, value)
        self.penlift.setCurrentIndex(int(self.settings.value("penlift_index", 2)))
        layout.addWidget(row(QLabel("Pen lift"), 1, self.penlift))

        state = theme.muted("in-process driver: %s"
                            % ("v%s" % axidriver.version() if axidriver.available()
                               else "not found — install the AxiDraw API"))
        state.setStyleSheet("color: %s;" % (theme.OK if axidriver.available()
                                            else theme.ERR))
        layout.addWidget(state)

        # -- speeds ------------------------------------------------------------- #
        box = QGroupBox("Speeds and the pen")
        grid = QGridLayout(box)
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setVerticalSpacing(3)
        self.fields = {}
        for index, (name, label, low, high, default, suffix) in enumerate(SETTINGS):
            spin = QSpinBox()
            spin.setRange(low, high)
            spin.setSuffix(suffix)
            spin.setValue(int(self.settings.value(name, default)))
            spin.setFixedWidth(84)
            self.fields[name] = spin
            grid.addWidget(QLabel(label), index, 0)
            grid.addWidget(spin, index, 1, Qt.AlignRight)
        self.const_speed = QCheckBox("Constant pen-down speed")
        self.const_speed.setChecked(self.settings.value("constSpeed", "false") == "true")
        grid.addWidget(self.const_speed, len(SETTINGS), 0, 1, 2)
        layout.addWidget(box)

        # -- optimisation ---------------------------------------------------------- #
        box = QGroupBox("Path handling")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 4)
        self.reorder = QComboBox()
        for value, label in ((0, "Leave the order alone"),
                             (1, "Reorder within each layer"),
                             (2, "Reorder, and reverse where it helps"),
                             (4, "Reorder everything")):
            self.reorder.addItem(label, value)
        self.reorder.setCurrentIndex(2)
        inner.addWidget(self.reorder)
        self.auto_rotate = QCheckBox("Let the AxiDraw rotate a tall page")
        self.auto_rotate.setToolTip(
            "The machine turns a page 90° when it is taller than it is wide. "
            "Off keeps what is on screen exactly where it is on the paper.")
        self.auto_rotate.setChecked(False)
        inner.addWidget(self.auto_rotate)
        layout.addWidget(box)

        # -- manual ------------------------------------------------------------------ #
        box = QGroupBox("By hand")
        grid = QGridLayout(box)
        grid.setContentsMargins(8, 4, 8, 4)
        commands = [("Pen up", "pen_up"), ("Pen down", "pen_down"),
                    ("Home", "home"), ("Motors off", "disable_motors")]
        for index, (label, command) in enumerate(commands):
            button = QPushButton(label)
            button.clicked.connect(lambda _c=False, cmd=command:
                                   self.manualRequested.emit(cmd))
            grid.addWidget(button, index // 2, index % 2)
        layout.addWidget(box)

        # -- plotting ------------------------------------------------------------------ #
        layout.addWidget(theme.hline())
        layout.addWidget(theme.h2("Plot"))

        self.estimate = theme.muted("Estimate not run.", wrap=True)
        layout.addWidget(self.estimate)

        self.preview_button = QPushButton("Estimate (no machine)")
        self.preview_button.setToolTip(
            "Motion-plan every layer without opening the serial port.")
        self.preview_button.clicked.connect(self.previewRequested.emit)
        self.dry_button = QPushButton("Dry run")
        self.dry_button.setToolTip("Rehearse the whole job, pen never moving.")
        self.dry_button.clicked.connect(lambda: self.plotRequested.emit(True))
        layout.addWidget(row(self.preview_button, self.dry_button))

        self.plot_button = QPushButton("Plot")
        self.plot_button.setObjectName("primary")
        self.plot_button.clicked.connect(lambda: self.plotRequested.emit(False))
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stopRequested.emit)
        layout.addWidget(row(self.plot_button, self.stop_button))

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setFormat("")
        layout.addWidget(self.progress)

        self.layers_label = theme.muted("", wrap=True)
        layout.addWidget(self.layers_label)

        self.pen_prompt = QFrame()
        self.pen_prompt.setObjectName("panel")
        prompt_layout = QVBoxLayout(self.pen_prompt)
        prompt_layout.setContentsMargins(8, 8, 8, 8)
        self.pen_prompt_text = QLabel("")
        self.pen_prompt_text.setWordWrap(True)
        prompt_layout.addWidget(self.pen_prompt_text)
        go_on = QPushButton("Pen changed — carry on")
        go_on.setObjectName("primary")
        go_on.clicked.connect(lambda: self.penChangeAcknowledged.emit(True))
        abort = QPushButton("Stop here")
        abort.setObjectName("danger")
        abort.clicked.connect(lambda: self.penChangeAcknowledged.emit(False))
        prompt_layout.addWidget(row(go_on, abort))
        self.pen_prompt.setVisible(False)
        layout.addWidget(self.pen_prompt)

        self.reset_button = QPushButton("Forget what is already plotted")
        self.reset_button.setToolTip(
            "The app remembers which layers of this sheet are down, so a "
            "stopped plot resumes rather than drawing them twice.")
        self.reset_button.clicked.connect(self.resetLayersRequested.emit)
        layout.addWidget(self.reset_button)

        layout.addStretch(1)

    # -- what the worker needs -------------------------------------------------------- #

    def options(self, model):
        """The option dict axiplot's driver takes."""
        opts = {name: self.fields[name].value() for name, *_ in SETTINGS}
        opts.update({
            "model": int(model),
            "port": self.port.text().strip(),
            "penlift": self.penlift.currentData(),
            "constSpeed": self.const_speed.isChecked(),
            "autoRotate": self.auto_rotate.isChecked(),
            "reordering": self.reorder.currentData(),
        })
        return opts

    def save_settings(self):
        for name, *_ in SETTINGS:
            self.settings.setValue(name, self.fields[name].value())
        self.settings.setValue("port", self.port.text().strip())
        self.settings.setValue("penlift_index", self.penlift.currentIndex())
        self.settings.setValue("constSpeed",
                               "true" if self.const_speed.isChecked() else "false")

    # -- feedback ------------------------------------------------------------------------ #

    def set_running(self, running):
        self.plot_button.setEnabled(not running)
        self.dry_button.setEnabled(not running)
        self.preview_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        if not running:
            self.pen_prompt.setVisible(False)

    def set_progress(self, fraction, text=""):
        self.progress.setValue(int(max(0.0, min(1.0, fraction)) * 1000))
        self.progress.setFormat(text)

    def ask_for_pen(self, text):
        self.pen_prompt_text.setText(text)
        self.pen_prompt.setVisible(True)

    def pen_prompt_done(self):
        self.pen_prompt.setVisible(False)
