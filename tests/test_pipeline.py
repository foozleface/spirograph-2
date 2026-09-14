"""Gate for spiro.pipeline: the module table, the INI writer, the engine.

No hardware, no network, no server. Run:  .venv/bin/python tests/test_pipeline.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from spiro.pipeline import build_ini, defaults_for, module_names, run  # noqa: E402
from spiro.pipeline.document import Document  # noqa: E402
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
check("categories are generator, path, transform or clock",
      {s["category"] for s in MODULE_DEFS.values()} <= {"generator", "path", "transform", "clock"})
check("there are generators, paths and transforms",
      module_names("generator") and module_names("path") and module_names("transform"))
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


def _keys_read_by(module_file, class_name):
    """The config keys a module class reads, from its own source."""
    import re
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), module_file + ".py")).read()
    body = src.split("class " + class_name, 1)[1].split("\nclass ", 1)[0]
    return set(re.findall(r"self\._get(?:float|int|boolean)?\('([a-z0-9_]+)'", body))


from spiro.pipeline.registry import TYPE_TO_MODULE, valid_keys as _valid  # noqa: E402
_gaps = {}
for _type in MODULE_DEFS:
    _file = TYPE_TO_MODULE.get(_type, _type)
    _class = "".join(w.capitalize() for w in _file.split("_")) + "Module"
    if _type == "rail_slide":
        _file, _class = "spirograph_rail", "SpirographRailTransformModule"
    if _type == "oscillating_rotation":
        _file, _class = "rotation", "OscillatingRotationModule"
    _missing = _keys_read_by(_file, _class) - _valid(_type)
    if _missing:
        _gaps[_type] = sorted(_missing)
check("every key a module reads is in the registry", not _gaps, _gaps)

# The runner's idea of an arm and the registry's must agree: an arm pushes
# a base the scope machinery counts, so a generator that forgot to say so
# would make "the last arm" mean the wrong thing.
import configparser as _cp  # noqa: E402
from main import load_module as _load  # noqa: E402
_disagree = []
for _type, _spec in MODULE_DEFS.items():
    _c = _cp.ConfigParser()
    _c.read_string("[m]\ntype = %s\n%s\n" % (
        TYPE_TO_MODULE.get(_type, _type),
        "surface = %s" % _spec["params"]["surface"]["default"] if "surface" in _spec["params"] else ""))
    if _load("m", _c).is_generator != (_spec["category"] in ("generator", "path")):
        _disagree.append(_type)
check("the runner and the registry agree on what an arm is", not _disagree, _disagree)


# -- the INI writer ---------------------------------------------------------- #

print("INI writer:")

SPEC = {
    "steps": [
        {"kind": "single", "params": {"type": "circle", "radius": 1.0, "cycles": 3}},
        {"kind": "group", "branches": [
            [{"type": "rotation", "total_degrees": 90}, {"type": "scale", "end_scale": 2}],
            [{"type": "arc", "radius": 2.5, "normalize": True}]]},
    ],
    "symmetry": {"n_fold": 6, "mirror": True},
}
text = build_ini(**SPEC)

check("the pipeline line names the steps in order",
      "modules = s0, grp_1" in text)
check("a group's branches are separated by a pipe",
      "modules = grp1_b0_m0, grp1_b0_m1 | grp1_b1_m0" in text)
check("booleans are written the way configparser reads them",
      "normalize = true" in text and "mirror = true" in text
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

# Every key a module reads is in the registry, and a key it does not read is
# refused — the modules read their defaults for anything unknown, so a
# misspelling is a drawing that quietly differs from its file.
from spiro.pipeline.registry import valid_keys  # noqa: E402
check("a misspelt parameter is refused, by name",
      raises(ValueError, lambda: build_ini(steps=[{"kind": "single", "params": {
          "type": "arc", "arc_radius": 100}}])))
check("an unknown module type is refused",
      raises(ValueError, lambda: build_ini(steps=[{"kind": "single", "params": {
          "type": "gearbox"}}])))
check("easing and oscillating drift are accepted everywhere they apply",
      {"easing", "osc_radius"} <= valid_keys("circle")
      and "osc_total_degrees" not in valid_keys("rotation"))
check("a renamed key is read the new way",
      Document.from_ini("[pipeline]\nmodules = a\n[a]\ntype = circle\nsweep = 3\n"
                        ).steps[0]["params"].get("lobe") == 3)


# -- the engine -------------------------------------------------------------- #

print("engine:")

# The runner is vectorised: every module sees the whole draw as arrays. A
# module written that way also answers for one moment, which is what the
# scrubber asks. Both must agree.
import configparser  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import load_module  # noqa: E402

STAGED = build_ini(steps=[
    {"kind": "single", "params": {"type": "spirograph_gear", "fixed_teeth": 96,
                                  "rolling_teeth": 36, "hole_position": 0.7}},
    {"kind": "single", "params": {"type": "rotation", "total_degrees": 90}},
    {"kind": "single", "params": {"type": "circle", "radius": 30, "cycles": 5}},
], sampling={"initial_samples": 20000, "output_samples": 3000})
staged = run(STAGED)
check("the drawing carries one stage per module", len(staged.stages) == 3)
check("each stage is sampled at the output points",
      all(len(s) == 3000 for s in staged.stages) and len(staged.t_values) == 3000)
check("the last stage is the drawn curve",
      np.allclose(staged.stages[-1], staged.paths[0]))
check("a rotation keeps each point's distance from the origin",
      np.allclose(np.abs(staged.stages[1]), np.abs(staged.stages[0])))
# cycles 1, a quarter turn, cycles 5: the LCM period is 5 t-cycles.
check("t runs from 0 towards the period, in order", staged.t_values[0] == 0
      and np.all(np.diff(staged.t_values) >= 0) and 4 < staged.t_values[-1] < 5)

def _load_cfg(text):
    cfg = configparser.ConfigParser()
    cfg.read_string(text)
    return cfg


_cfg = _load_cfg(STAGED)
_gear = load_module("s0", _cfg)
_one = _gear.transform(0j, 0.37)
_many = _gear.transform(np.zeros(3, dtype=complex), np.array([0.1, 0.37, 0.9]))
check("a module answers for one moment as it does for the whole draw",
      np.iscomplexobj(_many) and abs(_many[1] - _one) < 1e-12)
check("and a transform on a scalar stays a scalar",
      np.ndim(load_module("s1", _cfg).transform(1 + 0j, 0.5)) == 0)

# -- scope: a transform on the last k arms ------------------------------------- #

print("scope:")
_S = {"initial_samples": 12000, "output_samples": 2000}
_gear = {"type": "spirograph_gear", "fixed_teeth": 96, "rolling_teeth": 36, "hole_position": 0.7}
_circ = {"type": "circle", "radius": 40, "cycles": 7}
_rot = {"type": "rotation", "total_degrees": 90}
_scl = {"type": "scale", "start_scale": 1, "end_scale": 0.3}


def _pts(steps):
    return np.concatenate(run(build_ini(steps=steps, sampling=_S)).paths)


def _single(p, **extra):
    return {"kind": "single", "params": dict(p, **extra)}


def _group(*branches):
    return {"kind": "group", "branches": [list(b) for b in branches]}


_grouped = _pts([_group([_gear, _rot], [_circ, _scl])])
_flat = _pts([_single(_gear), _single(_rot, scope=1), _single(_circ), _single(_scl, scope=1)])
check("a group of two branches is the flat chain with scope on each transform",
      np.allclose(_grouped, _flat))
check("and differs from the chain with no scope",
      not np.allclose(_grouped, _pts([_single(_gear), _single(_rot), _single(_circ), _single(_scl)])))
check("scope = all is the plain chain",
      np.allclose(_pts([_single(_gear), _single(_rot, scope="all")]),
                  _pts([_single(_gear), _single(_rot)])))
check("scope = 0 on a rotation does nothing",
      np.allclose(_pts([_single(_gear), _single(_rot, scope=0)]), _pts([_single(_gear)])))
check("a path in its own branch is the path in the chain — a path is an arm",
      np.allclose(_pts([_single(_gear), _single({"type": "arc", "radius": 100})]),
                  _pts([_group([_gear], [{"type": "arc", "radius": 100}])])))
check("scope = 2 over the only two arms equals scope = all",
      np.allclose(_pts([_single(_gear), _single(_circ), _single(_rot, scope=2)]),
                  _pts([_single(_gear), _single(_circ), _single(_rot)])))
_nested_ini = build_ini(steps=[_single(_circ), _group([_gear, _rot, _circ, _scl], [_circ]),
                               _single(_scl)], sampling=_S)
_doc = Document.from_ini(_nested_ini)
check("a document reads a group as flat steps", all(s["kind"] == "single" for s in _doc.steps))
check("with the scope counting that branch's arms",
      [s["params"].get("scope", "-") for s in _doc.steps] == ["-", "-", 1, "-", 2, "-", "-"],
      [s["params"].get("scope", "-") for s in _doc.steps])
check("and draws exactly what the group drew",
      np.allclose(np.concatenate(run(_doc.to_ini(_S)).paths),
                  np.concatenate(run(_nested_ini).paths)))
check("scope = all is not written to the file",
      "scope = all" not in _doc.to_ini(_S) and "scope = 2" in _doc.to_ini(_S))

# -- clocks ------------------------------------------------------------------- #

print("clocks:")
# Sampled by index, not arc length, so point i is the same moment of the
# draw in every run and a dwell shows as repeated points.
_T = {"initial_samples": 2000, "output_samples": 2000, "use_arc_length": "false"}
_spiral = {"type": "spiral_shape", "start_radius": 5, "end_radius": 80, "turns": 3}


def _tpts(steps):
    return run(build_ini(steps=steps, sampling=_T)).stages[-1]


_plain = _tpts([_single(_spiral)])
_rev = _tpts([_single({"type": "tempo", "mode": "reverse"}), _single(_spiral)])
# Sample i of the reversed draw is the moment 1 - i/N, which is forward
# sample N - i; the very first one is the moment just short of the end.
check("tempo reverse draws the same curve backwards",
      np.allclose(_rev[1:], _plain[:0:-1], atol=1e-6)
      and abs(_rev[0] - _plain[-1]) < 1.0)
_fast = _tpts([_single({"type": "tempo", "mode": "speed", "rate": 3}), _single(_spiral)])
check("tempo speed 3 makes the spiral wind out three times",
      sum(1 for i in range(1, len(_fast)) if np.abs(_fast[i]) < np.abs(_fast[i - 1]) - 20) == 2)
_after = run(build_ini(steps=[_single(_gear), _single({"type": "tempo", "mode": "reverse"}),
                              _single(_circ)], sampling=_T))
check("a clock after an arm leaves that arm on its own time",
      np.allclose(_after.stages[0], run(build_ini(steps=[_single(_gear)], sampling=_T)).stages[0]))
check("and reverses the arm after it",
      np.allclose((_after.stages[2] - _after.stages[0])[1:],
                  _tpts([_single(_circ)])[:0:-1], atol=1e-6))
_stut = _tpts([_single({"type": "tempo", "mode": "stutter", "steps": 4, "dwell": 0.6}), _single(_circ)])
check("tempo stutter stops the pen: many samples sit on four spots",
      len(np.unique(np.round(_stut, 6))) < len(_stut) * 0.5)

# -- the pintograph ----------------------------------------------------------- #

print("pintograph:")
_pin = {"type": "pintograph", "spacing": 200, "radius_1": 60, "radius_2": 45,
        "turns_1": 7, "turns_2": 5, "arm_1": 180, "arm_2": 180}
_d = run(build_ini(steps=[_single(_pin)], sampling=_S))
_t = _d.t_values
_p1 = -100 + 60 * np.exp(1j * (2 * np.pi * 7 * _t))
_p2 = 100 + 45 * np.exp(1j * (np.pi / 2 + 2 * np.pi * 5 * _t))
_pen = _d.stages[0]
check("the pen is one rod's length from each crank pin",
      np.allclose(np.abs(_pen - _p1), 180, atol=1e-6)
      and np.allclose(np.abs(_pen - _p2), 180, atol=1e-6))
check("with the elbow up", np.all(_pen.imag > np.minimum(_p1.imag, _p2.imag) - 1e-9))
check("and it closes: integer turns bring the pen home",
      abs(_pen[0] - load_module("s0", _load_cfg(build_ini(steps=[_single(_pin)])))
          .transform(0j, 1.0)) < 1e-6)

# -- finishing: tile and clip --------------------------------------------------- #

print("finishing:")
_tiled = run(build_ini(steps=[_single(_circ)], sampling=_S,
                       extras={"tile": {"rows": 2, "cols": 3, "dx": 100, "dy": 90, "stagger": True}}))
check("tile makes rows x cols copies", len(_tiled.paths) == 6)
check("stepped by dx and dy", np.allclose(_tiled.paths[1] - _tiled.paths[0], 100)
      and np.allclose(_tiled.paths[3] - _tiled.paths[0], 50 + 90j))
# The default gear is about 14 units across.
_clipped = run(build_ini(steps=[_single(_gear)], sampling=_S,
                         extras={"clip": {"shape": "circle", "radius": 8}}))
check("clip keeps only what is inside, in several strokes",
      len(_clipped.paths) > 1 and all(np.all(np.abs(p) <= 8 + 1e-9) for p in _clipped.paths))
_rect = run(build_ini(steps=[_single(_gear)], sampling=_S,
                      extras={"clip": {"shape": "rect", "width": 10, "height": 500}}))
check("a rectangle clips by width and height",
      len(_rect.paths) > 1 and all(np.all(np.abs(p.real) <= 5 + 1e-9) for p in _rect.paths))
check("clipping everything away is an error, not an empty drawing",
      raises(ValueError, lambda: run(build_ini(steps=[_single(_gear)], sampling=_S,
                                               extras={"clip": {"radius": 0.1}}))))
check("a finishing key nobody reads is refused",
      raises(ValueError, lambda: build_ini(steps=[_single(_gear)],
                                           extras={"tile": {"rowz": 2}})))
_order = run(build_ini(steps=[_single(_circ)], sampling=_S, symmetry={"n_fold": 3},
                       extras={"tile": {"rows": 1, "cols": 2, "dx": 300}}))
check("symmetry runs before tile: each copy of the grid has its fold",
      len(_order.paths) == 6)

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

# -- whole-pattern effects ---------------------------------------------------- #

print("effects:")
from spiro.pipeline.document import Document  # noqa: E402

doc = Document()
doc.add_module("spirograph_gear")
doc.sampling = {"initial_samples": 20000, "output_samples": 1200}

doc.extras["pen_lift"] = {"mode": "periodic", "draw_length": 200,
                          "skip_length": 60}
lifted = run(doc.to_ini())
check("pen lift breaks one curve into several strokes", len(lifted.paths) > 1)
check("and the strokes still share one bounding box",
      close(lifted.width, run(Document.from_ini(
          build_ini(steps=doc.steps, sampling=doc.sampling)).to_ini()).width, 1e-6))

doc.drop_effect("pen_lift")
doc.extras["moire"] = {"copies": 4, "vary_param": "s0.hole_position",
                       "vary_range": 0.05}
moire = run(doc.to_ini())
check("a moire pass runs the pipeline once per copy", len(moire.paths) == 4)
check("the copies differ, which is what makes the interference",
      not np.allclose(moire.paths[0], moire.paths[-1]))
check("moire fills in its own module list from the pipeline",
      "modules = s0" in doc.to_ini().split("[moire]")[1])

reloaded = Document.from_ini(doc.to_ini())
check("effects survive a save and a reload",
      reloaded.extras["moire"]["vary_param"] == "s0.hole_position"
      and reloaded.extras["moire"]["copies"] == 4)
check("a stale module list from a loaded file is not carried forward",
      reloaded.to_ini() == doc.to_ini())

doc.add_module("rotation")
check("only single steps are offered as moire targets",
      all(section.startswith("s") for section, _, _ in doc.single_step_params()))
doc.make_group(1)
check("and a group's modules are not offered at all",
      not any(label.startswith("2.") for _, label, _ in doc.single_step_params()))

print()
print("pipeline: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
