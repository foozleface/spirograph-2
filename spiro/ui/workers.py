"""The two things that must not happen on the UI thread: generating and plotting.

Both are QObjects moved onto a QThread and talk back only in signals, which is
the only safe way to touch a widget from work that takes minutes.

The plot worker is the more interesting one. It hands
:func:`axiplot.run.plot_job` an in-process driver, so progress arrives in
millimetres of travel rather than as a spinner, and a pen change becomes a real
pause: the loop blocks in ``on_layer_start`` until the window says the next nib
is in. Nothing here opens a serial port itself — that is the driver's business,
and doing it twice is how a plot gets wrecked.
"""

import threading
import time
import traceback

from PySide6.QtCore import QObject, Signal

from axiplot import driver as axidriver
from axiplot import plotter as plotmod
from axiplot import run as axirun
from spiro.pipeline import engine


class RenderWorker(QObject):
    """Runs a pipeline. One at a time; a newer request supersedes an older."""

    finished = Signal(int, object)        # token, Drawing
    failed = Signal(int, str)
    started = Signal(int)

    def __init__(self):
        super().__init__()
        self.token = 0

    def render(self, token, ini_text):
        self.started.emit(token)
        try:
            drawing = engine.run(ini_text)
        except Exception as exc:
            traceback.print_exc()
            self.failed.emit(token, str(exc))
            return
        self.finished.emit(token, drawing)


class PlotWorker(QObject):
    """Plots a scene's job, layer by layer, reporting as it goes."""

    # (phase, done_mm, total_mm, fraction, remaining_s)
    progress = Signal(str, float, float, float, float)
    prepared = Signal(object, bool)       # layers, state was cleared
    layerStarted = Signal(int, object, int, int)   # index, layer, position, total
    layerDone = Signal(int, object, object)        # index, layer, result
    penChange = Signal(int, object, object)        # index, layer about to start, the one just done
    message = Signal(str)
    finished = Signal(object)             # summary dict
    failed = Signal(str)
    estimate = Signal(object)             # per-layer seconds

    def __init__(self, state=None):
        super().__init__()
        self.state = state or axirun.LayerState()
        self.driver = None
        self._stop = threading.Event()
        self._continue = threading.Event()
        self._aborted = False
        self._previous = None
        self.busy = False
        # A plot with more than one pen stops between layers so the nib can be
        # changed. Turned off for a dry run, where nothing is drawn.
        self.pause_between_layers = True

    # -- control ----------------------------------------------------------- #

    def stop(self):
        """Ask the machine to stop at the next opportunity. The AxiDraw's own
        pause receiver does the work; a stopped layer stays unmarked, so the
        next run resumes at it rather than redrawing what is already down."""
        self._stop.set()
        self._continue.set()
        if self.driver is not None:
            try:
                self.driver.stop()
            except Exception:
                pass

    def resume_after_pen_change(self, go_on=True):
        """Called from the UI thread when the operator has swapped the nib."""
        self._aborted = not go_on
        self._continue.set()

    # -- jobs ---------------------------------------------------------------- #

    def preview(self, job, opts):
        """Motion-plan every layer without touching the machine — the honest
        time estimate, and proof the file is plottable."""
        try:
            if not axidriver.available():
                self.failed.emit("AxiDraw Python sources not found — install the "
                                 "AxiDraw API into .venv (launch.sh does it).")
                return
            self.busy = True
            driver = axidriver.InProcessDriver(on_message=self.message.emit)
            prep = plotmod.prepare_layers(job)
            seconds = axirun.estimate_layers(prep["layers"], driver,
                                             dict(prep["opts"], **opts))
            self.estimate.emit([
                {"label": layer.get("label"), "hex": layer.get("hex"),
                 "seconds": est, "paths": layer.get("paths"),
                 "drawLenMm": layer.get("drawLenMm")}
                for layer, est in zip(prep["layers"], seconds)])
        except Exception as exc:
            traceback.print_exc()
            self.failed.emit(str(exc))
        finally:
            self.busy = False

    def plot(self, job, opts, dry_run=False, skip_done=True, notifier=None,
             pause_between_layers=True):
        """Plot the job. ``dry_run`` motion-plans instead of moving the pen."""
        if self.busy:
            self.failed.emit("A plot is already running")
            return
        self.busy = True
        self._stop.clear()
        self._aborted = False
        self._previous = None
        self.pause_between_layers = bool(pause_between_layers) and not dry_run
        try:
            if not axidriver.available():
                self.failed.emit("AxiDraw Python sources not found — install the "
                                 "AxiDraw API into .venv (launch.sh does it).")
                return

            def on_progress(**kw):
                self.progress.emit(kw.get("phase") or "", kw.get("done_mm") or 0.0,
                                   kw.get("total_mm") or 0.0,
                                   kw.get("fraction") or 0.0,
                                   kw.get("remaining") or 0.0)

            self.driver = axidriver.InProcessDriver(on_progress=on_progress,
                                                    on_message=self.message.emit)
            if dry_run:
                # preview=True never opens the port; the same code path
                # otherwise, so a dry run really does rehearse the plot.
                self.driver.plot = lambda path, o=None, progress=True: dict(
                    self.driver.preview(path, o), stopped=0)

            summary = axirun.plot_job(
                job, self.driver, state=self.state, notifier=notifier,
                opts=opts, skip_done=skip_done,
                on_prepare=lambda layers, cleared: self.prepared.emit(layers, cleared),
                on_layer_start=self._layer_start,
                on_layer_done=self._layer_done,
                on_done=None)
            self.finished.emit(summary)
        except Exception as exc:
            traceback.print_exc()
            self.failed.emit(str(exc))
        finally:
            self.driver = None
            self.busy = False

    # -- the pen change ------------------------------------------------------- #

    def _layer_start(self, index, layer, position, total):
        """Called by plot_job before each layer. Returning False aborts the run
        without marking anything, which is what a cancelled pen change means."""
        if self._stop.is_set():
            return False
        self.layerStarted.emit(index, layer, position, total)
        if position == 0 or not self.pause_between_layers:
            return True
        # Every layer after the first needs a different nib in the holder.
        # Block here — this is the plotting thread, not the UI's — until the
        # window says the swap is done.
        self._continue.clear()
        self.penChange.emit(index, layer, self._previous)
        while not self._continue.is_set():
            self._continue.wait(0.1)
        return not (self._aborted or self._stop.is_set())

    def _layer_done(self, index, layer, result, ok):
        self._previous = layer
        self.layerDone.emit(index, layer, result)
