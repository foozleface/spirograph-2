"""The window.

Design on the left, the machine on the right, and in the middle two tabs:
**Render**, the pattern being built on its own, and **Paper**, the sheet it is
placed on. A sheet — paper, pens, every placed pattern with its INI, position,
size and angle — saves to a ``.sheet.json`` and opens again as the same
arrangement, the curves regenerated in the background. The window owns
the two worker threads — one that generates, one that plots — and it is the
only place in the program that decides when either of them runs, because a
serial port needs exactly one owner and a hundred-thousand-point pipeline needs
exactly one queue.
"""

import atexit
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
from spiro.pipeline.document import Document, flatten_steps
from spiro.scene import SHEET_SUFFIX, Paper, Scene, item_inis
from spiro.ui import theme
from spiro.ui.canvas_view import PaperCanvas
from spiro.ui import glyphs
from spiro.ui.design_panel import DesignPanel
from spiro.ui.ideas_panel import IdeasPanel
from spiro.ui.library_panel import LibraryPanel
from spiro.ui.notify_panel import NotifyPanel
from spiro.ui.paper_window import PaperWindow
from spiro.ui.plot_panel import PlotPanel
from spiro.ui.render_view import RenderPanel
from spiro.ui.sheet_panel import SheetPanel
from spiro.ui.workers import PlotWorker, RenderWorker, manual_command

ROOT = Path(__file__).resolve().parents[2]


class MainWindow(QMainWindow):

    renderRequested = Signal(int, str)
    batchRequested = Signal(int, object)
    thumbsRequested = Signal(int, object)
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
        # Batch re-renders in flight: token -> (what to do with the drawings,
        # what to say while they arrive). A plot's Ultra pass and a sheet
        # being opened both go through here.
        self._pending_batches = {}
        self._pending_plot = None        # the batch token a plot is waiting on
        self.sheet_path = None           # the .sheet.json the paper came from
        self.inhibitor = awake.SleepInhibitor("A plot is running", "Spirograph")
        self._plot_started = 0.0
        self._status_until = 0.0         # see _say

        self._build_ui()
        self._start_workers()
        self._connect()
        self._new_document()

    # -- construction ---------------------------------------------------------- #

    def _build_ui(self):
        self.design = DesignPanel(self.document)
        self.ideas = IdeasPanel(ROOT)
        self.library = LibraryPanel(ROOT)
        left = QTabWidget()
        left.addTab(self.design, "Build")
        left.addTab(self.ideas, "Ideas")
        left.addTab(self.library, "Files")
        left.currentChanged.connect(self._left_tab_changed)
        self.left_tabs = left

        self.canvas = PaperCanvas(self.scene)
        self.render_panel = RenderPanel()
        self.render = self.render_panel.view
        self.sheet = SheetPanel(self.scene)
        self.plot = PlotPanel(QSettings("spirograph-2", "plotter"))
        self.notify = NotifyPanel(QSettings("spirograph-2", "notify"))

        right = QTabWidget()
        right.addTab(self.sheet, "Sheet")
        right.addTab(self.plot, "Plot")
        right.addTab(self.notify, "Alerts")
        self.right_tabs = right

        # The paper's home: the canvas, or a note saying where it went.
        self.paper_host = QWidget()
        centre_layout = QVBoxLayout(self.paper_host)
        centre_layout.setContentsMargins(0, 0, 0, 0)
        centre_layout.setSpacing(0)
        centre_layout.addWidget(self.canvas, 1)
        self.centre_layout = centre_layout
        self.detached_note = theme.muted(
            "The paper is in its own window.\nClose that window to bring it back.")
        self.detached_note.setAlignment(Qt.AlignCenter)
        self.detached_note.setVisible(False)
        centre_layout.addWidget(self.detached_note, 1)

        self.centre = QTabWidget()
        self.centre.addTab(self.render_panel, "Render")
        self.centre.addTab(self.paper_host, "Paper")
        self.centre.setDocumentMode(True)
        self.centre.currentChanged.connect(self._centre_tab_changed)

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
                ("Save &as…", QKeySequence.SaveAs, self._save_as)):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(fn)
            file_menu.addAction(action)
        file_menu.addSeparator()
        for label, shortcut, fn in (
                ("Open s&heet…", "Ctrl+Shift+O", self._open_sheet_dialog),
                ("Save shee&t", "Ctrl+Shift+S", self._save_sheet),
                ("Save sheet as…", "", self._save_sheet_as),
                ("Export sheet as &SVG…", "Ctrl+E", self._export_svg)):
            action = QAction(label, self)
            if shortcut:
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
                ("&Render", "Ctrl+1", lambda: self.centre.setCurrentWidget(self.render_panel)),
                ("&Paper", "Ctrl+2", lambda: self.centre.setCurrentWidget(self.paper_host)),
                ("&Fit the sheet", "Ctrl+0", self._fit_current),
                ("Zoom &in", QKeySequence.ZoomIn, lambda: self._zoom_current(1.2)),
                ("Zoom &out", QKeySequence.ZoomOut, lambda: self._zoom_current(1 / 1.2)),
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
        add_action = QAction("&Add a step…", self)
        add_action.setShortcut("Ctrl+Shift+A")
        add_action.triggered.connect(self.design._add_step)
        pattern_menu.addAction(add_action)
        play_action = QAction("Play the &machine", self)
        play_action.setShortcut("Ctrl+Space")
        play_action.triggered.connect(self.render_panel.play.toggle)
        pattern_menu.addAction(play_action)
        place = QAction("&Place on paper", self)
        place.setShortcut("Ctrl+Return")
        place.triggered.connect(self._place)
        pattern_menu.addAction(place)
        pattern_menu.addSeparator()
        take_off = QAction("&Take this pattern off the paper", self)
        take_off.setShortcut("Ctrl+Backspace")
        take_off.triggered.connect(self._remove_linked)
        pattern_menu.addAction(take_off)
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

        # Thumbnails for the Ideas tab: their own thread, so seventy small
        # renders never queue in front of the pattern being edited.
        self.thumb_thread = QThread(self)
        self.thumber = RenderWorker()
        self.thumber.moveToThread(self.thumb_thread)
        self.thumbsRequested.connect(self.thumber.render_each)
        self.thumber.eachFinished.connect(self._thumb_ready)
        self.thumber.eachFailed.connect(self._thumb_failed)
        self.thumb_thread.start()

        self.plot_thread = QThread(self)
        self.plotter = PlotWorker(self.layer_state)
        self.plotter.moveToThread(self.plot_thread)
        self.plotRequested.connect(self.plotter.plot)
        self.previewRequested.connect(self.plotter.preview)
        self.plot_thread.start()
        # A QThread destroyed while running aborts the process — and on
        # macOS that is a crash dialog. Whatever way the interpreter leaves,
        # the threads are stopped first.
        atexit.register(self._stop_threads)

    def _stop_threads(self):
        for name in ("render_thread", "thumb_thread", "plot_thread"):
            thread = getattr(self, name, None)
            if thread is None or not thread.isRunning():
                continue
            thread.quit()
            if not thread.wait(15000):
                thread.terminate()
                thread.wait(2000)

    def _connect(self):
        self.design.documentChanged.connect(self._schedule_render)
        self.design.addRequested.connect(self._place)
        self.design.newRequested.connect(self._new_document)
        self.design.offPaperRequested.connect(self._remove_linked)
        self.design.randomRequested.connect(self._randomize)
        self.design.selectionChanged.connect(self.render_panel.set_highlight)
        self.library.openRequested.connect(self._open_path)
        self.library.statusMessage.connect(self.status_left.setText)
        self.ideas.openRequested.connect(self._open_path)
        self.ideas.thumbnailsWanted.connect(
            lambda jobs: self._render_thumbnails([(("ideas", path), ini) for path, ini in jobs]))
        self.design.renderWanted.connect(self._render_thumbnails)
        # Have the pictures ready before anyone looks for them.
        QTimer.singleShot(1500, self.ideas.request_thumbnails)

        self.canvas.selectionChanged.connect(self._canvas_selected)
        self.canvas.itemChanged.connect(self._item_moved)
        self.canvas.deleteRequested.connect(self._remove_item)
        self.canvas.statusMessage.connect(self._canvas_message)

        self.sheet.sceneChanged.connect(self._scene_changed)
        self.sheet.selectionChanged.connect(self._sheet_selected)
        self.sheet.paperChanged.connect(self._paper_changed)
        self.sheet.cleared.connect(
            lambda: self.status_left.setText("The paper is clear."))
        self.sheet.saveSheetRequested.connect(self._save_sheet_as)
        self.sheet.openSheetRequested.connect(self._open_sheet_dialog)

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
        self._update_placement()
        self._update_title()
        self._schedule_render()

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open a pattern", str(ROOT),
                                              "Pattern files (*.ini)")
        if path:
            self._open_path(path)

    def _open_path(self, path):
        """Load a pattern file — from the Files tab, the dialog, or the
        command line. A sheet file goes to the paper instead."""
        if str(path).endswith(SHEET_SUFFIX):
            return self._open_sheet(path)
        try:
            loaded = Document.load(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could not open it", str(exc))
            return
        self.document.__dict__.update(loaded.__dict__)
        self.document.renew()
        self.design.refresh(select=0 if self.document.steps else None)
        self.design.show_recipe(None)
        self._update_placement()
        self.library.select(path)
        self.ideas.select(path)
        self.left_tabs.setCurrentWidget(self.design)
        self.centre.setCurrentWidget(self.render_panel)
        self._update_title()
        self._schedule_render()
        self.status_left.setText("Opened %s" % Path(path).name)

    def _randomize(self):
        """Build a pipeline from one of the recipes worth drawing."""
        made = recipes.random_pattern(avoid=self.recent_recipes)
        self.recent_recipes.append(made["index"])
        del self.recent_recipes[:-40]

        self.document.steps = flatten_steps(made["steps"])
        self.document.symmetry = made["symmetry"]
        self.document.output.update(made["output"])
        self.document.extras = {}
        self.document.path = None
        self.document.name = made["slug"]
        self.document.renew()

        self.left_tabs.setCurrentWidget(self.design)
        self.centre.setCurrentWidget(self.render_panel)
        self.design.refresh(select=0)
        self.design.show_recipe(made["name"])
        self._update_placement()
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
        if on:
            self.centre.setCurrentWidget(self.paper_host)
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

    def _sheet_label(self):
        return self.sheet_path.name if self.sheet_path else ""

    def _update_title(self):
        title = self._document_label()
        if self.sheet_path:
            title += "  ·  " + self._sheet_label()
        self.setWindowTitle("Spirograph — %s" % title)
        self.centre.setTabText(1, "Paper — %s" % self._sheet_label()
                               if self.sheet_path else "Paper")
        if self.paper_window is not None:
            self.paper_window.retitle(self._sheet_label() or self._document_label())

    def _fit_current(self):
        if self.centre.currentWidget() is self.render_panel:
            self.render.fit()
        else:
            self.canvas.fit()

    def _zoom_current(self, factor):
        if self.centre.currentWidget() is self.render_panel:
            self.render.zoom_by(factor)
        else:
            self.canvas.zoom_by(factor)

    def _left_tab_changed(self, _index):
        if self.left_tabs.currentWidget() is self.ideas:
            self.ideas.request_thumbnails()

    def _centre_tab_changed(self, _index):
        if self.centre.currentWidget() is self.paper_host:
            self.canvas.setFocus()
        else:
            self.render.setFocus()

    # -- the sheet as a file ------------------------------------------------------ #

    def _save_sheet(self):
        if self.sheet_path is None:
            return self._save_sheet_as()
        self._write_sheet(self.sheet_path)

    def _save_sheet_as(self):
        if not self.scene.items:
            self.status_left.setText("Nothing on the paper to save.")
            return
        suggested = self.sheet_path or (ROOT / ("sheet" + SHEET_SUFFIX))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save the sheet", str(suggested),
            "Sheet files (*%s)" % SHEET_SUFFIX)
        if not path:
            return
        if not path.endswith(SHEET_SUFFIX):
            path = path[:-5] if path.endswith(".json") else path
            path += SHEET_SUFFIX
        self._write_sheet(path)

    def _write_sheet(self, path):
        path = self.scene.save(path, extra={"paper_setup": self.sheet.paper_setup()})
        self.sheet_path = path
        self.library.refresh()
        self.library.select(path)
        self._update_title()
        self.status_left.setText("Saved %s — %d pattern%s"
                                 % (path.name, len(self.scene.items),
                                    "" if len(self.scene.items) == 1 else "s"))

    def _open_sheet_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open a sheet", str(ROOT), "Sheet files (*%s)" % SHEET_SUFFIX)
        if path:
            self._open_sheet(path)

    def _open_sheet(self, path):
        """Bring back a saved arrangement.

        The file holds the INI of each pattern, not its points, so every item
        is regenerated — in the background, at the preview quality, since a
        sheet saved after a plot carries Ultra INIs and a hundred thousand
        points apiece is a slow way to look at a layout. The plot path
        upgrades them again when it needs to.
        """
        try:
            data = Scene.read(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could not open the sheet", str(exc))
            return
        quality = self.design.quality_sampling()
        try:
            inis = [Document.from_ini(text).to_ini(quality)
                    for text in item_inis(data)]
        except Exception as exc:
            QMessageBox.warning(self, "Could not open the sheet",
                                "A pattern in it does not read: %s" % exc)
            return
        self.centre.setCurrentWidget(self.paper_host)
        self.right_tabs.setCurrentWidget(self.sheet)
        count = len(inis)
        self._run_batch(
            inis,
            lambda drawings: self._sheet_ready(Path(path), data, drawings),
            "opening %s — %d pattern%s to regenerate"
            % (Path(path).name, count, "" if count == 1 else "s"))

    def _sheet_ready(self, path, data, drawings):
        self.scene.apply_dict(data, drawings)
        if data.get("paper_setup"):
            self.sheet.restore_paper_setup(data["paper_setup"])
        self.sheet_path = path
        self.canvas.invalidate()
        self.canvas.select(None)
        self.sheet.refresh()
        self.canvas.fit()
        self._scene_changed()
        self.library.select(path)
        self._update_title()
        self.status_left.setText(
            "Opened %s — %d pattern%s on %s"
            % (path.name, len(self.scene.items),
               "" if len(self.scene.items) == 1 else "s",
               self.scene.paper.describe()))

    def _edit_item(self, item_id):
        """Bring a placed pattern's pipeline into Build.

        Selecting an item — in the list or on the canvas — does this, so the
        parameters of whatever is picked are the parameters on the left. The
        item and the document are then linked the way a freshly placed one
        is: an edit in Build regenerates the item in place, on the paper and
        in Render both. That is also how a sheet opened from a file becomes
        editable again — its items arrive with no document behind them.

        Whatever was in Build and not yet placed is replaced; a placed
        pattern is never lost this way, because its item holds the INI.
        """
        item = self.scene.find(item_id)
        if item is None:
            return
        if item.source is not None and item.source == self.document.token:
            return                       # already the pattern being built
        text = getattr(item.drawing, "ini_text", "")
        if not text:
            self.status_left.setText("%s has no pipeline to edit." % item.name)
            return
        try:
            loaded = Document.from_ini(text, name=item.name)
        except Exception as exc:
            QMessageBox.warning(self, "Could not read the pattern", str(exc))
            return
        self.document.__dict__.update(loaded.__dict__)
        self.document.path = None
        self.document.name = item.name
        if item.source is None:
            item.source = self.document.renew()
        else:
            self.document.token = item.source
        # Preview at the panel's quality, not whatever the item was last
        # generated at — a plotted item carries an Ultra INI.
        self.document.sampling.update(self.design.quality_sampling())
        self.design.refresh(select=0 if self.document.steps else None)
        self.design.show_recipe(None)
        self.left_tabs.setCurrentWidget(self.design)
        self._update_placement()
        self._update_title()
        self._schedule_render()
        self.status_left.setText("Editing %s — changes redraw it on the paper."
                                 % item.name)

    # -- generating ------------------------------------------------------------------ #

    def _schedule_render(self):
        self._render_timer.start()

    def _render_now(self):
        if self.document.is_empty():
            self.drawing = None
            self.render_panel.set_drawing(None)
            self.design.set_stages(None)
            # An empty machine draws nothing. Leaving its copy on the paper
            # would leave a picture no pipeline can make again — so it comes
            # off, and New pattern is the way to start another and keep the
            # paper as it is.
            stale = self._linked_items()
            if stale:
                for item in stale:
                    self.scene.remove(item.item_id)
                self.canvas.select(None)
                self.sheet.refresh()
                self._scene_changed()
                self._say("The machine is empty, so %s came off the paper. "
                          "New pattern starts another and leaves the paper alone."
                          % stale[-1].name)
            self._update_placement()
            return
        self.render_token += 1
        self._say_idle("Generating…")
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
        caption = ("%s — %d paths, %s points, %.0f x %.0f units"
                   % (self.document.describe_step(0) if self.document.steps else "pattern",
                      len(drawing.paths), "{:,}".format(drawing.point_count),
                      drawing.width, drawing.height))
        self._say_idle(caption)
        singles = [step["params"] for step in self.document.steps
                   if step.get("kind") == "single"]
        kinds = [glyphs.kind_of(params["type"]) for params in singles]
        scopes = [params.get("scope", "all") for params in singles]
        self.render_panel.set_drawing(drawing, "%s   ·   %s" % (self.document.name, caption),
                                      kinds, scopes)
        self.design.set_stages(drawing)
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
        if token in self._pending_batches:
            _, label = self._pending_batches.pop(token)
            if token == self._pending_plot:
                self._pending_plot = None
                self.plot.set_running(False)
            self.status_left.setText("Could not re-generate (%s): %s" % (label, message))
            return
        if token == self.render_token:
            self.status_left.setText("Generator error: %s" % message)

    def _render_thumbnails(self, jobs):
        self.plot_token += 1
        self.thumbsRequested.emit(self.plot_token, jobs)

    def _thumb_ready(self, _token, key, drawing):
        what, ref = key
        if what == "ideas":
            self.ideas.set_thumbnail(ref, drawing)
        else:
            self.design.explained(ref, drawing)

    def _thumb_failed(self, _token, key, message):
        what, ref = key
        if what == "ideas":
            self.ideas.set_failure(ref, message)
        else:
            self.design.explain_failed(ref, message)

    # -- the paper ---------------------------------------------------------------------- #

    def _place(self):
        """Put what is in Build on the paper, and follow *that* copy.

        The token is renewed first, so a second copy becomes the one an edit
        redraws and the first keeps the curves it was placed with. One
        pattern in Build, one live item on the paper.
        """
        if self.drawing is None:
            self.status_left.setText("Nothing generated yet.")
            return
        item = self.scene.add(self.drawing, name=self.document.name,
                              source=self.document.renew())
        self.scene.ensure_pens(item.pen + 1)
        self.sheet.refresh(select=item.item_id)
        self.canvas.select(item.item_id)
        self.canvas.invalidate()
        self.centre.setCurrentWidget(self.paper_host)
        self._update_placement()
        self._say("Placed %s — %.0f x %.0f mm at %.0f, %.0f on pen %d"
                  % (item.name, item.w_mm, item.h_mm, item.x_mm, item.y_mm,
                     item.pen + 1))

    def _say(self, text, hold=4.0):
        """Say something the person did, and hold it.

        Every click schedules a re-generation that finishes a moment later
        and wants the status line for its own caption; without a hold, "took
        it off the paper" is on screen for a fifth of a second.
        """
        self.status_left.setText(text)
        self._status_until = time.time() + hold

    def _say_idle(self, text):
        """The generator's own chatter: shown only if nothing is being held."""
        if time.time() >= self._status_until:
            self.status_left.setText(text)

    def _linked_items(self):
        """What on the paper is drawn by the pattern in Build."""
        return [item for item in self.scene.items
                if item.source == self.document.token]

    def _update_placement(self):
        """Tell Build whether it is looking at something on the paper."""
        linked = self._linked_items()
        self.design.set_placed(linked[-1] if linked else None)

    def _take_off(self, items):
        """Take items off the paper and say so. Nothing is lost by it:
        whatever is picked on the paper is the pattern in Build, so it can be
        placed again — which is why nothing here asks first."""
        if not items:
            return False
        for item in items:
            self.scene.remove(item.item_id)
        self.canvas.select(None)
        self.sheet.refresh()
        self._scene_changed()
        self._say("Took %s off the paper — it is still here in Build."
                  % items[-1].name)
        return True

    def _remove_item(self, item_id):
        """Take one pattern off the paper — the × on it, or the Delete key."""
        item = self.scene.find(item_id)
        if item is not None:
            self._take_off([item])

    def _remove_linked(self):
        """The Build panel's own way off the paper."""
        if not self._take_off(self._linked_items()):
            self._say("This pattern is not on the paper.")

    def _scene_changed(self):
        self.canvas.update()
        self.sheet.refresh(select=self.sheet.selected_id())
        self._update_placement()
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
        if item_id is not None:
            self._edit_item(item_id)

    def _sheet_selected(self, item_id):
        self.canvas.select(item_id)
        if item_id is not None:
            self._edit_item(item_id)

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
        self.plot.set_running(True)
        self.plot.set_progress(0, "re-generating at plot quality…")
        self._pending_plot = self._run_batch(
            inis, then,
            "re-generating %d pattern%s at plot quality — a preview is sampled "
            "for the screen, a plot for the paper"
            % (len(inis), "" if len(inis) == 1 else "s"))
        return True

    def _run_batch(self, inis, then, label):
        """Generate several INIs off the UI thread, then ``then(drawings)``.
        Returns the token the batch will report under."""
        self.plot_token += 1
        self._pending_batches[self.plot_token] = (then, label)
        self.status_left.setText(label[0].upper() + label[1:] + "…")
        self.batchRequested.emit(self.plot_token, inis)
        return self.plot_token

    def _plot_drawings_progress(self, token, done, total):
        if token not in self._pending_batches:
            return
        _, label = self._pending_batches[token]
        self.status_left.setText("%s — %d/%d" % (label[0].upper() + label[1:],
                                                 done, total))
        if token == self._pending_plot:
            self.plot.set_progress(done / max(total, 1),
                                   "re-generating %d/%d…" % (done, total))

    def _plot_drawings_ready(self, token, drawings):
        entry = self._pending_batches.pop(token, None)
        if entry is None:
            return
        then, _ = entry
        if token == self._pending_plot:
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
        self.render_panel.play.setChecked(False)
        self._stop_threads()
        super().closeEvent(event)


def _hms(seconds):
    seconds = int(round(seconds or 0))
    if seconds < 60:
        return "%d s" % seconds
    if seconds < 3600:
        return "%d min %02d s" % (seconds // 60, seconds % 60)
    return "%d h %02d min" % (seconds // 3600, (seconds % 3600) // 60)
