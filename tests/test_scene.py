"""Gate for spiro.scene: paper, placement in millimetres, pens, the SVG.

The point of this file is the round trip. A pattern is placed at a known
position and size in millimetres; the SVG that would go to the plotter is
parsed back; the numbers must agree. That is the property the old code did not
have, and every "it plotted somewhere else" bug lived in the gap.

Run:  .venv/bin/python tests/test_scene.py
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from axiplot import colorsplit, svgutil  # noqa: E402
from spiro.pipeline import build_ini, run  # noqa: E402
from spiro.scene import Paper, PlacedItem, Pen, Scene  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-60s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


def close(a, b, tol=1e-3):
    return abs(a - b) <= tol


def drawing(gear=35, samples=1500, **kw):
    params = {"type": "spirograph_gear", "fixed_teeth": 96,
              "rolling_teeth": gear}
    params.update(kw)
    return run(build_ini(steps=[{"kind": "single", "params": params}],
                         sampling={"initial_samples": samples * 10,
                                   "output_samples": samples}))


_NUM = re.compile(r"-?\d+\.?\d*")


def _extent(paths):
    """(min_x, min_y, max_x, max_y) of a list of complex arrays."""
    c = np.concatenate(paths)
    return (float(c.real.min()), float(c.imag.min()),
            float(c.real.max()), float(c.imag.max()))


def svg_bounds(svg, stroke=None):
    """(min_x, min_y, max_x, max_y) over the SVG's path data, in user units —
    which are millimetres. Read back the same way a reader would."""
    xs, ys = [], []
    for path in colorsplit.parse(svg)["paths"]:
        if stroke is not None and path["stroke"] != stroke:
            continue
        d = re.search(r'\bd="([^"]*)"', path["el"]).group(1)
        nums = [float(n) for n in _NUM.findall(d)]
        xs += nums[0::2]
        ys += nums[1::2]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _matches_axidraw():
    """The ids in AXIDRAW_MODELS are pyaxidraw's options.model, so the travel
    has to be the travel that model really has. Read it from the AxiDraw
    sources rather than trusting the transcription."""
    try:
        from axidrawinternal import axidraw_conf as conf
    except ImportError:
        print("    (axidrawinternal not importable; table not cross-checked)")
        return True
    from spiro.scene.paper import AXIDRAW_MODELS
    names = {1: "default", 2: "V3A3", 3: "V3XLX", 4: "MiniKit", 5: "SEA1",
             6: "SEA2", 7: "V3B6"}
    for model, spec in AXIDRAW_MODELS.items():
        want = (getattr(conf, "x_travel_" + names[model]),
                getattr(conf, "y_travel_" + names[model]))
        if not (close(spec["width_in"], want[0], 0.001)
                and close(spec["height_in"], want[1], 0.001)):
            print("    model %d: have %s, axidraw says %s"
                  % (model, (spec["width_in"], spec["height_in"]), want))
            return False
    return True


# -- paper -------------------------------------------------------------------- #

print("paper:")
a4 = Paper.preset("A4")
check("a preset is portrait unless asked otherwise",
      (a4.width_mm, a4.height_mm) == (210.0, 297.0))
check("landscape swaps the axes",
      Paper.preset("A4", landscape=True).width_mm == 297.0)
check("an AxiDraw model becomes a sheet of its travel",
      close(Paper.from_axidraw(2).width_mm, 16.93 * 25.4, 0.01))
check("the model table matches axidrawinternal's own travel limits",
      _matches_axidraw())
check("the drawable area is the paper less the margin on all four sides",
      Paper(200, 100, margin_mm=10).drawable == (10, 10, 180.0, 80.0))
check("a point inside the margin is inside", Paper(200, 100, 10).contains(15, 15))
check("a point in the margin is not", not Paper(200, 100, 10).contains(5, 50))
check("clamp brings a stray point back to the edge",
      Paper(200, 100, 10).clamp(-50, 500) == (10, 90))

# -- placement ---------------------------------------------------------------- #

print("placement, in millimetres:")
d = drawing()
paper = Paper.from_axidraw(3)          # 594.9 x 217.9 mm, a wide bed
item = PlacedItem(d, x_mm=100, y_mm=50, w_mm=60, h_mm=60 / d.aspect)

x0, y0, x1, y1 = item.bounds_mm()
check("the box is centred on the item's position",
      close(x0, 70) and close(x1, 130) and close((y0 + y1) / 2, 50))

extent = _extent(item.paths_mm())
check("the curves fill exactly that box",
      close(extent[0], 70, 0.01) and close(extent[2], 130, 0.01))
check("and are centred on it vertically too",
      close((extent[1] + extent[3]) / 2, 50, 0.01))

item.move_by(25, -10)
extent = _extent(item.paths_mm())
check("moving by 25mm moves the curves by 25mm",
      close(extent[0], 95, 0.01) and close(extent[2], 155, 0.01))

item.move_to(100, 50)
item.set_width(120)
extent = _extent(item.paths_mm())
check("resizing keeps the centre and doubles the extent",
      close((extent[0] + extent[2]) / 2, 100, 0.01)
      and close(extent[2] - extent[0], 120, 0.01))
check("and the height follows the aspect ratio, not the box",
      close(item.h_mm, 120 / d.aspect, 1e-9)
      and close(extent[3] - extent[1], item.h_mm, 0.01))

check("the width is the height times the drawing's aspect, always",
      close(item.w_mm, item.h_mm * item.aspect, 1e-12))
check("and it is what actually gets drawn",
      close(_extent(item.paths_mm())[2] - _extent(item.paths_mm())[0],
            item.w_mm, 1e-6))
item.set_height(40)
check("setting a height re-derives the width",
      close(item.h_mm, 40) and close(item.w_mm, 40 * item.aspect, 1e-12))
item.scale_by(2)
check("scaling keeps the shape",
      close(item.h_mm, 80) and close(item.w_mm / item.h_mm, item.aspect, 1e-12))
item.set_width(120)

tall = PlacedItem(drawing(gear=37), 0, 0, 10, 10)
tall.fit_into(200, 50)
check("fit_into gives the largest box of the pattern's shape that fits",
      close(tall.h_mm, 50, 1e-9) and tall.w_mm <= 200 + 1e-9
      and close(tall.w_mm / tall.h_mm, tall.aspect, 1e-9))

item.rotation_deg = 90
extent = _extent(item.paths_mm())
check("a quarter turn swaps the extents and keeps the centre",
      close(extent[2] - extent[0], item.h_mm, 0.01)
      and close((extent[0] + extent[2]) / 2, 100, 0.01))
check("bounds_mm covers a rotated item",
      item.bounds_mm()[0] <= extent[0] + 1e-6
      and item.bounds_mm()[2] >= extent[2] - 1e-6)
item.rotation_deg = 0

check("a hit test finds the item under its own centre", item.contains(100, 50))
check("and misses a point outside it", not item.contains(400, 50))
corner = (100 + item.w_mm / 2 - 0.5, 50 + item.h_mm / 2 - 0.5)
check("an unrotated item's corner is inside it", item.contains(*corner))
item.rotation_deg = 45
check("the hit test is done in the item's own frame, so rotation counts",
      item.contains(100, 50) and not item.contains(*corner))
item.rotation_deg = 0

placed = PlacedItem.fitted_to(d, paper, fraction=0.5)
check("a new item lands centred on the paper",
      close(placed.x_mm, paper.width_mm / 2) and close(placed.y_mm, paper.height_mm / 2))
check("at the asked-for fraction of the drawable area",
      close(placed.h_mm, paper.height_mm * 0.5, 0.01))

# -- the scene and its SVG ------------------------------------------------------ #

print("scene:")
scene = Scene(paper=Paper.from_axidraw(3))
first = scene.add(drawing(), name="one")
second = scene.add(drawing(gear=37), name="two")
check("each pattern lands on its own pen", (first.pen, second.pen) == (0, 1))
check("a third would reuse the first, there being two pens",
      scene.add(drawing(gear=31), name="three").pen == 0)
scene.remove(scene.items[-1].item_id)

first.move_to(120, 80)
first.set_width(90)
second.move_to(400, 110)
second.set_width(70)

svg = scene.to_svg()
BED_W, BED_H = 594.87, 217.93
check("the SVG declares its size in millimetres",
      'width="%gmm"' % BED_W in svg and 'height="%gmm"' % BED_H in svg)
check("and one user unit is one millimetre",
      svgutil.get_view_box(svg) == {"x": 0, "y": 0, "w": BED_W, "h": BED_H})

# THE round trip: what is in the SVG is where the item was put.
b = svg_bounds(svg, stroke=scene.pens[0].color)
check("the first pattern is in the SVG exactly where it was placed",
      close(b[0], 120 - 45, 0.01) and close(b[2], 120 + 45, 0.01)
      and close((b[1] + b[3]) / 2, 80, 0.01))
b = svg_bounds(svg, stroke=scene.pens[1].color)
check("and so is the second, on its own pen",
      close(b[0], 400 - 35, 0.01) and close(b[2], 400 + 35, 0.01)
      and close((b[1] + b[3]) / 2, 110, 0.01))

check("every path is stroked with the colour of its pen",
      {p["stroke"] for p in colorsplit.parse(svg)["paths"]}
      == {scene.pens[0].color, scene.pens[1].color})
check("paths close explicitly, which is what colorsplit matches on",
      svg.count("</path>") == len(colorsplit.parse(svg)["paths"]))

check("restricting the SVG to one pen leaves only that pen's paths",
      {p["stroke"] for p in colorsplit.parse(scene.to_svg(pens={1}))["paths"]}
      == {scene.pens[1].color})

# -- pens and the job ------------------------------------------------------------ #

print("pens and the plot job:")
job = scene.job()
check("two pens in use means colour mode", job["mode"] == "color")
check("the job carries the paper size in mm",
      job["paperSize"] == {"width_mm": BED_W, "height_mm": BED_H})
check("the job names each pen in use", [p["label"] for p in job["pens"]]
      == [scene.pens[0].label, scene.pens[1].label])

layers = colorsplit.split_by_groups(job["svg"], [{"colors": [p["color"]],
                                                  "label": p["label"]}
                                                 for p in job["pens"]])
check("axiplot splits the job into one layer per pen", len(layers) == 2)
check("each layer holds only its own pen's paths",
      all(len(colorsplit.parse(l["svg"])["paths"]) == l["count"] for l in layers)
      and sum(l["count"] for l in layers) == len(colorsplit.parse(job["svg"])["paths"]))
check("a layer's geometry is untouched by the split",
      close(svg_bounds(layers[0]["svg"])[0], 120 - 45, 0.01))

second.pen = 0
check("one pen in use means mono mode", scene.job()["mode"] == "mono")
second.pen = 1

scene.pens[1].include = False
check("an excluded pen drops out of the job",
      len(scene.job()["pens"]) == 1 and scene.job()["mode"] == "mono")
scene.pens[1].include = True

check("the summary counts items and points per pen",
      [row["items"] for row in scene.summary()] == [1, 1]
      and scene.summary()[0]["points"] == first.point_count())

# -- bounds, paper changes, and the stamp ------------------------------------------ #

print("bounds, paper and the stamp:")
check("nothing is out of bounds to begin with", scene.out_of_bounds() == [])
second.move_to(scene.paper.width_mm - 5, 110)
check("an item hanging off the edge is reported",
      [i.item_id for i in scene.out_of_bounds()] == [second.item_id])
second.move_to(400, 110)

check("an item well inside the paper is in bounds with no margin",
      Scene(Paper(BED_W, BED_H), scene.pens, [first]).out_of_bounds() == [])
check("and out of bounds once the margin reaches it",
      Scene(Paper(BED_W, BED_H, margin_mm=60), scene.pens,
            [first]).out_of_bounds() == [first])
scene.paper = Paper.from_axidraw(3)

before = (first.x_mm / scene.paper.width_mm, first.w_mm / scene.paper.width_mm)
scene.set_paper(Paper.preset("A2", landscape=True))
after = (first.x_mm / scene.paper.width_mm, first.w_mm / scene.paper.width_mm)
check("changing paper keeps an item's position relative to the sheet",
      close(before[0], after[0], 1e-9))
check("and shrinks it by the tighter of the two axes, so it still fits",
      after[1] <= before[1] + 1e-9)

scene.set_paper(Paper.from_axidraw(3), rescale=False)
first.move_to(120, 80)
first.set_width(90)

stamp = scene.stamp()
check("the stamp is stable when nothing changes", scene.stamp() == stamp)
first.move_by(1, 0)
check("moving an item changes it", scene.stamp() != stamp)
first.move_by(-1, 0)
check("and putting it back restores it", scene.stamp() == stamp)
scene.pens[0] = Pen("#123456", "Ink")
check("changing a pen changes it too", scene.stamp() != stamp)

# -- the sheet file ------------------------------------------------------------------ #

print("the sheet file:")
import json  # noqa: E402
import tempfile  # noqa: E402

from spiro.scene import item_inis  # noqa: E402

first.move_to(120, 80)
first.set_width(90)
first.rotate_to(30)
second.move_to(400, 110)
second.set_width(120)
second.rotate_to(-15)
check("rotation is kept in [0, 360)", close(second.rotation_deg, 345.0, 1e-9))
scene.pens[1].label = "Fine red"

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "gate.sheet.json")
    scene.save(path, extra={"paper_setup": {"model": 3, "preset": None,
                                            "margin_mm": 0}})
    raw = json.load(open(path))
    check("it is JSON with a format tag", raw.get("format") == "spirograph-sheet")
    check("and the caller's extra keys", raw.get("paper_setup", {}).get("model") == 3)
    check("every item carries the INI that made it",
          all(entry["ini"].strip() for entry in raw["items"]))
    check("but not its points", os.path.getsize(path) < 20000, os.path.getsize(path))

    data = Scene.read(path)
    drawings = [run(text) for text in item_inis(data)]
    again = Scene.from_dict(data, drawings)
    check("it reads back with the same paper",
          again.paper == scene.paper)
    check("the same pens",
          [p.to_dict() for p in again.pens] == [p.to_dict() for p in scene.pens])
    check("and the same items, in order",
          [i.name for i in again.items] == [i.name for i in scene.items])
    for one, two in zip(scene.items, again.items):
        check("%s: position, width, angle and pen survive" % one.name,
              close(one.x_mm, two.x_mm, 1e-9) and close(one.y_mm, two.y_mm, 1e-9)
              and close(one.w_mm, two.w_mm, 1e-3)
              and close(one.rotation_deg, two.rotation_deg, 1e-9)
              and one.pen == two.pen and one.visible == two.visible)
    check("a reopened item does not claim a session token it never had",
          all(i.source is None for i in again.items))
    check("the geometry that reaches the plotter is the same geometry",
          all(close(a, b, 1e-3) for a, b in
              zip(svg_bounds(scene.to_svg()), svg_bounds(again.to_svg()))),
          (svg_bounds(scene.to_svg()), svg_bounds(again.to_svg())))
    check("the stamp agrees too — same sheet, as far as the plotter knows",
          again.stamp() == scene.stamp())

    # In place, because the canvas and the panels hold one scene.
    live = Scene()
    same = live.apply_dict(data, drawings)
    check("apply_dict fills the scene it is called on", same is live and len(live.items) == 2)

    other = os.path.join(folder, "notes.json")
    with open(other, "w") as handle:
        json.dump({"hello": "world"}, handle)
    try:
        Scene.read(other)
        check("a JSON file that is not a sheet is refused", False)
    except ValueError:
        check("a JSON file that is not a sheet is refused", True)
    try:
        Scene.from_dict(data, drawings[:1])
        check("the wrong number of drawings is refused", False)
    except ValueError:
        check("the wrong number of drawings is refused", True)

first.rotate_to(0)
second.rotate_to(0)

print()
print("scene: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
