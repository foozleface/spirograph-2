"""The left side: what to draw.

A palette of modules, the pipeline they are chained into, and the parameters of
whichever step is selected. Everything here edits one
:class:`spiro.pipeline.document.Document`; nothing here knows about paper,
pens or the plotter.

Groups are the one idea that needs a picture. A step is normally one module,
and steps run in series — generate, then rotate, then bend. A *group* step runs
its branches simultaneously from the origin and sums them, which is what a
machine with two independent arms does. `Make group` turns a step into a group
of one arm; `Add arm` puts another beside it.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QPushButton,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from spiro.pipeline.registry import MODULE_DEFS
from spiro.ui import theme
from spiro.ui.widgets import ParamRow, row

QUALITY = {                    # label -> (initial samples, output samples)
    "Draft": (20000, 3000),
    "Fine": (120000, 16000),
    "Ultra": (400000, 50000),
}


class DesignPanel(QWidget):
    """Palette, pipeline, parameters."""

    documentChanged = Signal()          # the pattern needs regenerating
    addRequested = Signal()             # put the current pattern on the paper

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self.selected_step = None
        self._building = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        outer.addWidget(theme.h2("Add a module"))
        self.picker = QComboBox()
        self._fill_picker()
        add = QPushButton("Add")
        add.clicked.connect(self._add_module)
        outer.addWidget(row(self.picker, add, stretch_last=False))
        self.picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        outer.addWidget(theme.h2("Pipeline"))
        self.steps = QListWidget()
        self.steps.setMaximumHeight(180)
        self.steps.currentRowChanged.connect(self._select_step)
        outer.addWidget(self.steps)

        self.up = QPushButton("↑")
        self.down = QPushButton("↓")
        self.group = QPushButton("⑂ Group")
        self.arm = QPushButton("+ Arm")
        self.delete = QPushButton("Remove")
        self.delete.setObjectName("danger")
        self.up.setToolTip("Move this step earlier in the pipeline")
        self.down.setToolTip("Move this step later")
        self.group.setToolTip("Turn this step into a group, so arms can run beside it")
        self.arm.setToolTip("Add a parallel arm to this group")
        for button in (self.up, self.down):
            button.setFixedWidth(30)
        for button, fn in ((self.up, lambda: self._move(-1)),
                           (self.down, lambda: self._move(1)),
                           (self.group, self._make_group),
                           (self.arm, self._add_arm),
                           (self.delete, self._remove)):
            button.clicked.connect(fn)
        outer.addWidget(row(self.up, self.down, self.group, self.arm, 1, self.delete,
                            spacing=4))

        outer.addWidget(theme.hline())
        self.param_title = theme.h2("Parameters")
        outer.addWidget(self.param_title)

        self.params_area = QScrollArea()
        self.params_area.setWidgetResizable(True)
        self.params_area.setFrameShape(QFrame.NoFrame)
        self.params_host = QWidget()
        self.params_layout = QVBoxLayout(self.params_host)
        self.params_layout.setContentsMargins(0, 0, 6, 0)
        self.params_layout.setSpacing(2)
        self.params_area.setWidget(self.params_host)
        outer.addWidget(self.params_area, 1)

        outer.addWidget(theme.hline())
        quality_label = QLabel("Preview quality")
        self.quality = QComboBox()
        self.quality.addItems(list(QUALITY))
        self.quality.setCurrentText("Draft")
        self.quality.currentTextChanged.connect(self._quality_changed)
        outer.addWidget(row(quality_label, 1, self.quality))
        outer.addWidget(theme.muted(
            "Plots always run at Ultra sampling, whatever the preview shows.",
            wrap=True))

        self.add_button = QPushButton("Place on paper")
        self.add_button.setObjectName("primary")
        self.add_button.clicked.connect(self.addRequested.emit)
        outer.addWidget(self.add_button)

        self.refresh()

    # -- the palette -------------------------------------------------------- #

    def _fill_picker(self):
        self.picker.clear()
        for category, heading in (("generator", "— Generators —"),
                                  ("transform", "— Transforms —")):
            self.picker.addItem(heading)
            index = self.picker.count() - 1
            self.picker.model().item(index).setEnabled(False)
            for name, spec in sorted(MODULE_DEFS.items(),
                                     key=lambda kv: kv[1]["label"]):
                if spec["category"] == category:
                    self.picker.addItem(spec["label"], name)
                    self.picker.setItemData(
                        self.picker.count() - 1, spec.get("desc", ""),
                        Qt.ToolTipRole)
        self.picker.setCurrentIndex(1)

    def _add_module(self):
        module_type = self.picker.currentData()
        if not module_type:
            return
        self.document.add_module(module_type)
        self.refresh(select=len(self.document.steps) - 1)
        self.documentChanged.emit()

    # -- the pipeline ------------------------------------------------------- #

    def refresh(self, select=None):
        self._building = True
        self.steps.clear()
        for index in range(len(self.document.steps)):
            entry = QListWidgetItem("%d. %s" % (index + 1,
                                                self.document.describe_step(index)))
            self.steps.addItem(entry)
        self._building = False
        if select is None:
            select = self.selected_step
        if select is not None and 0 <= select < len(self.document.steps):
            self.steps.setCurrentRow(select)
        else:
            self.selected_step = None
            self._build_params()
        self._update_buttons()

    def _select_step(self, index):
        if self._building:
            return
        self.selected_step = index if index >= 0 else None
        self._build_params()
        self._update_buttons()

    def _update_buttons(self):
        has = self.selected_step is not None
        is_group = has and self.document.steps[self.selected_step].get("kind") == "group"
        for button in (self.up, self.down, self.delete, self.arm):
            button.setEnabled(has)
        self.group.setEnabled(has and not is_group)
        self.arm.setText("+ Arm" if is_group else "⑂ Arms")
        self.add_button.setEnabled(bool(self.document.steps))

    def _move(self, delta):
        if self.selected_step is None:
            return
        moved = self.document.move_step(self.selected_step, delta)
        self.refresh(select=moved)
        self.documentChanged.emit()

    def _remove(self):
        if self.selected_step is None:
            return
        self.document.remove_step(self.selected_step)
        self.refresh(select=min(self.selected_step,
                                len(self.document.steps) - 1) or None)
        self.documentChanged.emit()

    def _make_group(self):
        if self.selected_step is None:
            return
        self.document.make_group(self.selected_step)
        self.refresh(select=self.selected_step)
        self.documentChanged.emit()

    def _add_arm(self):
        if self.selected_step is None:
            return
        module_type = self.picker.currentData() or "circle"
        self.document.add_branch(self.selected_step, module_type)
        self.refresh(select=self.selected_step)
        self.documentChanged.emit()

    # -- the parameters -------------------------------------------------------- #

    def _build_params(self):
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self.selected_step is None:
            self.param_title.setText("Parameters")
            self.params_layout.addWidget(theme.muted("Select a step."))
            self.params_layout.addStretch(1)
            return

        self.param_title.setText("Parameters — %s"
                                 % self.document.describe_step(self.selected_step))
        for heading, params in self.document.modules_in(self.selected_step):
            if heading:
                self.params_layout.addWidget(theme.muted(heading))
            self._build_module_params(params)
        self.params_layout.addStretch(1)

    def _build_module_params(self, params):
        spec = MODULE_DEFS.get(params.get("type"))
        if not spec:
            self.params_layout.addWidget(
                theme.muted("No editor for '%s'." % params.get("type")))
            return
        drift_of = {p["drift_for"]: name
                    for name, p in spec["params"].items() if "drift_for" in p}
        for name, param_spec in spec["params"].items():
            if "drift_for" in param_spec:
                continue                       # shown beside the value it drifts
            end_name = drift_of.get(name)
            widget = ParamRow(
                name, param_spec, params.get(name, param_spec["default"]),
                drift_name=end_name,
                drift_spec=spec["params"].get(end_name),
                drift_value=params.get(end_name, params.get(name)))
            widget.valueChanged.connect(
                lambda key, value, target=params: self._set_param(target, key, value))
            self.params_layout.addWidget(widget)

    def _set_param(self, params, name, value):
        params[name] = value
        self.documentChanged.emit()

    # -- sampling ---------------------------------------------------------------- #

    def _quality_changed(self, label):
        initial, output = QUALITY[label]
        self.document.sampling.update(initial_samples=initial,
                                      output_samples=output)
        self.documentChanged.emit()

    def quality_sampling(self):
        initial, output = QUALITY[self.quality.currentText()]
        return {"initial_samples": initial, "output_samples": output}
