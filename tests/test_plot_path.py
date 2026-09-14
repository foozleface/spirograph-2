"""Gate for the whole path from the canvas to the machine.

The scene round trip (tests/test_scene.py) proves the SVG matches the
placement. This proves the rest of it: that what axiplot actually hands the
AxiDraw — after sizing to physical millimetres, splitting into per-pen layers
and running the path optimiser over it — is still the same drawing in the same
place. Those three steps are string and geometry surgery on the file, and each
is a chance to move it.

Also checks the canvas: the transform the widget paints through is built from
the same four numbers as the geometry, so the pixels and the paper agree.

The AxiDraw is exercised in preview mode, which motion-plans and never opens a
port. No hardware, no network. Run:

    .venv/bin/python tests/test_plot_path.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from axiplot import colorsplit, driver as axidriver, plotter as plotmod, run as axirun  # noqa: E402
from spiro.pipeline import build_ini, run  # noqa: E402
from spiro.scene import Paper, Scene  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-60s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


def close(a, b, tol=0.05):
    return abs(a - b) <= tol


_NUM = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")


def svg_bounds(svg):
    xs, ys = [], []
    for path in colorsplit.parse(svg)["paths"]:
        nums = [float(n) for n in
                _NUM.findall(re.search(r'\bd="([^"]*)"', path["el"]).group(1))]
        xs += nums[0::2]
        ys += nums[1::2]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def drawing(gear=35, samples=1200):
    return run(build_ini(
        steps=[{"kind": "single", "params": {"type": "spirograph_gear",
                                             "fixed_teeth": 96,
                                             "rolling_teeth": gear}}],
        sampling={"initial_samples": samples * 12, "output_samples": samples}))


# A deliberately awkward arrangement: a wide bed, two patterns of different
# sizes, neither centred, one turned. Everything the old code got wrong.
scene = Scene(paper=Paper.from_axidraw(3))          # 594.87 x 217.93 mm
left = scene.add(drawing(), name="left")
right = scene.add(drawing(gear=37), name="right")
left.move_to(120.0, 80.0)
left.set_width(90.0)
right.move_to(430.0, 110.0)
right.set_width(150.0)
right.rotation_deg = 30.0

PLACEMENTS = {0: (120.0, 80.0, 90.0), 1: (430.0, 110.0, 150.0)}

print("the geometry the placement describes:")
for item in scene.items:
    points = np.concatenate(item.paths_mm())
    x, y, _ = PLACEMENTS[item.pen]
    check("%s is centred where it was put" % item.name,
          close((points.real.min() + points.real.max()) / 2, x, 0.01)
          and close((points.imag.min() + points.imag.max()) / 2, y, 0.01))

def span(item, axis="real"):
    values = getattr(np.concatenate(item.paths_mm()), axis)
    return float(values.max() - values.min())


check("an unrotated item is exactly as wide as its box",
      close(span(left), 90.0, 0.01))
# bounds_mm bounds the item's BOX, which a round pattern does not fill into
# the corners -- so it is an envelope, and the drawn extent must stay inside it.
x0, y0, x1, y1 = right.bounds_mm()
drawn = np.concatenate(right.paths_mm())
check("a rotated item stays inside the envelope its box implies",
      x0 <= drawn.real.min() + 1e-9 and drawn.real.max() <= x1 + 1e-9
      and y0 <= drawn.imag.min() + 1e-9 and drawn.imag.max() <= y1 + 1e-9)
right.rotation_deg = 90.0
turned = np.concatenate(right.paths_mm())
right.rotation_deg = 0.0
straight = np.concatenate(right.paths_mm())
check("and a quarter turn really does swap width for height",
      close(float(turned.real.max() - turned.real.min()),
            float(straight.imag.max() - straight.imag.min()), 0.01)
      and close(float(turned.imag.max() - turned.imag.min()),
                float(straight.real.max() - straight.real.min()), 0.01))
right.rotation_deg = 30.0

# -- the canvas paints through the same numbers --------------------------------- #

print("the canvas:")
try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QTransform
    have_qt = True
except ImportError:
    have_qt = False
    print("    (PySide6 not installed; the canvas transform is not cross-checked)")

if have_qt:
    for item in scene.items:
        scale, rotation, tx, ty = item.affine()
        transform = (QTransform().translate(tx, ty).rotate(rotation)
                     .scale(scale, scale))
        # The widget paints unit_paths through exactly this transform, so
        # mapping a unit point must land on the millimetre point.
        sample = item.unit_paths()[0][0]
        mapped = transform.map(complex(sample).real, complex(sample).imag)
        want = item.paths_mm()[0][0]
        check("%s: the canvas transform lands on the same millimetre" % item.name,
              close(mapped[0], want.real, 1e-6) and close(mapped[1], want.imag, 1e-6))

# -- through axiplot, all the way to the driver ------------------------------------ #

print("through axiplot's layer pipeline:")
job = scene.job(opts={"model": 3, "port": ""})
check("two pens make a two-layer colour job",
      job["mode"] == "color" and len(job["pens"]) == 2)

prep = plotmod.prepare_layers(job)
layers = prep["layers"]
check("prepare_layers produces one layer per pen", len(layers) == 2)
check("each layer is sized in the paper's own millimetres",
      all(close(layer["widthMm"], scene.paper.width_mm)
          and close(layer["heightMm"], scene.paper.height_mm) for layer in layers))
check("the optimiser ran", all(layer["optimized"] for layer in layers))

for layer, item in zip(layers, scene.items):
    with open(layer["svgPath"]) as handle:
        final = handle.read()
    bounds = svg_bounds(final)
    points = np.concatenate(item.paths_mm())
    check("%s survives sizing, splitting and optimising, in place" % item.name,
          close(bounds[0], points.real.min()) and close(bounds[2], points.real.max())
          and close(bounds[1], points.imag.min()) and close(bounds[3], points.imag.max()),
          "svg %s vs placed %s" % (
              tuple(round(v, 2) for v in bounds),
              (round(points.real.min(), 2), round(points.imag.min(), 2),
               round(points.real.max(), 2), round(points.imag.max(), 2))))

check("the declared physical size is the paper, so nothing is rescaled again",
      all('width="%gmm"' % scene.paper.width_mm in open(layer["svgPath"]).read()
          for layer in layers))

check("every layer fits inside the machine's travel",
      all(0 <= svg_bounds(open(layer["svgPath"]).read())[0]
          and svg_bounds(open(layer["svgPath"]).read())[2] <= scene.paper.width_mm
          for layer in layers))

# -- the AxiDraw's own opinion --------------------------------------------------- #

print("the AxiDraw, in preview mode (no port opened):")
if not axidriver.available():
    print("    (AxiDraw sources not importable; skipped)")
else:
    machine = axidriver.InProcessDriver()
    opts = dict(prep["opts"], model=3, autoRotate=False)
    results = [machine.preview(layer["svgPath"], opts) for layer in layers]
    check("it motion-plans both layers", all(r["estTimeSec"] > 0 for r in results))
    for layer, result in zip(layers, results):
        # The machine measures pen-down travel itself. It should match the
        # length of the polylines we asked it to draw, to a fraction of a
        # percent -- if the file had been rescaled, it would not.
        drawn_mm = result["drawLenM"] * 1000
        check("%s: the machine's own pen-down travel matches the geometry"
              % layer["label"],
              close(drawn_mm, layer["drawLenMm"], max(2.0, 0.01 * layer["drawLenMm"])),
              "machine %.1f mm vs file %.1f mm" % (drawn_mm, layer["drawLenMm"]))
    check("nothing was reported out of bounds",
          not any("bounds" in (r["raw"] or "").lower() for r in results),
          "; ".join(r["raw"][:120] for r in results))

    # And the converse: a sheet that really is too big must be caught.
    over = Scene(paper=Paper.from_axidraw(3))
    huge = over.add(drawing(), name="huge")
    huge.set_width(900.0)
    check("an item wider than the bed is reported out of bounds",
          [i.item_id for i in over.out_of_bounds()] == [huge.item_id])

# -- the layer bookkeeping ---------------------------------------------------------- #

print("layer state:")
state = axirun.LayerState()
state.sync(axirun.job_stamp(job), 2)
state.mark(0)
check("a finished layer is remembered", state.pending() == [1])
check("the same sheet keeps the marks",
      not state.sync(axirun.job_stamp(job), 2) and state.pending() == [1])
left.move_by(5, 0)
check("a moved item is a different sheet, so the marks are dropped",
      state.sync(axirun.job_stamp(scene.job()), 2) and state.pending() == [0, 1])

print()
print("plot path: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
