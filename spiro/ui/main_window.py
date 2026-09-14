"""The window.

Design on the left, the paper in the middle, the machine on the right. It owns
the two worker threads — one that generates, one that plots — and it is the
only place in the program that decides when either of them runs, because a
serial port needs exactly one owner and a hundred-thousand-point pipeline needs
exactly one queue.
"""

import os
import re
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow,
                               QMessageBox, QSplitter, QStatusBar, QTabWidget,
                               QVBoxLayout, QWidget)

from axiplot import awake
from axiplot import run as axirun
from spiro.pipeline import PLOT_SAMPLING, recipes
from spiro.pipeline.document import Document
from spiro.scene import Paper, Scene
from spiro.ui import theme
from spiro.ui.canvas_view import PaperCanvas
from spiro.ui.design_panel import DesignPanel
from spiro.ui.effects_panel import EffectsPanel
from spiro.ui.library_panel import LibraryPanel
from spiro.ui.notify_panel import NotifyPanel
from spiro.ui.paper_window import PaperWindow
from spiro.ui.plot_panel import PlotPanel
from spiro.ui.sheet_panel import SheetPanel
from spiro.ui.workers import PlotWorker, RenderWorker, manual_command

ROOT = Path(__file__).resolve().parents[2]


class MainWindow(QMainWindow):

    renderRequested = Signal(int, str)
    batchRequested = Signal(int, object)
    plotRequested = Signal(object, object, bool, bool, object)
    previewRequested = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spirograph")
        self.resize(1600, 950)

        self.settings = QSettings("spirograph-2", "app")
        self.document = Document()
        self.scene = Scene(paper=Paper.from_axidraw(3))
        self.drawing = None               # the current preview, not yet placed
        self.render_token = 0
        self.layer_state = axirun.LayerState()
        self.plot_token = 0
        # The last few recipes, so pressing the button repeatedly explores
        # rather than circles. Forty is most of them.
        self.recent_recipes = []
        self._pending_plot = None        # what to do once the Ultra render lands
        self.inhibitor = awake.SleepInhibitor("A plot is running", "Spirograph")
        self._plot_started = 0.0

        self._build_ui()
        self._start_workers()
        self._connect()
        self._new_document()

    # -- construction ---------------------------------------------------------- #

    def _build_ui(self):
        self.design = DesignPanel(self.document)
        self.effects = EffectsPanel(self.document)
        self.library = LibraryPanel(ROOT)
        left = QTabWidget()
        left.addTab(self.design, "Build")
        left.addTab(self.effects, "Effects")
        left.addTab(self.library, "Files")
        self.left_tabs = left

        self.canvas = PaperCanvas(self.scene)
        self.sheet = SheetPanel(self.scene)
        self.plot = PlotPanel(QSettings("spirograph-2", "plotter"))
        self.notify = NotifyPanel(QSettings("spirograph-2", "notify"))

        right = QTabWidget()
        right.addTab(self.sheet, "Sheet")
        right.addTab(self.plot, "Plot")
        right.addTab(self.notify, "Alerts")
        self.right_tabs = right

        self.centre = QWidget()
        centre_layout = QVBoxLayout(self.centre)
        centre_layout.setContentsMargins(0, 0, 0, 0)
        centre_layout.setSpacing(0)
        centre_layout.addWidget(self.canvas, 1)
        self.centre_layout = centre_layout
        self.detached_note = theme.muted(
            "The paper is in its own window.\nClose that window to bring it back.")
        self.detached_note.setAlignment(Qt.AlignCenter)
        self.detached_note.setVisible(False)
        centre_layout.addWidget(self.detached_note, 1)

        self.splitter = QSplitter(Qt.Horizontal)
        for widget in (left, self.centre, right):
            widget.setMinimumWidth(320 if widget is self.centre else 280)
            self.splitter.addWidget(widget)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([340, 900, 380])
        self.setCentralWidget(self.splitter)
        self.paper_window = None
        self._panel_sizes = None

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_left = QLabel("")
        self.status_right = QLabel("")
        self.status.addWidget(self.status_left, 1)
        self.status.addPermanentWidget(self.status_right)

        self._build_menu()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        for label, shortcut, fn in (
                ("&New", QKeySequence.New, self._new_document),
                ("&Open…", QKeySequence.Open, self._open),
                ("&Save", QKeySequence.Save, self._save),
                ("Save &as…", QKeySequence.SaveAs, self._save_as),
                ("Export sheet as &SVG…", "Ctrl+E", self._export_svg)):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(fn)
            file_menu.addAction(action)
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu("&View")
        for label, shortcut, fn in (
                ("&Fit the sheet", "Ctrl+0", lambda: self.canvas.fit()),
                ("Zoom &in", QKeySequence.ZoomIn, lambda: self.canvas.zoom_by(1.2)),
                ("Zoom &out", QKeySequence.ZoomOut, lambda: self.canvas.zoom_by(1 / 1.2)),
                ("Toggle &grid", "Ctrl+G", self._toggle_grid)):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(fn)
            view_menu.addAction(action)
        view_menu.addSeparator()

        self.paper_only_action = QAction("Paper &only", self)
        self.paper_only_action.setCheckable(True)
        self.paper_only_action.setShortcut("F11")
        self.paper_only_action.setToolTip(
            "Hide the side panels and give the sheet the whole window")
        self.paper_only_action.toggled.connect(self._set_paper_only)
        view_menu.addAction(self.paper_only_action)

        self.detach_action = QAction("Paper in its own &window", self)
        self.detach_action.setCheckable(True)
        self.detach_action.setShortcut("Ctrl+Shift+P")
        self.detach_action.setToolTip(
            "Put the sheet in a window of its own — for a second screen")
        self.detach_action.toggled.connect(self._set_detached)
        view_menu.addAction(self.detach_action)

        pattern_menu = self.menuBar().addMenu("&Pattern")
        random_action = QAction("&Surprise me", self)
        random_action.setShortcut("Ctrl+R")
        random_action.triggered.connect(self._randomize)
        pattern_menu.addAction(random_action)
        place = QAction("&Place on paper", self)
        place.setShortcut("Ctrl+Return")
        place.triggered.connect(self._place)
        pattern_menu.addAction(place)
        pattern_menu.addSeparator()
        clear = QAction("&Clear the paper", self)
        clear.setShortcut("Ctrl+Shift+Backspace")
        clear.triggered.connect(lambda: self.sheet.clear_paper())
        pattern_menu.addAction(clear)

    def _start_workers(self):
        self.render_thread = QThread(self)
        self.renderer = RenderWorker()
        self.renderer.moveToThread(self.render_thread)
        self.renderRequested.connect(self.renderer.render)
        self.batchRequested.connect(self.renderer.render_batch)
        self.renderer.finished.connect(self._render_finished)
        self.renderer.batchFinished.connect(self._plot_drawings_ready)
        self.renderer.batchProgress.connect(self._plot_drawings_progress)
        self.renderer.failed.connect(self._render_failed)
        self.render_thread.start()

        self.plot_thread = QThread(self)
        self.plotter = PlotWorker(self.layer_state)
        self.plotter.moveToThread(self.plot_thread)
        self.plotRequested.connect(self.plotter.plot)
        self.previewRequested.connect(self.plotter.preview)
        self.plot_thread.start()

    def _connect(self):
        self.design.documentChanged.connect(self._schedule_render)
        self.design.structureChanged.connect(self.effects.reload)
        self.design.addRequested.connect(self._place)
        self.design.randomRequested.connect(self._randomize)
        self.library.openRequested.connect(self._open_path)
        self.library.statusMessage.connect(self.status_left.setText)
        self.effects.documentChanged.connect(self._schedule_render)

        self.canvas.selectionChanged.connect(self._canvas_selected)
        self.canvas.itemChanged.connect(self._item_moved)
        self.canvas.statusMessage.connect(self._canvas_message)

        self.sheet.sceneChanged.connect(self._scene_changed)
        self.sheet.selectionChanged.connect(self._sheet_selected)
        self.sheet.paperChanged.connect(self._paper_changed)
        self.sheet.cleared.connect(
            lambda: self.status_left.setText("The paper is clear."))

        self.plot.plotRequested.connect(self._start_plot)
        self.plot.previewRequested.connect(self._start_preview)
        self.plot.stopRequested.connect(self._stop_plot)
        self.plot.manualRequested.connect(self._manual)
        self.plot.penChangeAcknowledged.connect(self._pen_change_done)
        self.plot.resetLayersRequested.connect(self._reset_layers)

        self.plotter.prepared.connect(self._plot_prepared)
        self.plotter.layerStarted.connect(self._layer_started)
        self.plotter.layerDone.connect(self._layer_done)
        self.plotter.penChange.connect(self._ask_for_pen)
        self.plotter.progress.connect(self._plot_progress)
        self.plotter.message.connect(lambda text: self.status_left.setText(text))
        self.plotter.finished.connect(self._plot_finished)
        self.plotter.failed.connect(self._plot_failed)
        self.plotter.estimate.connect(self._estimate_ready)

        self.notify.statusMessage.connect(self.status_left.setText)

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(220)      # coalesce a slider being dragged
        self._render_timer.timeout.connect(self._render_now)

    # -- the document ------------------------------------------------------------ #

    def _new_document(self):
        self.document.steps = []
        self.document.output = {}
        self.document.sampling = dict(self.design.quality_sampling())
        self.document.symmetry = {}
        self.document.extras = {}
        self.document.path = None
        self.document.name = "untitled"
        self.document.renew()
        self.document.add_module("spirograph_gear")
        self.design.refresh(select=0)
        self.design.show_recipe(None)
        self.effects.reload()
        self._update_title()
        self._schedule_render()

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open a pattern", str(ROOT),
                                              "Pattern files (*.ini)")
        if path:
            self._open_path(path)

    def _open_path(self, path):
        """Load a pattern file — from the Files tab, the dialog, or the
        command line."""
        try:
            loaded = Document.load(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could not open it", str(exc))
            return
        self.document.__dict__.update(loaded.__dict__)
        self.document.renew()
        self.design.refresh(select=0 if self.document.steps else None)
        self.design.show_recipe(None)
        self.effects.reload()
        self.library.select(path)
        self._update_title()
        self._schedule_render()
        self.status_left.setText("Opened %s" % Path(path).name)

    def _randomize(self):
        """Build a pipeline from one of the recipes worth drawing."""
        made = recipes.random_pattern(avoid=self.recent_recipes)
        self.recent_recipes.append(made["index"])
        del self.recent_recipes[:-40]

        self.document.steps = made["steps"]
        self.document.symmetry = made["symmetry"]
        self.document.output.update(made["output"])
        self.document.extras = {}
        self.document.path = None
        self.document.name = made["slug"]
        self.document.renew()

        self.left_tabs.setCurrentWidget(self.design)
        self.design.refresh(select=0)
        self.design.show_recipe(made["name"])
        self.effects.reload()
        self._update_title()
        self._schedule_render()
        self.status_left.setText("%s — %d step%s"
                                 % (made["name"], len(made["steps"]),
                                    "" if len(made["steps"]) == 1 else "s"))

    # -- how much room the paper gets ------------------------------------------ #

    def _set_paper_only(self, on):
        """Hide the side panels so the sheet has the window."""
        if on and self._panel_sizes is None:
            self._panel_sizes = self.splitter.sizes()
        for index in (0, 2):
            self.splitter.widget(index).setVisible(not on)
        if not on and self._panel_sizes:
            self.splitter.setSizes(self._panel_sizes)
            self._panel_sizes = None
        self.canvas.fit()
        self.status_left.setText(
            "Paper only — F11 brings the panels back." if on else "")

    def _set_detached(self, on):
        """Move the canvas into a window of its own, or bring it back."""
        if on and self.paper_window is None:
            self.centre_layout.removeWidget(self.canvas)
            self.paper_window = PaperWindow(self.canvas, self._document_label())
            self.paper_window.closed.connect(self._reattach_paper)
            self.detached_note.setVisible(True)
            self.paper_window.show()
            self.canvas.fit()
            self.status_left.setText(
                "The paper is in its own window — F11 there for fullscreen.")
        elif not on and self.paper_window is not None:
            window, self.paper_window = self.paper_window, None
            window.closed.disconnect()
            window.release_canvas()
            window.close()
            window.deleteLater()
            self._reclaim_canvas()

    def _reattach_paper(self):
        """The paper window was closed by its own button."""
        self.paper_window = None
        self._reclaim_canvas()
        self.detach_action.blockSignals(True)
        self.detach_action.setChecked(False)
        self.detach_action.blockSignals(False)

    def _reclaim_canvas(self):
        self.detached_note.setVisible(False)
        self.centre_layout.insertWidget(0, self.canvas, 1)
        self.canvas.show()
        self.canvas.fit()
        self.status_left.setText("")

    def _canvas_message(self, text):
        """Where the pointer is, shown wherever the canvas currently lives."""
        self.status_right.setText(text)
        if self.paper_window is not None:
            self.paper_window.show_position(text)

    def _save(self):
        if self.document.path is None:
            return self._save_as()
        self.document.save()
        self.library.refresh()
        self.library.select(self.document.path)
        self.status_left.setText("Saved %s" % self.document.path.name)
        self._update_title()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save the pattern", str(ROOT / (self.document.name + ".ini")),
            "Pattern files (*.ini)")
        if not path:
            return
        if not path.endswith(".ini"):
            path += ".ini"
        self.document.save(path)
        self.library.refresh()
        self.library.select(path)
        self.status_left.setText("Saved %s" % Path(path).name)
        self._update_title()

    def _export_svg(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export the sheet", str(ROOT / "sheet.svg"), "SVG (*.svg)")
        if not path:
            return
        Path(path).write_text(self.scene.to_svg())
        self.status_left.setText("Wrote %s — %d mm across"
                                 % (Path(path).name, round(self.scene.paper.width_mm)))

    def _document_label(self):
        return self.document.path.name if self.document.path else "untitled"

    def _update_title(self):
        self.setWindowTitle("Spirograph — %s" % self._document_label())
        if self.paper_window is not None:
            self.paper_window.retitle(self._document_label())

    # -- generating ------------------------------------------------------------------ #

    def _schedule_render(self):
        self._render_timer.start()

    def _render_now(self):
        if self.document.is_empty():
            self.drawing = None
            return
        self.render_token += 1
        self.status_left.setText("Generating…")
        try:
            ini = self.document.to_ini(self.design.quality_sampling())
        except Exception as exc:
            self.status_left.setText("Bad pipeline: %s" % exc)
            return
        self.renderRequested.emit(self.render_token, ini)

    def _render_finished(self, token, drawing):
        if token != self.render_token:
            return                       # superseded by a later edit
        self.drawing = drawing
        self.status_left.setText(
            "%s — %d paths, %s points, %.0f x %.0f units"
            % (self.document.describe_step(0) if self.document.steps else "pattern",
               len(drawing.paths), "{:,}".format(drawing.point_count),
               drawing.width, drawing.height))
        # Re-generating replaces the drawing behind any item that came from
        # this document, so an edit is visible on the paper immediately.
        touched = False
        for item in self.scene.items:
            if item.source == self.document.token:
                item.drawing = drawing
                item._unit = None
                self.canvas.invalidate(item)
                touched = True
        if touched:
            self._scene_changed()

    def _render_failed(self, token, message):
        if self._pending_plot and token == self._pending_plot[0]:
            self._pending_plot = None
            self.plot.set_running(False)
            self.status_left.setText("Could not re-generate for the plot: %s"
                                     % message)
            return
        if token == self.render_token:
            self.status_left.setText("Generator error: %s" % message)

    # -- the paper ---------------------------------------------------------------------- #

    def _place(self):
        if self.drawing is None:
            self.status_left.setText("Nothing generated yet.")
            return
        item = self.scene.add(self.drawing, name=self.document.name,
                              source=self.document.token)
        self.scene.ensure_pens(item.pen + 1)
        self.sheet.refresh(select=item.item_id)
        self.canvas.select(item.item_id)
        self.canvas.invalidate()
        self.status_left.setText(
            "Placed %s — %.0f x %.0f mm at %.0f, %.0f on pen %d"
            % (item.name, item.w_mm, item.h_mm, item.x_mm, item.y_mm, item.pen + 1))

    def _scene_changed(self):
        self.canvas.update()
        self.sheet.refresh(select=self.sheet.selected_id())
        self._warn_out_of_bounds()

    def _paper_changed(self):
        self.canvas.fit()
        self._warn_out_of_bounds()

    def _warn_out_of_bounds(self):
        stray = self.scene.out_of_bounds()
        if stray:
            self.status_right.setText(
                "⚠ %d item%s outside the drawable area"
                % (len(stray), "" if len(stray) == 1 else "s"))
        else:
            self.status_right.setText("")

    def _canvas_selected(self, item_id):
        self.sheet.select(item_id)

    def _sheet_selected(self, item_id):
        self.canvas.select(item_id)

    def _item_moved(self, item_id):
        item = self.scene.find(item_id)
        if item is not None:
            self.sheet.refresh(select=item_id)
        self._warn_out_of_bounds()

    def _toggle_grid(self):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.update()

    # -- plotting ------------------------------------------------------------------------ #

    def _plot_job(self, drawings=None):
        """The job to send, optionally with each item's curves replaced.

        ``drawings`` is the Ultra-quality re-render, one per item in order.
        The placement is untouched: an item keeps its millimetres and takes
        the new curves at the same width, so a finer sampling changes the
        smoothness and nothing else.
        """
        if not self.scene.items:
            self.status_left.setText("Nothing on the paper to plot.")
            return None
        if not self.scene.pens_in_use():
            self.status_left.setText("No pen is switched on.")
            return None
        if drawings:
            # Only the curves change. An item's size is its height, so it is
            # untouched; the width follows the new drawing's aspect ratio,
            # which a finer sampling measures a few microns differently.
            for item, drawing in zip(self.scene.items, drawings):
                item.drawing = drawing
                item._unit = None
                self.canvas.invalidate(item)
            self.canvas.update()
        return self.scene.job(opts=self.plot.options(self.sheet.current_model()))

    def _needs_plot_quality(self):
        """The items whose curves came from a coarser preview.

        Facet depth on a plotted curve goes as chord squared over eight times
        the radius, so a Draft preview that looks smooth on screen plots with
        visible flats on the tight lobes. Plots always run at Ultra; this is
        what notices that the sheet is not there yet.
        """
        want = int(PLOT_SAMPLING["output_samples"])
        stale = []
        for item in self.scene.items:
            text = getattr(item.drawing, "ini_text", "")
            match = re.search(r"^output_samples\s*=\s*(\d+)", text, re.M)
            if not match or int(match.group(1)) < want:
                stale.append(item)
        return stale

    def _with_plot_quality(self, then):
        """Re-generate every item at plot sampling, then do ``then(drawings)``.

        Returns True if it started a re-render (and ``then`` will be called
        later), False if the sheet was already at plot quality.
        """
        if not self._needs_plot_quality():
            return False
        inis = []
        for item in self.scene.items:
            text = getattr(item.drawing, "ini_text", "")
            inis.append(Document.from_ini(text).to_ini(PLOT_SAMPLING)
                        if text else text)
        self.plot_token += 1
        self._pending_plot = (self.plot_token, then)
        self.plot.set_running(True)
        self.plot.set_progress(0, "re-generating at plot quality…")
        self.status_left.setText(
            "Re-generating %d pattern%s at plot quality — a preview is sampled "
            "for the screen, a plot for the paper."
            % (len(inis), "" if len(inis) == 1 else "s"))
        self.batchRequested.emit(self.plot_token, inis)
        return True

    def _plot_drawings_progress(self, token, done, total):
        if self._pending_plot and token == self._pending_plot[0]:
            self.plot.set_progress(done / max(total, 1),
                                   "re-generating %d/%d…" % (done, total))

    def _plot_drawings_ready(self, token, drawings):
        if not self._pending_plot or token != self._pending_plot[0]:
            return
        _, then = self._pending_plot
        self._pending_plot = None
        self.sheet.refresh(select=self.sheet.selected_id())
        then(drawings)

    def _start_preview(self):
        if not self.scene.items:
            self.status_left.setText("Nothing on the paper to plot.")
            return
        if self._with_plot_quality(self._preview_with):
            return
        self._preview_with(None)

    def _preview_with(self, drawings):
        job = self._plot_job(drawings)
        if job is None:
            self.plot.set_running(False)
            return
        self.plot.set_running(True)
        self.plot.set_progress(0, "estimating…")
        self.status_left.setText("Motion-planning every layer — no port is opened.")
        self.previewRequested.emit(job, self.plot.options(self.sheet.current_model()))

    def _estimate_ready(self, layers):
        total = sum(entry["seconds"] or 0 for entry in layers)
        lines = ["%s — %s, %d paths"
                 % (entry["label"], _hms(entry["seconds"]), entry["paths"] or 0)
                 for entry in layers]
        self.plot.estimate.setText("%s in total\n%s" % (_hms(total), "\n".join(lines)))
        self.plot.set_running(False)
        self.plot.set_progress(0, "")
        self.status_left.setText("Estimate: %s across %d layer%s"
                                 % (_hms(total), len(layers),
                                    "" if len(layers) == 1 else "s"))

    def _start_plot(self, dry_run):
        if not self.scene.items:
            self.status_left.setText("Nothing on the paper to plot.")
            return
        if self._with_plot_quality(lambda drawings:
                                   self._plot_with(drawings, dry_run)):
            return
        self._plot_with(None, dry_run)

    def _plot_with(self, drawings, dry_run):
        job = self._plot_job(drawings)
        if job is None:
            self.plot.set_running(False)
            return
        stray = self.scene.out_of_bounds()
        if stray and not dry_run:
            answer = QMessageBox.question(
                self, "Off the paper",
                "%d item%s reach%s outside the drawable area and will be "
                "clipped by the machine. Plot anyway?"
                % (len(stray), "" if len(stray) == 1 else "s",
                   "es" if len(stray) == 1 else ""),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                self.plot.set_running(False)
                return

        self.plot.save_settings()
        self.notify.save_settings()
        self.plot.set_running(True)
        self.plot.set_progress(0, "preparing…")
        self._plot_started = time.time()
        if not dry_run:
            self.inhibitor.start()
        notifier = None if dry_run else self.notify.notifier()
        self.plotRequested.emit(job, self.plot.options(self.sheet.current_model()),
                                dry_run, True, notifier)

    def _stop_plot(self):
        self.status_left.setText("Stopping — the pen will lift at the next segment.")
        self.plotter.stop()

    def _plot_prepared(self, layers, cleared):
        names = ", ".join(layer.get("label") or "?" for layer in layers)
        note = " (a different sheet — starting over)" if cleared else ""
        self.plot.layers_label.setText("%d layer%s: %s%s"
                                       % (len(layers),
                                          "" if len(layers) == 1 else "s",
                                          names, note))

    def _layer_started(self, index, layer, position, total):
        self.status_left.setText("Layer %d of %d — %s"
                                 % (position + 1, total,
                                    layer.get("label") or index + 1))

    def _layer_done(self, index, layer, result):
        self.plot.layers_label.setText(
            "%s done — %s" % (layer.get("label") or index + 1,
                              _hms(result.get("seconds"))))

    def _ask_for_pen(self, index, layer, previous):
        """The plotting thread is blocked in here until one of these buttons
        is pressed, so this is the moment the operator walks over."""
        nib = layer.get("label") or "the next"
        was = (previous or {}).get("label")
        self.right_tabs.setCurrentWidget(self.plot)
        self.plot.ask_for_pen(
            "%sPut in the <b>%s</b> pen and press on.<br>"
            "%s paths, about %s."
            % ("<b>%s</b> is done. " % was if was else "",
               nib, layer.get("paths") or "?", _hms(layer.get("estSec"))))
        self.status_left.setText("Waiting for the %s pen…" % nib)

    def _pen_change_done(self, go_on):
        self.plot.pen_prompt_done()
        self.plotter.resume_after_pen_change(go_on)

    def _plot_progress(self, phase, done_mm, total_mm, fraction, remaining):
        self.plot.set_progress(fraction, "%.0f%%  ·  %s left"
                               % (fraction * 100, _hms(remaining)))

    def _plot_finished(self, summary):
        self.inhibitor.stop()
        self.plot.set_running(False)
        self.plot.set_progress(1.0 if summary.get("complete") else 0.0, "")
        if summary.get("stopped"):
            pending = len(summary["state"].pending())
            self.status_left.setText(
                "Stopped. %d layer%s still to draw — plotting again resumes there."
                % (pending, "" if pending == 1 else "s"))
        else:
            self.status_left.setText("Finished — %d layer%s in %s"
                                     % (len(summary["layers"]),
                                        "" if len(summary["layers"]) == 1 else "s",
                                        _hms(summary.get("seconds"))))

    def _plot_failed(self, message):
        self.inhibitor.stop()
        self.plot.set_running(False)
        self.status_left.setText("Plot failed: %s" % message)
        QMessageBox.warning(self, "The plot did not run", message)

    def _reset_layers(self):
        self.layer_state.clear()
        self.plot.layers_label.setText("Layer marks cleared.")
        self.status_left.setText("Forgotten — the next plot draws every layer.")

    def _manual(self, command):
        """A one-off command to the machine, on this thread.

        Safe only because it is refused while a plot is running: two things
        holding the port is how a plot gets wrecked, and Linux will not stop us.
        """
        if self.plotter.busy:
            self.status_left.setText("The machine is busy plotting.")
            return
        try:
            manual_command(command, self.plot.options(self.sheet.current_model()))
            self.status_left.setText("Sent: %s" % command.replace("_", " "))
        except Exception as exc:
            traceback.print_exc()
            self.status_left.setText("Could not send %s: %s" % (command, exc))

    # -- shutdown ------------------------------------------------------------------------- #

    def closeEvent(self, event):
        if self.plotter.busy:
            answer = QMessageBox.question(
                self, "A plot is running",
                "Quitting will leave the pen where it is. Stop the plot and quit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.plotter.stop()
        if self.paper_window is not None:
            self.paper_window.closed.disconnect()
            self.paper_window.release_canvas()
            self.paper_window.close()
            self.paper_window = None
        self.plot.save_settings()
        self.notify.save_settings()
        self.inhibitor.stop()
        for thread in (self.render_thread, self.plot_thread):
            thread.quit()
            thread.wait(2000)
        super().closeEvent(event)


def _hms(seconds):
    seconds = int(round(seconds or 0))
    if seconds < 60:
        return "%d s" % seconds
    if seconds < 3600:
        return "%d min %02d s" % (seconds // 60, seconds % 60)
    return "%d h %02d min" % (seconds // 3600, (seconds % 3600) // 60)
