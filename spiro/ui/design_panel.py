"""The left side: the machine, and the numbers of whichever step is picked.

The pattern is a machine: arms that add movement, carriage paths that carry
the whole mechanism, table moves that turn the paper under it, clocks that
re-time what follows, and finishing once the ink is down. The panel shows
that machine as a strip of steps — each with a picture of the drawing as it
stands after that step — a gallery to add one from, the parameters of the
selected step with a slider beside every bounded number, and the finishing
passes underneath.

Everything here edits one :class:`spiro.pipeline.document.Document`;
nothing here knows about paper, pens or the plotter.
"""

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from spiro.pipeline.registry import COMMON_PARAMS, MODULE_DEFS, OSC_PREFIX
from spiro.ui import glyphs, theme
from spiro.ui.explainer import ExplainerCard
from spiro.ui.finishing_panel import FinishingPanel
from spiro.ui.gallery import GalleryDialog
from spiro.ui.step_strip import ROW, StepStrip
from spiro.ui.widgets import ParamRow, ScopeRow, row

QUALITY = {                    # label -> (initial samples, output samples)
    # Draft is what you see on first load, so it has to be enough to tell
    # what the pattern is; 3000 points was not.
    "Draft": (60000, 8000),
    "Fine": (120000, 16000),
    "Ultra": (400000, 50000),
}

STRIP_ROWS = 6                 # how many steps show before the strip scrolls


def legend():
    """The four kinds in their colours, one line."""
    parts = []
    for kind in ("generator", "path", "transform", "clock"):
        word = glyphs.KIND_WORDS[kind][0].lower()
        parts.append('<span style="color:%s">%s&nbsp;%s</span>'
                     % (glyphs.KIND_COLORS[kind].name(), glyphs.KIND_GLYPHS[kind], word))
    label = QLabel("&nbsp;&nbsp;".join(parts))
    label.setTextFormat(Qt.RichText)
    label.setWordWrap(True)
    label.setToolTip("\n".join("%s %s — %s" % (glyphs.KIND_GLYPHS[k], w, what)
                               for k, (w, what) in glyphs.KIND_WORDS.items()))
    return label


class DesignPanel(QWidget):
    """The machine, the gallery, the parameters, the finishing."""

    documentChanged = Signal()          # the pattern needs regenerating
    structureChanged = Signal()         # steps added, removed or reordered
    selectionChanged = Signal(object)   # the step index picked, or None
    addRequested = Signal()             # put the current pattern on the paper
    randomRequested = Signal()          # invent a pipeline
    renderWanted = Signal(object)       # small renders for the explainer

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self.selected_step = None
        self._show_more = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        self.random_button = QPushButton("🎲  Surprise me")
        self.random_button.setToolTip(
            "Build a pipeline from one of the recipes that turned out worth "
            "drawing (Ctrl+R)")
        self.random_button.clicked.connect(self.randomRequested.emit)
        outer.addWidget(self.random_button)
        self.recipe_label = theme.muted("", wrap=True)
        self.recipe_label.setVisible(False)
        outer.addWidget(self.recipe_label)

        # -- the machine ------------------------------------------------------- #
        outer.addWidget(theme.h2("The machine"))
        outer.addWidget(legend())
        self.strip = StepStrip()
        self.strip_area = QScrollArea()
        self.strip_area.setWidgetResizable(True)
        self.strip_area.setFrameShape(QFrame.NoFrame)
        self.strip_area.setWidget(self.strip)
        self.strip_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self.strip_area)
        self.strip.selected.connect(self._select_step)
        self.strip.moveRequested.connect(self._move)
        self.strip.removeRequested.connect(lambda _i: self._remove())

        self.add = QPushButton("+ Add a step…")
        self.add.setToolTip("Pick an arm, a path, a table move or a clock "
                            "from a gallery of what each one draws")
        self.add.clicked.connect(self._add_step)
        self.up = QPushButton("↑")
        self.down = QPushButton("↓")
        self.delete = QPushButton("Remove")
        self.delete.setObjectName("danger")
        self.clear = QPushButton("Clear")
        self.clear.setObjectName("danger")
        self.clear.setToolTip("Take every step and every finishing pass off — an empty machine")
        self.clear.clicked.connect(self.clear_machine)
        self.up.setToolTip("Move this step earlier (Alt+Up)")
        self.down.setToolTip("Move this step later (Alt+Down)")
        self.delete.setToolTip("Take this step out of the machine (Delete)")
        for button in (self.up, self.down):
            button.setFixedWidth(30)
        self.up.clicked.connect(lambda: self._move(self.selected_step, -1))
        self.down.clicked.connect(lambda: self._move(self.selected_step, 1))
        self.delete.clicked.connect(self._remove)
        outer.addWidget(row(self.add, self.up, self.down, 1, self.delete, self.clear,
                            spacing=4))

        outer.addWidget(theme.hline())

        # -- the parameters, then finishing, in one scroll ----------------------- #
        self.params_area = QScrollArea()
        self.params_area.setWidgetResizable(True)
        self.params_area.setFrameShape(QFrame.NoFrame)
        self.params_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 6, 0)
        host_layout.setSpacing(6)

        self.step_box = QWidget()
        self.step_layout = QVBoxLayout(self.step_box)
        self.step_layout.setContentsMargins(0, 0, 0, 0)
        self.step_layout.setSpacing(2)
        host_layout.addWidget(self.step_box)
        # The explainer lives outside the step box so a rebuild keeps its
        # cache; it is re-parented into the step box's layout on each build.
        self.explainer = ExplainerCard()
        self.explainer.renderWanted.connect(self.renderWanted.emit)
        self._explain_timer = QTimer(self)
        self._explain_timer.setSingleShot(True)
        self._explain_timer.setInterval(250)     # a slider drag, coalesced
        self._explain_timer.timeout.connect(self.explainer.refresh)

        host_layout.addWidget(theme.hline())
        self.finishing_toggle = QPushButton()
        self.finishing_toggle.setObjectName("flat")
        self.finishing_toggle.setCheckable(True)
        self.finishing_toggle.setToolTip(glyphs.KIND_WORDS["finish"][1])
        self.finishing_toggle.setStyleSheet(
            "QPushButton#flat { text-align: left; color: %s; font-weight: 600; }"
            % glyphs.KIND_COLORS["finish"].name())
        self.finishing_toggle.toggled.connect(self._show_finishing)
        host_layout.addWidget(self.finishing_toggle)
        self.finishing = FinishingPanel(document)
        self.finishing.documentChanged.connect(self._finishing_changed)
        host_layout.addWidget(self.finishing)
        host_layout.addStretch(1)
        self.params_area.setWidget(host)
        outer.addWidget(self.params_area, 1)

        outer.addWidget(theme.hline())
        quality_label = QLabel("Preview quality")
        self.quality = QComboBox()
        self.quality.addItems(list(QUALITY))
        self.quality.setCurrentText("Fine")
        self.quality.currentTextChanged.connect(self._quality_changed)
        outer.addWidget(row(quality_label, 1, self.quality))
        outer.addWidget(theme.muted(
            "Plots always run at Ultra sampling, whatever the preview shows.",
            wrap=True))

        self.add_button = QPushButton("Place on paper")
        self.add_button.setObjectName("primary")
        self.add_button.clicked.connect(self.addRequested.emit)
        outer.addWidget(self.add_button)

        self._show_finishing(False)
        self.refresh()

    # -- the machine ---------------------------------------------------------- #

    def refresh(self, select=None):
        """The document changed underneath: rebuild the strip, keep (or set)
        the selection, reload the finishing switches."""
        self.document.flatten()
        self.strip.set_steps(self.document.steps, select=select)
        # The strip is as tall as its steps, up to a few, then scrolls.
        self.strip_area.setFixedHeight(ROW * max(1, min(len(self.document.steps),
                                                        STRIP_ROWS)) + 6)
        self.selected_step = self.strip.selection
        self._build_params()
        self._update_buttons()
        self.finishing.reload()
        self._label_finishing()
        self.selectionChanged.emit(self.selected_step)

    def set_stages(self, drawing):
        """The engine's output after every step — the strip's pictures."""
        stages = list(getattr(drawing, "stages", None) or [])
        if drawing is None or len(stages) != len(self.document.steps):
            self.strip.set_stages([])
            return
        self.strip.set_stages([[stage] for stage in stages])

    def _select_step(self, index):
        self.selected_step = index
        self._build_params()
        self._update_buttons()
        self.selectionChanged.emit(index)

    def _update_buttons(self):
        has = self.selected_step is not None
        for button in (self.up, self.down, self.delete):
            button.setEnabled(has)
        self.clear.setEnabled(bool(self.document.steps) or bool(self.document.symmetry)
                              or bool(self.document.extras))
        self.add_button.setEnabled(bool(self.document.steps))

    def _add_step(self):
        dialog = GalleryDialog(self)
        dialog.chosen.connect(self.insert_module)
        dialog.exec()

    def insert_module(self, module_type):
        """Put a module after the selected step (or at the end)."""
        index = (self.selected_step + 1 if self.selected_step is not None
                 else len(self.document.steps))
        self.document.add_module(module_type, index)
        self.refresh(select=index)
        self.structureChanged.emit()
        self.documentChanged.emit()

    def clear_machine(self):
        """An empty machine: no steps, no finishing."""
        self.document.steps = []
        self.document.symmetry = {}
        self.document.extras = {}
        self.refresh(select=None)
        self.structureChanged.emit()
        self.documentChanged.emit()

    def _move(self, index, delta):
        if index is None:
            return
        moved = self.document.move_step(index, delta)
        self.refresh(select=moved)
        self.structureChanged.emit()
        self.documentChanged.emit()

    def _remove(self):
        if self.selected_step is None:
            return
        self.document.remove_step(self.selected_step)
        remaining = len(self.document.steps)
        self.refresh(select=min(self.selected_step, remaining - 1) if remaining else None)
        self.structureChanged.emit()
        self.documentChanged.emit()

    # -- the parameters -------------------------------------------------------- #

    def _clear_step_box(self):
        self.explainer.setParent(None)
        while self.step_layout.count():
            child = self.step_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _build_params(self):
        self._clear_step_box()
        if self.selected_step is None:
            self.step_layout.addWidget(theme.h2("Parameters"))
            self.step_layout.addWidget(theme.muted(
                "Pick a step above, or add one." if self.document.steps
                else "Add an arm to start the machine.", wrap=True))
            return

        params = self.document.steps[self.selected_step]["params"]
        module_type = params["type"]
        spec = MODULE_DEFS.get(module_type)
        kind = glyphs.kind_of(module_type)
        color = glyphs.KIND_COLORS[kind].name()
        word, what = glyphs.KIND_WORDS[kind]
        title = QLabel('<span style="color:%s">%s</span>&nbsp; %d. %s'
                       % (color, glyphs.KIND_GLYPHS[kind], self.selected_step + 1,
                          spec["label"] if spec else module_type))
        title.setTextFormat(Qt.RichText)
        title.setObjectName("h2")
        title.setToolTip("%s — %s" % (word, what))
        self.step_layout.addWidget(title)
        self.step_layout.addWidget(theme.muted(
            "%s · %s" % (word, glyphs.plain(module_type)), wrap=True))
        if not spec:
            self.step_layout.addWidget(
                theme.muted("No editor for '%s'." % module_type))
            return
        self.step_layout.addWidget(self.explainer)
        self.explainer.setVisible(False)
        self._step_spec = spec
        self._step_params = params
        self._step_kind = kind

        if kind == "transform":
            scope = ScopeRow(params.get("scope", "all"),
                             arms_available=self.document.arms_before(self.selected_step))
            scope.valueChanged.connect(
                lambda key, value, target=params: self._set_param(target, key, value))
            self.step_layout.addWidget(scope)

        drift_of = {p["drift_for"]: name
                    for name, p in spec["params"].items() if "drift_for" in p}
        plain, more = [], []
        for name, param_spec in spec["params"].items():
            if "drift_for" in param_spec or param_spec.get("hidden"):
                continue
            (more if param_spec.get("advanced") else plain).append((name, param_spec))
        for name, param_spec in COMMON_PARAMS.items():
            more.append((name, param_spec))

        for name, param_spec in plain:
            self.step_layout.addWidget(self._row_for(params, spec, drift_of, name, param_spec))
        if plain:
            self.explain(plain[0][0])

        if more:
            self.more_toggle = QPushButton()
            self.more_toggle.setObjectName("flat")
            self.more_toggle.setCheckable(True)
            self.more_toggle.setStyleSheet("QPushButton#flat { text-align: left; }")
            self.more_toggle.setToolTip("Centres, timing curve, and the knobs "
                                        "you rarely need")
            self.more_host = QWidget()
            more_layout = QVBoxLayout(self.more_host)
            more_layout.setContentsMargins(0, 0, 0, 0)
            more_layout.setSpacing(2)
            for name, param_spec in more:
                more_layout.addWidget(self._row_for(params, spec, drift_of, name, param_spec))
            self.more_toggle.toggled.connect(self._toggle_more)
            self.step_layout.addWidget(self.more_toggle)
            self.step_layout.addWidget(self.more_host)
            self.more_toggle.setChecked(self._show_more)
            self._toggle_more(self._show_more)

    def _row_for(self, params, spec, drift_of, name, param_spec):
        end_name = drift_of.get(name)
        widget = ParamRow(
            name, param_spec, params.get(name, param_spec["default"]),
            drift_name=end_name,
            drift_spec=spec["params"].get(end_name),
            drift_value=params.get(end_name, params.get(name, param_spec["default"])),
            osc_value=params.get(OSC_PREFIX + name))
        widget.valueChanged.connect(
            lambda key, value, target=params: self._set_param(target, key, value))
        widget.hovered.connect(self.explain)
        return widget

    def explain(self, name):
        """Show what one parameter of the selected step does."""
        spec = self._step_spec["params"].get(name) or COMMON_PARAMS.get(name)
        if spec is None:
            return
        self.explainer.show_param(self._step_params, name, spec, self._step_kind)

    def explained(self, ini, drawing):
        self.explainer.deliver(ini, drawing)

    def explain_failed(self, ini, message):
        self.explainer.fail(ini, message)

    def _toggle_more(self, on):
        self._show_more = on
        self.more_host.setVisible(on)
        count = self.more_host.layout().count()
        self.more_toggle.setText("%s More… (%d)" % ("▾" if on else "▸", count))

    def _set_param(self, params, name, value):
        if value is None:
            params.pop(name, None)       # an oscillation switched off
        else:
            params[name] = value
        self.strip.update()              # the summary line and the brackets
        if self.explainer.params is params:
            self._explain_timer.start()  # the pictures follow the new value
        self.documentChanged.emit()

    def show_recipe(self, name):
        """Say which recipe made what is on screen — it is worth knowing which
        of them you liked."""
        self.recipe_label.setText("from “%s”" % name if name else "")
        self.recipe_label.setVisible(bool(name))

    # -- finishing --------------------------------------------------------------- #

    def _show_finishing(self, on):
        self.finishing.setVisible(on)
        self._label_finishing()

    def _label_finishing(self):
        active = [FinishingLabel for FinishingLabel in self._active_finishing()]
        self.finishing_toggle.setText(
            "%s %s Finishing%s" % ("▾" if self.finishing_toggle.isChecked() else "▸",
                                   glyphs.KIND_GLYPHS["finish"],
                                   " — " + ", ".join(active) if active else ""))

    def _active_finishing(self):
        symmetry = self.document.symmetry or {}
        if int(symmetry.get("n_fold", 1) or 1) > 1 or symmetry.get("mirror"):
            yield "%d-fold" % int(symmetry.get("n_fold", 1) or 1)
        for name in ("pen_lift", "moire", "tile", "clip"):
            if self.document.extras.get(name):
                yield name.replace("_", " ")

    def _finishing_changed(self):
        self._label_finishing()
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
