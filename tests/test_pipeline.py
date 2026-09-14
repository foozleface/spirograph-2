"""Gate for spiro.pipeline: the module table, the INI writer, the engine.

No hardware, no network, no server. Run:  .venv/bin/python tests/test_pipeline.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from spiro.pipeline import build_ini, defaults_for, module_names, run  # noqa: E402
from spiro.pipeline.engine import normalize  # noqa: E402
from spiro.pipeline.registry import MODULE_DEFS  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-58s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


def parses(text):
    import configparser
    config = configparser.ConfigParser()
    config.read_string(text)
    return config.get("pipeline", "modules") != ""


# -- the module table -------------------------------------------------------- #

print("module table:")
check("every module declares a category, label and params",
      all({"category", "label", "params"} <= set(spec)
          for spec in MODULE_DEFS.values()))
check("categories are only generator or transform",
      {s["category"] for s in MODULE_DEFS.values()} <= {"generator", "transform"})
check("there are generators and transforms",
      module_names("generator") and module_names("transform"))
check("every parameter has a type and a default",
      all("type" in p and "default" in p
          for spec in MODULE_DEFS.values() for p in spec["params"].values()))
check("every drift parameter points at a real parameter",
      all(p["drift_for"] in spec["params"]
          for spec in MODULE_DEFS.values() for p in spec["params"].values()
          if "drift_for" in p))
check("defaults_for carries the type and every default",
      defaults_for("circle")["type"] == "circle"
      and set(defaults_for("circle")) == {"type"} | set(MODULE_DEFS["circle"]["params"]))
check("defaults_for rejects an unknown module",
      raises(KeyError, lambda: defaults_for("nope")))


# -- the INI writer ---------------------------------------------------------- #

print("INI writer:")

SPEC = {
    "steps": [
        {"kind": "single", "params": {"type": "circle", "radius": 1.0, "closed": True}},
        {"kind": "group", "branches": [
            [{"type": "rotation", "total_degrees": 90}, {"type": "scale", "factor": 2}],
            [{"type": "arc", "arc_radius": 2.5}]]},
    ],
    "symmetry": {"n_fold": 6, "mirror": True},
}
text = build_ini(**SPEC)

check("the pipeline line names the steps in order",
      "modules = s0, grp_1" in text)
check("a group's branches are separated by a pipe",
      "modules = grp1_b0_m0, grp1_b0_m1 | grp1_b1_m0" in text)
check("booleans are written the way configparser reads them",
      "closed = true" in text and "mirror = true" in text
      and "True" not in text)
check("a UI type name is mapped to its implementation module",
      "type = surface" in build_ini(steps=[{"kind": "single",
                                            "params": {"type": "klein_bottle"}}]))
check("output and sampling always have defaults",
      "[output]" in text and "width = 800" in text
      and "[sampling]" in text and "initial_samples = 80000" in text)
check("given values override the defaults",
      "width = 210" in build_ini(steps=SPEC["steps"], output={"width": 210}))
check("no symmetry section when there is no symmetry",
      "[symmetry]" not in build_ini(steps=SPEC["steps"]))
check("a legacy flat group becomes one branch per module",
      "modules = grp0_b0_m0 | grp0_b1_m0" in build_ini(
          steps=[{"kind": "group", "params": [{"type": "circle"}, {"type": "ellipse"}]}]))
check("legacy arms and globals still write a pipeline",
      "modules = mod_0, global_0" in build_ini(
          arms=[[{"type": "circle"}]], global_mods=[{"type": "noise"}]))
check("two legacy arms become two groups",
      "modules = arm_0, arm_1" in build_ini(
          arms=[[{"type": "circle"}], [{"type": "ellipse"}]]))
check("the INI is parseable", parses(text))


# -- the engine -------------------------------------------------------------- #

print("engine:")

GEAR = build_ini(steps=[{"kind": "single", "params": {
    "type": "spirograph_gear", "fixed_teeth": 96, "rolling_teeth": 36,
    "hole_position": 0.6}}],
    sampling={"initial_samples": 20000, "output_samples": 4000})

d = run(GEAR)
check("a run produces points", d.point_count == 4000)
check("bounds enclose every point",
      all(d.min_x <= p.real.min() and p.real.max() <= d.max_x
          and d.min_y <= p.imag.min() and p.imag.max() <= d.max_y for p in d.paths))
check("width, height and aspect follow from the bounds",
      close(d.width, d.max_x - d.min_x) and close(d.height, d.max_y - d.min_y)
      and close(d.aspect, d.width / d.height))
check("the drawing keeps the INI it came from", d.ini_text == GEAR)
check("style comes from the output section",
      d.style["width"] == 800 and d.style["stroke_color"] == "#000000")


def extent(paths):
    c = np.concatenate(paths)
    return (float(c.real.min()), float(c.real.max()),
            float(c.imag.min()), float(c.imag.max()))


# A gear this symmetric is square, so it fits a wide box on height and is
# centred across the width -- the property that used to be got wrong.
x0, x1, y0, y1 = extent(d.fitted(200, 100))
check("a square pattern fits a wide box on its height",
      close(y0, 0, 1e-3) and close(y1, 100, 1e-3))
check("and is centred across the width",
      close((x0 + x1) / 2, 100, 1e-3) and close(x1 - x0, 100, 1e-3))

x0, x1, y0, y1 = extent(d.fitted(100, 200))
check("a tall box is filled on the width instead",
      close(x0, 0, 1e-3) and close(x1, 100, 1e-3) and close((y0 + y1) / 2, 100, 1e-3))

x0, x1, y0, y1 = extent(d.fitted(100, 100, margin=0.1))
check("a margin is a fraction of the box left clear on every side",
      close(x0, 10, 1e-3) and close(x1, 90, 1e-3)
      and close(y0, 10, 1e-3) and close(y1, 90, 1e-3))

up = extent(d.fitted(100, 100, flip_y=False))
down = extent(d.fitted(100, 100, flip_y=True))
check("flip_y mirrors about the box's centre line, and only that",
      close(up[0], down[0]) and close(up[1], down[1])
      and close(up[2], 100 - down[3]) and close(up[3], 100 - down[2]))

check("fitting is idempotent in scale -- the same box gives the same result",
      extent(d.fitted(100, 100)) == extent(d.fitted(100, 100)))

# The legacy fit expands the canvas to the pattern's aspect ratio.
paths, w, h = normalize(d, 800, 400)
check("normalize grows a canvas to the pattern's aspect ratio",
      close(w / h, d.aspect, 1e-9) and close(w, 800))
check("normalize keeps the declared margin",
      close(extent(paths)[0], 800 * 0.08, 1e-3))

# Symmetry and pen-lift arrive as extra paths sharing one bounding box.
sym = run(build_ini(steps=[{"kind": "single", "params": {
    "type": "spirograph_gear", "fixed_teeth": 96, "rolling_teeth": 35}}],
    sampling={"initial_samples": 20000, "output_samples": 2000},
    symmetry={"n_fold": 6, "mirror": False}))
check("symmetry expands one curve into n copies", len(sym.paths) == 6)
sx0, sx1, sy0, sy1 = extent(sym.paths)
check("the bounds cover every copy, not just the first",
      close(sx0, sym.min_x) and close(sx1, sym.max_x)
      and close(sy0, sym.min_y) and close(sy1, sym.max_y))

print()
print("pipeline: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
