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
* **A sheet comes back as it was saved.** Save the paper, clear it, open the
  file: the same patterns at the same position, size, angle and pen — and
  editable again.

Run:  .venv/bin/python tests/test_window.py
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from PySide6.QtCore import QEventLoop, Qt, QTimer  # noqa: E402
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
ROOT_DIR = Path(__file__).resolve().parents[1]


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

# -- clearing the paper ------------------------------------------------------------ #

print("clearing:")
before = len(window.scene.items)
check("there is something to clear", before >= 2)
window.sheet.clear_paper(confirm=False)
check("clear takes everything off the sheet", window.scene.items == [])
check("and says so", "clear" in window.status_left.text().lower())
check("but leaves the pens alone", len(window.scene.pens) >= 2)
check("and leaves the pattern being built alone", bool(window.document.steps))
check("clearing an empty sheet is harmless",
      window.sheet.clear_paper(confirm=False) is False)
check("the canvas has nothing selected afterwards",
      window.canvas.selected_id is None or
      window.scene.find(window.canvas.selected_id) is None)

# -- an item tracks the document it came from, not one with the same name ------------ #

print("which pattern an item follows:")
window._render_now()
wait_for(lambda: window.drawing)
first = window.scene.add(window.drawing, name="twins", source=window.document.token)
old_token = window.document.token
window.document.renew()                      # as opening another file would
window.document.name = "twins"               # ...that happens to share a name
window.drawing = None
window._render_now()
wait_for(lambda: window.drawing)
second_drawing = window.drawing
window._render_finished(window.render_token, second_drawing)
check("a same-named pattern does not reach back into a placed item",
      first.drawing is not second_drawing)
check("the item still points at the document it was placed from",
      first.source == old_token)
window.scene.items = []

# -- room for the paper --------------------------------------------------------------- #

print("paper only:")
window.paper_only_action.setChecked(True)
pump(80)
check("both side panels are hidden",
      not window.splitter.widget(0).isVisible()
      and not window.splitter.widget(2).isVisible())
check("the canvas is still in the main window", window.canvas.window() is window)
window.paper_only_action.setChecked(False)
pump(80)
check("and they come back",
      window.splitter.widget(0).isVisible() and window.splitter.widget(2).isVisible())

print("paper in its own window:")
window.detach_action.setChecked(True)
pump(120)
check("a paper window opens", window.paper_window is not None)
check("the canvas moved into it — the same widget, not a copy",
      window.canvas.window() is window.paper_window)
check("the main window says where the paper went",
      window.detached_note.isVisible())
check("the two windows are not called the same thing",
      window.paper_window.windowTitle() != window.windowTitle()
      and "Paper" in window.paper_window.windowTitle())
window.canvas.statusMessage.emit("12.0, 34.0 mm")
pump(30)
check("pointer position is reported in the paper window too",
      "12.0" in window.paper_window.readout.text())

window.paper_window.close()
pump(120)
check("closing it brings the canvas home", window.canvas.window() is window)
check("the canvas survived the trip",
      window.canvas.isVisible() and window.canvas.scene is window.scene)
check("and the menu item un-checks itself", not window.detach_action.isChecked())
check("the placeholder is gone", not window.detached_note.isVisible())

window.detach_action.setChecked(True)
pump(120)
window.detach_action.setChecked(False)
pump(120)
check("detaching and re-attaching from the menu works too",
      window.paper_window is None and window.canvas.window() is window)

# -- the file list ----------------------------------------------------------------------- #

print("the file list:")
check("it found the project's patterns", window.library.tree.topLevelItemCount() > 0)
window.library.filter.setText("harmonograph")
pump(30)
check("filtering narrows it", "match" in window.library.count.text())
window.library.filter.setText("")
pump(30)
check("and clearing the filter restores it", "pattern" in window.library.count.text())

target = None
for index in range(window.library.tree.topLevelItemCount()):
    item = window.library.tree.topLevelItem(index)
    if item.data(0, Qt.UserRole):
        target = item
        break
check("the list holds openable files", target is not None)
if target is not None:
    window.library.openRequested.emit(target.data(0, Qt.UserRole))
    pump(60)
    check("clicking one loads it",
          window.document.path is not None
          and window.document.path.name == target.text(0) + ".ini")
    check("and lands in Build", window.left_tabs.currentWidget() is window.design)
    check("and the pipeline panel shows its steps",
          window.design.steps.count() == len(window.document.steps))

# -- render and paper are two tabs --------------------------------------------------------- #

print("two tabs:")
check("the centre is Render and Paper",
      [window.centre.tabText(i) for i in range(window.centre.count())][:2]
      == ["Render", "Paper"])
window.drawing = None
window._render_now()
wait_for(lambda: window.drawing)
check("the render view shows the pattern being built",
      window.render.drawing is window.drawing)
check("and says what it is", window.document.name in window.render.caption)
window.centre.setCurrentWidget(window.render)
window._place()
check("placing switches to the paper", window.centre.currentWidget() is window.paper_host)
placed = window.scene.items[-1]
window.sheet.select(placed.item_id)
pump(30)
check("the sheet panel's editors follow the selection",
      close(window.sheet.sel_x.value(), placed.x_mm, 0.1)
      and close(window.sheet.sel_w.value(), placed.w_mm, 0.1))
window.sheet.sel_rot.setValue(30)
window.sheet.sel_x.setValue(150)
pump(30)
check("typing an angle turns the item", close(placed.rotation_deg, 30.0, 1e-9))
check("typing a position moves it", close(placed.x_mm, 150.0, 1e-9))
window.canvas.select(placed.item_id)
from PySide6.QtGui import QKeyEvent  # noqa: E402
from PySide6.QtCore import QEvent  # noqa: E402
window.canvas.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_BracketRight,
                                      Qt.ShiftModifier))
check("] with shift turns it fifteen degrees", close(placed.rotation_deg, 45.0, 1e-9))
window.canvas.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_BracketLeft,
                                      Qt.NoModifier))
check("[ turns it back one", close(placed.rotation_deg, 44.0, 1e-9))

# -- the sheet as a file ---------------------------------------------------------------- #

print("the sheet file:")
window.document.add_module("rose")
window.document.name = "rose-on-sheet"
window.document.renew()
window.design.refresh(select=1)
saved_steps = len(window.document.steps)
window.drawing = None
window._render_now()
wait_for(lambda: window.drawing)
window._place()
window.scene.items[-1].move_to(400, 120)
window.scene.items[-1].set_width(70)
window.scene.items[-1].rotate_to(300)
window.scene.pens[1].label = "Violet"
window._scene_changed()
kept = [(i.name, i.x_mm, i.y_mm, i.w_mm, i.rotation_deg, i.pen)
        for i in window.scene.items]
check("two patterns to save", len(kept) == 2)

with tempfile.TemporaryDirectory() as folder:
    sheet_path = os.path.join(folder, "gate.sheet.json")
    window._write_sheet(sheet_path)
    check("saving writes the sheet file", os.path.getsize(sheet_path) > 0)
    check("the window knows which sheet it is on",
          window.sheet_path is not None and window.sheet_path.name == "gate.sheet.json")
    check("and says so in the title", "gate.sheet.json" in window.windowTitle())

    window.sheet.clear_paper(confirm=False)
    window.sheet_path = None
    window.scene.pens[1].label = "Something else"
    window.centre.setCurrentWidget(window.render)
    window._open_path(sheet_path)
    check("opening a sheet regenerates every pattern in the background",
          wait_for(lambda: len(window.scene.items) == 2, timeout=300))
    pump(100)
    check("it opens on the paper", window.centre.currentWidget() is window.paper_host)
    back = [(i.name, i.x_mm, i.y_mm, i.w_mm, i.rotation_deg, i.pen)
            for i in window.scene.items]
    check("name, position, width, angle and pen all come back",
          all(one[0] == two[0] and one[5] == two[5]
              and all(close(a, b, 1e-3) for a, b in zip(one[1:5], two[1:5]))
              for one, two in zip(kept, back)),
          (kept, back))
    check("the pens come back", window.scene.pens[1].label == "Violet")
    check("at the preview quality, not whatever was saved",
          all(i.point_count() == window.design.quality_sampling()["output_samples"]
              for i in window.scene.items))
    check("so the plot path will still upgrade them",
          len(window._needs_plot_quality()) == 2)
    check("the window is on the sheet it opened",
          window.sheet_path is not None and window.sheet_path.name == "gate.sheet.json")

    # Selecting: a reopened item has no document behind it until picked.
    target = window.scene.items[1]
    check("a reopened item is not tracking any document", target.source is None)
    window.left_tabs.setCurrentWidget(window.library)
    window.sheet.select(target.item_id)
    window.sheet.selectionChanged.emit(target.item_id)   # as a click does
    pump(30)
    check("selecting it brings its pipeline into Build",
          window.document.name == target.name
          and len(window.document.steps) == saved_steps)
    check("and shows the Build tab", window.left_tabs.currentWidget() is window.design)
    check("without leaving the paper", window.centre.currentWidget() is window.paper_host)
    check("and links the item to the document", target.source == window.document.token)
    other = window.scene.items[0]
    window.canvas._select(other.item_id)              # a click on the canvas
    pump(30)
    check("clicking on the canvas does the same",
          window.document.name == other.name and other.source == window.document.token)
    window.canvas._select(target.item_id)
    pump(30)
    was = target.drawing
    window._render_now()
    check("so an edit in Build regenerates it on the paper",
          wait_for(lambda: target.drawing is not was))
    check("without moving it", close(target.rotation_deg, 300.0, 1e-9)
          and close(target.x_mm, 400.0, 1e-9))

    window.library.root = Path(folder)
    window.library.refresh()
    pump(30)
    rows = [(window.library.tree.topLevelItem(i).text(0),
             window.library.tree.topLevelItem(i).text(1))
            for i in range(window.library.tree.topLevelItemCount())]
    check("the file list shows the sheet, with what is on it",
          any(name == "gate" and "sheet" in text and "2 patterns" in text
              for name, text in rows), rows)
    window.library.root = ROOT_DIR
    window.library.refresh()

window.sheet.clear_paper(confirm=False)
window.sheet_path = None
window._update_title()

# -- the randomizer, from the window ------------------------------------------------------- #

print("surprise me:")
window._randomize()
check("it builds a pipeline", bool(window.document.steps))
check("names the document after the recipe",
      window.document.name and window.document.name.isascii())
check("says which recipe it used", window.design.recipe_label.isVisible())
check("and forgets the file it came from", window.document.path is None)
picks = set()
for _ in range(12):
    window._randomize()
    picks.add(window.design.recipe_label.text())
check("pressing it repeatedly does not sit on one recipe", len(picks) >= 10, len(picks))
check("it remembers what it has used recently",
      len(window.recent_recipes) == len(set(window.recent_recipes)))

window.plotter.stop()
print()
print("window: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
