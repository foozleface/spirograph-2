"""Golden gate: the engine draws today what it drew yesterday.

Every module at its defaults, every module with every drift engaged, every
``.ini`` in the repository, thirty seeded recipes, the group cases, and each
finishing pass — rendered at a small fixed sampling and reduced to a
fingerprint: bounds, path length, point count, and sixty-four points spread
along the result. The fingerprints live in ``tests/golden/`` and this gate
fails when one moves by more than a millionth of the drawing's extent.

The point is to rewrite the engine freely. A change that is *meant* to alter
a drawing re-records with ``--record`` in a commit that says why; a change
that alters one by accident is caught here.

Run:  .venv/bin/python tests/test_golden.py            check
      .venv/bin/python tests/test_golden.py --record   re-record everything
      .venv/bin/python tests/test_golden.py --record --only recipes
"""

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from spiro.pipeline import build_ini, defaults_for, run  # noqa: E402
from spiro.pipeline import recipes  # noqa: E402
from spiro.pipeline.document import Document  # noqa: E402
from spiro.pipeline.registry import MODULE_DEFS  # noqa: E402

GOLDEN = ROOT / "tests" / "golden"
SAMPLING = {"initial_samples": 12000, "output_samples": 2000}
POINTS = 64
TOLERANCE = 1e-6          # of the drawing's extent

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    if not cond:
        print("  %-60s FAIL %s" % (name, detail))


# -- fingerprints -------------------------------------------------------------- #

def fingerprint(drawing):
    combined = np.concatenate(drawing.paths)
    step = max(len(combined) // POINTS, 1)
    sample = combined[::step][:POINTS]
    length = float(sum(np.abs(np.diff(p)).sum() for p in drawing.paths if len(p) > 1))
    return {
        "paths": len(drawing.paths),
        "points": int(sum(len(p) for p in drawing.paths)),
        "bounds": [drawing.min_x, drawing.min_y, drawing.max_x, drawing.max_y],
        "length": length,
        "sample": [[float(p.real), float(p.imag)] for p in sample],
    }


def compare(name, want, got):
    extent = max(want["bounds"][2] - want["bounds"][0],
                 want["bounds"][3] - want["bounds"][1], 1e-9)
    tol = TOLERANCE * extent
    if want["paths"] != got["paths"] or want["points"] != got["points"]:
        return "paths/points %d/%d -> %d/%d" % (want["paths"], want["points"],
                                                 got["paths"], got["points"])
    worst = max(abs(a - b) for a, b in zip(want["bounds"], got["bounds"]))
    if worst > tol:
        return "bounds moved by %.3g" % worst
    if abs(want["length"] - got["length"]) > tol * 50:
        return "length %.6f -> %.6f" % (want["length"], got["length"])
    a = np.array(want["sample"])
    b = np.array(got["sample"])
    if a.shape != b.shape:
        return "sample shape %s -> %s" % (a.shape, b.shape)
    worst = float(np.abs(a - b).max()) if len(a) else 0.0
    if worst > tol:
        return "a point moved by %.3g (tolerance %.3g)" % (worst, tol)
    return None


# -- the cases ------------------------------------------------------------------- #

def single(module_type, **params):
    return {"kind": "single", "params": dict(params, type=module_type)}


def group(*branches):
    return {"kind": "group", "branches": [list(b) for b in branches]}


def _ini(steps, **kw):
    kw.setdefault("sampling", SAMPLING)
    return build_ini(steps=steps, **kw)


def module_cases():
    """Every module at its defaults, and again with every drift engaged."""
    out = {}
    for name, spec in sorted(MODULE_DEFS.items()):
        params = defaults_for(name)
        chain = [single(name, **{k: v for k, v in params.items() if k != "type"})]
        if spec["category"] != "generator":
            # A transform on its own moves nothing, and a path on its own is
            # only its path; give both an arm to carry.
            chain = [single("circle", radius=40, cycles=3)] + chain
        out["module/%s" % name] = _ini(chain)

        drifted = dict(params)
        touched = False
        for key, p in spec["params"].items():
            if "drift_for" in p:
                base = drifted[p["drift_for"]]
                drifted[key] = base * 1.7 + 3 if isinstance(base, (int, float)) else base
                touched = True
        if touched:
            chain2 = [single(name, **{k: v for k, v in drifted.items() if k != "type"})]
            if spec["category"] != "generator":
                chain2 = [single("circle", radius=40, cycles=3)] + chain2
            out["drift/%s" % name] = _ini(chain2)
    return out


def composition_cases():
    gear = dict(type="spirograph_gear", fixed_teeth=96, rolling_teeth=36, hole_position=0.7)
    circ = dict(type="circle", radius=40, cycles=7)
    rot = dict(type="rotation", total_degrees=90)
    scl = dict(type="scale", start_scale=1, end_scale=0.3)
    s = lambda p: {"kind": "single", "params": p}  # noqa: E731
    return {
        "compose/chain-two-generators": _ini([s(gear), s(circ)]),
        "compose/group-two-generators": _ini([group([gear], [circ])]),
        "compose/chain-gen-rot-gen": _ini([s(gear), s(rot), s(circ)]),
        "compose/group-gen-rot|gen": _ini([group([gear, rot], [circ])]),
        "compose/chain-gen-rot-gen-scale": _ini([s(gear), s(rot), s(circ), s(scl)]),
        "compose/group-gen-rot|gen-scale": _ini([group([gear, rot], [circ, scl])]),
        "compose/nested-group-in-chain": _ini([s(circ), group([gear, rot], [circ]), s(scl)]),
        "compose/rotation-720-vs-period": _ini([s(dict(type="circle", radius=40, cycles=3)),
                                                s(dict(type="rotation", total_degrees=720))]),
        "compose/scroll-repeats": _ini([s(gear), s(rot)],
                                       sampling=dict(SAMPLING, scroll_repeats=2.5)),
        "compose/easing-and-osc": _ini([s(dict(type="circle", radius=20, end_radius=60,
                                               cycles=9, easing="sine", osc_radius="3,0.3")),
                                        s(dict(type="rotation", total_degrees=180,
                                               easing="ease_in_out"))]),
        "compose/normalize-off": _ini([s(dict(type="circle", radius=40, cycles=3)),
                                       s(dict(type="rotation", total_degrees=360,
                                              normalize=False))]),
        "finish/symmetry-6-mirror": _ini([s(gear)], symmetry={"n_fold": 6, "mirror": True}),
        "finish/pen-lift-periodic": _ini([s(gear)], extras={"pen_lift": {
            "mode": "periodic", "draw_length": 120, "skip_length": 40}}),
        "finish/pen-lift-threshold": _ini([s(dict(type="line", length=100, cycles=12,
                                                  stroke_time=0.1)), s(rot)],
                                          extras={"pen_lift": {"mode": "threshold",
                                                               "threshold": 5}}),
        "finish/pen-lift-angular": _ini([s(gear)], extras={"pen_lift": {
            "mode": "angular", "angle_draw": 30, "angle_skip": 10}}),
        "finish/moire": _ini([s(gear)], extras={"moire": {
            "copies": 3, "vary_param": "s0.hole_position", "vary_range": 0.05}}),
    }


def file_cases():
    """Every pattern file in the repository, at the gate's sampling."""
    out = {}
    skip = {".venv", "venv", ".git", "__pycache__", "node_modules", "output",
            "test-results", "docs", "tests"}
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in skip and not d.startswith("."))
        for name in sorted(names):
            if not name.endswith(".ini") or name.startswith("_"):
                continue
            path = Path(folder) / name
            try:
                text = Document.load(path).to_ini(SAMPLING)
            except Exception as exc:
                text = None
                print("  (skipping %s: %s)" % (path.relative_to(ROOT), exc))
            if text:
                out["file/%s" % path.relative_to(ROOT)] = text
    return out


def recipe_cases(count=30):
    out = {}
    for seed in range(count):
        made = recipes.random_pattern(rng=random.Random(seed))
        out["recipe/%02d-%s" % (seed, made["slug"])] = build_ini(
            steps=made["steps"], symmetry=made["symmetry"], sampling=SAMPLING)
    return out


def all_cases(only=None):
    groups = {"modules": module_cases, "compose": composition_cases,
              "files": file_cases, "recipes": recipe_cases}
    cases = {}
    for key, fn in groups.items():
        if only and key not in only:
            continue
        cases.update(fn())
    return cases


def _file_for(name):
    return GOLDEN / (name.replace("/", "__") + ".json")


# -- record / check ---------------------------------------------------------------- #

def render(text):
    return run(text)


def record(only=None):
    GOLDEN.mkdir(exist_ok=True)
    cases = all_cases(only)
    for name, text in sorted(cases.items()):
        drawing = render(text)
        _file_for(name).write_text(json.dumps(
            {"name": name, "ini": text, "fingerprint": fingerprint(drawing)},
            indent=1))
    print("recorded %d fingerprints into %s" % (len(cases), GOLDEN.relative_to(ROOT)))


def gate(only=None):
    cases = all_cases(only)
    for name, text in sorted(cases.items()):
        path = _file_for(name)
        if not path.exists():
            check(name, False, "no golden recorded — run with --record")
            continue
        want = json.loads(path.read_text())
        try:
            got = fingerprint(render(text))
        except Exception as exc:
            check(name, False, "raised %s: %s" % (type(exc).__name__, exc))
            continue
        problem = compare(name, want["fingerprint"], got)
        check(name, problem is None, problem or "")
    recorded = {p.stem for p in GOLDEN.glob("*.json")}
    expected = {name.replace("/", "__") for name in cases}
    stale = sorted(recorded - expected)
    check("no golden is left without a case", not stale, stale[:5])
    print()
    print("golden: %d passed, %d failed" % (len(PASS), len(FAIL)))
    if FAIL:
        for name in FAIL:
            print("  FAILED: %s" % name)
    return not FAIL


if __name__ == "__main__":
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    if "--record" in args:
        record(only)
        sys.exit(0)
    sys.exit(0 if gate(only) else 1)
