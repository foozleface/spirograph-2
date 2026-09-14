"""Gate for the per-pen plot: one layer per pen, and a real stop between them.

The question this answers is the one the user asked for — "each plot added to
the canvas should be plottable using a different pen" — end to end. Two items,
two pens, and what the machine is handed is two layers containing exactly the
right paths, plotted in pen order, with the plotting thread genuinely blocked
between them until someone says the nib is swapped.

The machine is a recorder. No hardware, no port, no Qt event loop.
Run:  .venv/bin/python tests/test_pens.py
"""

import os
import re
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from axiplot import colorsplit  # noqa: E402
from spiro.pipeline import build_ini, run  # noqa: E402
from spiro.scene import Paper, Pen, Scene  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-60s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


def drawing(gear=35, samples=600):
    return run(build_ini(
        steps=[{"kind": "single", "params": {"type": "spirograph_gear",
                                             "fixed_teeth": 96,
                                             "rolling_teeth": gear}}],
        sampling={"initial_samples": samples * 12, "output_samples": samples}))


class Recorder:
    """Stands where the AxiDraw stands. Records what it was asked to plot and
    how long the caller waited between asks."""

    def __init__(self, stop_after=None):
        self.plotted = []
        self.previewed = []
        self.stop_after = stop_after

    def _record(self, svg_path, into):
        with open(svg_path) as handle:
            svg = handle.read()
        into.append({"path": svg_path, "svg": svg, "at": time.time(),
                     "strokes": sorted({p["stroke"] for p
                                        in colorsplit.parse(svg)["paths"]})})

    def plot(self, svg_path, opts=None, progress=True):
        self._record(svg_path, self.plotted)
        stopped = (self.stop_after is not None
                   and len(self.plotted) >= self.stop_after)
        return {"stopped": 1 if stopped else 0, "stats": {}, "raw": ""}

    def preview(self, svg_path, opts=None):
        """A dry run goes through preview, which on the real driver
        motion-plans without opening the port."""
        self._record(svg_path, self.previewed)
        return {"estTimeSec": 1.0, "drawLenM": 0.0, "penUpLenM": 0.0,
                "totalLenM": 0.0, "tookSec": 0.0, "raw": ""}


def build_scene():
    scene = Scene(paper=Paper.from_axidraw(3))
    scene.pens = [Pen("#000000", "Black"), Pen("#c0392b", "Red")]
    first = scene.add(drawing(), name="one")
    second = scene.add(drawing(gear=37), name="two")
    first.move_to(120, 80)
    first.set_width(90)
    second.move_to(430, 110)
    second.set_width(120)
    return scene, first, second


# -- the split ---------------------------------------------------------------- #

print("one layer per pen:")
scene, first, second = build_scene()
check("each item landed on its own pen", (first.pen, second.pen) == (0, 1))
check("both pens are in use", len(scene.pens_in_use()) == 2)

job = scene.job()
check("which makes it a colour job", job["mode"] == "color")
check("with the pens in the order they will be drawn",
      [p["label"] for p in job["pens"]] == ["Black", "Red"])

second.pen = 0
check("putting both on one pen makes it mono again", scene.job()["mode"] == "mono")
second.pen = 1

scene.pens.append(Pen("#1e8449", "Green"))
check("a pen with nothing on it is not a layer", len(scene.job()["pens"]) == 2)
scene.pens.pop()

# -- the run ------------------------------------------------------------------- #

print("plotting, layer by layer:")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])

from spiro.ui.workers import PlotWorker  # noqa: E402

events = []
recorder = Recorder()
worker = PlotWorker(make_driver=lambda progress, message: recorder)
worker.layerStarted.connect(lambda i, l, p, t: events.append(("start", i, p, t)))
worker.layerDone.connect(lambda i, l, r: events.append(("done", i)))
worker.penChange.connect(lambda i, l, prev: events.append(("pen", i)))
worker.finished.connect(lambda s: events.append(("finished", s)))
worker.failed.connect(lambda m: events.append(("failed", m)))


def plot_in_background(worker, job, **kw):
    thread = threading.Thread(target=worker.plot, args=(job, {"model": 3}),
                              kwargs=kw, daemon=True)
    thread.start()
    return thread


def wait_for(predicate, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


thread = plot_in_background(worker, scene.job())
paused = wait_for(lambda: any(e[0] == "pen" for e in events))
check("it stops before the second layer and asks for the pen", paused)
check("the first layer is already drawn, the second is not",
      len(recorder.plotted) == 1)

still_waiting = not wait_for(lambda: len(recorder.plotted) > 1, timeout=1.0)
check("and it really is blocked — nothing moves while it waits", still_waiting)

worker.resume_after_pen_change(True)
done = wait_for(lambda: any(e[0] == "finished" for e in events))
thread.join(5)
check("saying the pen is changed lets it carry on", done)
check("both layers were drawn, in pen order", len(recorder.plotted) == 2)
check("the first layer held only the black pen's paths",
      recorder.plotted[0]["strokes"] == ["#000000"])
check("the second held only the red pen's paths",
      recorder.plotted[1]["strokes"] == ["#c0392b"])

summary = [e[1] for e in events if e[0] == "finished"][0]
check("the run reports itself complete", summary["complete"]
      and not summary["stopped"])
check("and both layers are marked as on the paper",
      summary["state"].pending() == [])

_NUM = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")


def bounds(svg):
    xs, ys = [], []
    for path in colorsplit.parse(svg)["paths"]:
        nums = [float(n) for n in
                _NUM.findall(re.search(r'\bd="([^"]*)"', path["el"]).group(1))]
        xs += nums[0::2]
        ys += nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)


for layer, item in zip(recorder.plotted, (first, second)):
    got = bounds(layer["svg"])
    want = np.concatenate(item.paths_mm())
    check("%s went to the machine where it sits on the paper" % item.name,
          abs(got[0] - want.real.min()) < 0.05
          and abs(got[2] - want.real.max()) < 0.05)

# -- cancelling at the prompt ----------------------------------------------------- #

print("cancelling at the pen change:")
events.clear()
recorder = Recorder()
worker = PlotWorker(make_driver=lambda progress, message: recorder)
worker.penChange.connect(lambda i, l, prev: events.append(("pen", i)))
worker.finished.connect(lambda s: events.append(("finished", s)))

thread = plot_in_background(worker, scene.job())
wait_for(lambda: any(e[0] == "pen" for e in events))
worker.resume_after_pen_change(False)
wait_for(lambda: any(e[0] == "finished" for e in events))
thread.join(5)
summary = [e[1] for e in events if e[0] == "finished"][0]
check("stopping at the prompt leaves the second layer undrawn",
      len(recorder.plotted) == 1 and summary["stopped"])
check("the first layer stays marked, so plotting again resumes at the second",
      summary["state"].pending() == [1])

print("resuming:")
events.clear()
recorder2 = Recorder()
worker2 = PlotWorker(state=summary["state"],
                     make_driver=lambda progress, message: recorder2)
worker2.finished.connect(lambda s: events.append(("finished", s)))
thread = plot_in_background(worker2, scene.job())
wait_for(lambda: any(e[0] == "finished" for e in events))
thread.join(5)
check("only the layer that was left is drawn", len(recorder2.plotted) == 1)
check("and it is the red one", recorder2.plotted[0]["strokes"] == ["#c0392b"])
check("no pen prompt this time — it is the first layer of this run",
      not any(e[0] == "pen" for e in events))
check("the sheet is now complete",
      [e[1] for e in events if e[0] == "finished"][0]["complete"])

# -- a dry run never pauses --------------------------------------------------------- #

print("a dry run:")
events.clear()
recorder3 = Recorder()
worker3 = PlotWorker(make_driver=lambda progress, message: recorder3)
worker3.finished.connect(lambda s: events.append(("finished", s)))
worker3.penChange.connect(lambda i, l, prev: events.append(("pen", i)))
thread = plot_in_background(worker3, scene.job(), dry_run=True)
wait_for(lambda: any(e[0] == "finished" for e in events))
thread.join(5)
check("a dry run does not stop for a pen that is never changed",
      not any(e[0] == "pen" for e in events))
check("it rehearses every layer",
      len(recorder3.previewed) == 2
      and [l["strokes"] for l in recorder3.previewed]
      == [["#000000"], ["#c0392b"]])
check("without ever asking the machine to draw", recorder3.plotted == [])
check("and it finishes cleanly, not by failing",
      [e[1] for e in events if e[0] == "finished"][0]["complete"])

print()
print("pens: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
