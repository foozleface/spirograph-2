"""Gate for the window's own decisions, driven headlessly.

Two of them matter enough to pin down:

* **A preview is sampled for the screen, a plot for the paper.** Facet depth on
  a plotted curve goes as chord squared over eight times the radius, so a Draft
  preview that looks smooth at screen resolution plots with visible flats on
  the tight lobes. The window re-generates every item at Ultra before it sends
  anything to the machine — and must not move anything while it does.
* **Placing, dragging and plotting agree.** The same property the scene gate
  checks, but reached the way a person reaches it: generate, place, drag, and
  read back what the plot job says.

Run:  .venv/bin/python tests/test_window.py
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np  # noqa: E402
from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from axiplot import colorsplit  # noqa: E402
from spiro.pipeline import PLOT_SAMPLING  # noqa: E402
from spiro.ui.main_window import MainWindow  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-60s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


def close(a, b, tol=0.05):
    return abs(a - b) <= tol


app = QApplication.instance() or QApplication([])


def pump(ms=60):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def wait_for(predicate, timeout=180.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        pump(40)
        if predicate():
            return True
    return False


_NUM = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")


def job_bounds(svg, stroke):
    xs, ys = [], []
    for path in colorsplit.parse(svg)["paths"]:
        if path["stroke"] != stroke:
            continue
        nums = [float(n) for n in
                _NUM.findall(re.search(r'\bd="([^"]*)"', path["el"]).group(1))]
        xs += nums[0::2]
        ys += nums[1::2]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


window = MainWindow()
window.resize(1400, 860)
window.show()
pump(200)

# -- generate and place ----------------------------------------------------- #

print("generate and place:")
window._render_now()
check("a fresh window generates something", wait_for(lambda: window.drawing))
check("at the preview quality, not the plot's",
      window.drawing.point_count == window.design.quality_sampling()["output_samples"])

window._place()
check("placing puts one item on the paper", len(window.scene.items) == 1)
first = window.scene.items[0]
check("centred on the sheet",
      close(first.x_mm, window.scene.paper.width_mm / 2, 0.01)
      and close(first.y_mm, window.scene.paper.height_mm / 2, 0.01))
check("and on the first pen", first.pen == 0)

window.document.add_module("rose")
window.document.name = "rose"
window.design.refresh(select=1)
window.drawing = None
window._render_now()
wait_for(lambda: window.drawing)
window._place()
second = window.scene.items[-1]
check("a second pattern lands on a second pen", second.pen == 1)
check("the pen list grew to hold it", len(window.scene.pens) >= 2)

first.move_to(120.0, 80.0)
first.set_width(90.0)
second.move_to(430.0, 110.0)
second.set_width(120.0)
window._scene_changed()
pump(100)

# -- the canvas paints where the item is -------------------------------------- #

print("the canvas:")
window.canvas.fit()
pump(60)
canvas = window.canvas
corner = canvas.to_px(*first.rect_mm[:2])
back = canvas.to_mm(corner)
check("screen pixels and paper millimetres convert both ways",
      close(back.x(), first.rect_mm[0], 1e-6) and close(back.y(), first.rect_mm[1], 1e-6))
check("the whole sheet is on screen after a fit",
      canvas.to_px(0, 0).x() >= 0
      and canvas.to_px(window.scene.paper.width_mm, 0).x() <= canvas.width())
check("a hit test through the canvas finds the item under it",
      canvas.scene.item_at(120.0, 80.0) is first)
check("and nothing where there is nothing",
      canvas.scene.item_at(5.0, 5.0) is None)

# -- the plot is upgraded to Ultra --------------------------------------------- #

print("plot quality:")
check("the window notices the sheet is at preview quality",
      len(window._needs_plot_quality()) == 2)

placements = [(item.x_mm, item.y_mm, item.w_mm, item.h_mm)
              for item in window.scene.items]
jobs = []
started = window._with_plot_quality(jobs.append)
check("asking to plot starts a re-render first", started)
check("which finishes", wait_for(lambda: jobs, timeout=600))

if jobs:
    check("every item was re-generated at plot sampling",
          all(d.point_count >= int(PLOT_SAMPLING["output_samples"])
              for d in jobs[0]),
          [d.point_count for d in jobs[0]])

    job = window._plot_job(jobs[0])
    check("and now nothing is stale", window._needs_plot_quality() == [])
    after = [(item.x_mm, item.y_mm, item.w_mm, item.h_mm)
             for item in window.scene.items]
    check("position and size come through the re-render untouched",
          all(close(one[0], two[0], 1e-9) and close(one[1], two[1], 1e-9)
              and close(one[3], two[3], 1e-9)
              for one, two in zip(placements, after)),
          (placements, after))
    # The width is derived: it is the height times the drawing's aspect ratio,
    # and that ratio is measured off the sampled points. Sampling more finely
    # finds the curve's extremes slightly more accurately, so the width shifts
    # by microns. It cannot be otherwise, and the bar is that it stays far
    # below what the machine can express -- 2032 steps to the inch is 0.0125 mm
    # a step, and the pen draws a line twenty times wider than that.
    drift = max(abs(one[2] - two[2]) for one, two in zip(placements, after))
    check("the derived width shifts by less than a pen line",
          drift < 0.05, "%.4f mm" % drift)

    check("the job is a two-pen colour job", job["mode"] == "color")
    for item, pen in zip(window.scene.items, window.scene.pens):
        bounds = job_bounds(job["svg"], pen.color)
        check("%s reaches the machine where it sits on the paper" % item.name,
              close(bounds[0], item.x_mm - item.w_mm / 2)
              and close(bounds[2], item.x_mm + item.w_mm / 2)
              and close((bounds[1] + bounds[3]) / 2, item.y_mm),
              "svg %s vs item at %.1f,%.1f %.1f wide"
              % (tuple(round(v, 2) for v in bounds), item.x_mm, item.y_mm, item.w_mm))

    points = sum(len(colorsplit.parse(job["svg"])["paths"]) for _ in (0,))
    check("the plotted SVG has paths for both pens", points >= 2)

# -- out of bounds ----------------------------------------------------------------- #

print("off the paper:")
second.move_to(window.scene.paper.width_mm - 5, 110)
window._scene_changed()
check("an item hanging off the edge is reported",
      [i.item_id for i in window.scene.out_of_bounds()] == [second.item_id])
check("and the window says so", "outside" in window.status_right.text())
second.move_to(430, 110)
window._scene_changed()
check("bringing it back clears the warning", window.status_right.text() == "")

# -- files -------------------------------------------------------------------------- #

print("files:")
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "gate.ini")
    window.document.save(path)
    check("saving writes an INI", os.path.getsize(path) > 0)
    from spiro.pipeline.document import Document  # noqa: E402
    again = Document.load(path)
    check("which reads back with the same steps",
          [s.get("kind") for s in again.steps]
          == [s.get("kind") for s in window.document.steps])

    svg_path = os.path.join(folder, "sheet.svg")
    with open(svg_path, "w") as handle:
        handle.write(window.scene.to_svg())
    check("exporting the sheet writes an SVG in millimetres",
          'width="%gmm"' % window.scene.paper.width_mm in open(svg_path).read())

window.plotter.stop()
print()
print("window: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
