#!/usr/bin/env python3
"""Run 2000 novel spirograph pattern experiments against the API."""

import json
import random
import requests
from collections import defaultdict

API_URL = "http://127.0.0.1:8890/api/generate-points"
RESULTS = []
FAILURES = []

random.seed(42)

def make_request(steps, sampling=None, output=None, symmetry=None):
    payload = {
        "steps": steps,
        "sampling": sampling or {"initial_samples": 20000, "output_samples": 3000},
        "output": output or {"stroke_width": 0.12}
    }
    if symmetry:
        payload["symmetry"] = symmetry
    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        if resp.status_code != 200:
            return None, payload, f"HTTP {resp.status_code}"
        data = resp.json()
        paths = data.get("paths", [])
        if not paths or not paths[0]:
            return None, payload, "no paths"
        # Flatten all paths for spread calculation
        all_x, all_y = [], []
        for path in paths:
            for p in path:
                all_x.append(p[0])
                all_y.append(p[1])
        spread = (max(all_x) - min(all_x)) + (max(all_y) - min(all_y))
        return spread, payload, None
    except Exception as e:
        return None, payload, str(e)[:100]

def run_experiment(name, steps, symmetry=None):
    spread, payload, err = make_request(steps, symmetry=symmetry)
    if err:
        FAILURES.append({"name": name, "config": payload, "error": err})
    else:
        RESULTS.append({"name": name, "spread": spread, "config": payload})
    return spread

# --- Step builders ---
# Each module needs {"kind":"single","params":{"type":"<module_name>",...}}
# For groups: {"kind":"group","branches":[[{params1},{params2}],[{params3}]]}

def single(params_dict=None, **kw):
    """Build a single step. Can pass a dict or keyword args."""
    if params_dict is not None:
        return {"kind": "single", "params": params_dict}
    return {"kind": "single", "params": kw}

def group(branches):
    """branches = [[params_dict, params_dict], [params_dict]]"""
    return {"kind": "group", "branches": branches}

# --- Random parameter generators ---

PRIMES = [7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

def rand_guilloche():
    return {"type": "guilloche",
            "inner": random.uniform(20, 150), "outer": random.uniform(80, 350),
            "nodes": random.uniform(20, 250), "div": random.choice(PRIMES),
            "n0": random.uniform(1, 20), "h0": random.uniform(1, 40),
            "n1": random.uniform(1, 20), "h1": random.uniform(1, 40)}

def rand_gear():
    return {"type": "spirograph_gear",
            "fixed_teeth": random.choice([48, 60, 72, 84, 96, 105, 120, 144]),
            "rolling_teeth": random.choice([15, 18, 21, 24, 30, 36, 40, 45, 48]),
            "tooth_pitch": random.uniform(0.5, 3.0),
            "hole_position": random.uniform(0.2, 1.3),
            "inside": random.choice(["true", "false"]),
            "cycles": random.randint(1, 8)}

def rand_harmonograph():
    f1 = random.uniform(1.5, 6.0)
    return {"type": "harmonograph",
            "freq1": round(f1, 2), "freq2": round(f1 * random.uniform(1.2, 2.5), 2),
            "amp1": random.uniform(30, 150), "amp2": random.uniform(30, 150),
            "phase1": random.uniform(0, 360), "phase2": random.uniform(0, 360),
            "decay1": random.uniform(0, 0.05), "decay2": random.uniform(0, 0.05),
            "freq3": round(f1 * random.uniform(0.5, 1.8), 2),
            "amp3": random.uniform(20, 120),
            "phase3": random.uniform(0, 360), "decay3": random.uniform(0, 0.05),
            "duration": random.uniform(30, 120), "cycles": 1}

def rand_lissajous():
    return {"type": "lissajous",
            "freq_x": random.randint(1, 12), "freq_y": random.randint(1, 12),
            "amplitude_x": random.uniform(20, 150), "amplitude_y": random.uniform(20, 150),
            "phase": random.uniform(0, 360), "cycles": random.randint(0, 5)}

def rand_rose():
    return {"type": "rose",
            "k_num": random.randint(1, 12), "k_den": random.randint(1, 8),
            "radius": random.uniform(20, 150), "cycles": 0}

def rand_circle():
    r = random.uniform(20, 150)
    return {"type": "circle", "radius": r, "cycles": random.randint(1, 30)}

def rand_polygon():
    return {"type": "polygon", "sides": random.randint(3, 12),
            "radius": random.uniform(20, 150), "cycles": random.randint(1, 30),
            "rotation": random.uniform(0, 360)}

def rand_star():
    return {"type": "star_shape", "points": random.randint(3, 12),
            "outer_radius": random.uniform(30, 150), "inner_radius": random.uniform(5, 60),
            "cycles": random.randint(1, 20), "rotation": random.uniform(-180, 180)}

def rand_ellipse():
    return {"type": "ellipse", "radius_x": random.uniform(15, 150),
            "radius_y": random.uniform(15, 150), "cycles": random.randint(1, 20),
            "rotation": random.uniform(0, 360)}

def rand_spiral():
    return {"type": "spiral_shape", "start_radius": random.uniform(0, 50),
            "end_radius": random.uniform(30, 150), "turns": random.uniform(1, 15)}

def rand_line():
    return {"type": "line", "length": random.uniform(20, 300),
            "cycles": random.randint(1, 30), "rotation": random.uniform(0, 360)}

def rand_rack():
    return {"type": "rack", "straight_teeth": random.randint(10, 100),
            "end_teeth": random.randint(10, 50), "gear_teeth": random.randint(10, 50),
            "tooth_pitch": random.uniform(0.5, 3.0), "hole_position": random.uniform(0.2, 1.2),
            "laps": random.randint(1, 5), "cycles": random.randint(1, 5)}

def rand_rail():
    return {"type": "spirograph_rail", "rail_length": random.uniform(50, 300),
            "gear_teeth": random.randint(10, 60), "tooth_pitch": random.uniform(0.3, 2.0),
            "hole_position": random.uniform(0.2, 1.2), "passes": random.randint(1, 8)}

def rand_torus():
    return {"type": "torus", "surface": "torus",
            "major_radius": random.uniform(50, 200), "minor_radius": random.uniform(10, 80),
            "v_lines": random.randint(10, 80),
            "view_angle_x": random.uniform(-60, 60), "view_angle_y": random.uniform(-60, 60)}

def rand_figure8():
    return {"type": "figure8", "surface": "figure8",
            "major_radius": random.uniform(50, 200), "minor_radius": random.uniform(10, 80),
            "v_lines": random.randint(10, 80),
            "view_angle_x": random.uniform(-60, 60), "view_angle_y": random.uniform(-60, 60)}

def rand_klein():
    return {"type": "klein_bottle", "surface": "klein",
            "major_radius": random.uniform(50, 200), "minor_radius": random.uniform(10, 80),
            "v_lines": random.randint(10, 80),
            "view_angle_x": random.uniform(-60, 60), "view_angle_y": random.uniform(-60, 60)}

def rand_mobius():
    return {"type": "mobius", "surface": "mobius",
            "major_radius": random.uniform(50, 200), "width": random.uniform(10, 100),
            "v_lines": random.randint(10, 80),
            "view_angle_x": random.uniform(-60, 60), "view_angle_y": random.uniform(-60, 60)}

def rand_ribbon():
    return {"type": "ribbon", "surface": "ribbon",
            "major_radius": random.uniform(50, 200), "width": random.uniform(10, 100),
            "twists": random.uniform(0.5, 6),
            "v_lines": random.randint(10, 80),
            "view_angle_x": random.uniform(-60, 60), "view_angle_y": random.uniform(-60, 60)}

def rand_helix_ribbon():
    return {"type": "helix_ribbon", "surface": "helix_ribbon",
            "major_radius": random.uniform(50, 200), "width": random.uniform(10, 100),
            "twists": random.uniform(0.5, 6),
            "v_lines": random.randint(10, 80),
            "view_angle_x": random.uniform(-60, 60), "view_angle_y": random.uniform(-60, 60)}

def rand_sphere():
    return {"type": "sphere", "surface": "sphere",
            "major_radius": random.uniform(50, 200), "v_lines": random.randint(10, 80)}

ALL_GEN_FUNCS = [rand_guilloche, rand_gear, rand_harmonograph, rand_lissajous, rand_rose,
                 rand_circle, rand_polygon, rand_star, rand_ellipse, rand_spiral, rand_line,
                 rand_rack, rand_rail, rand_torus, rand_figure8, rand_klein, rand_mobius,
                 rand_ribbon, rand_helix_ribbon, rand_sphere]

COMMON_GEN_FUNCS = [rand_guilloche, rand_gear, rand_harmonograph, rand_lissajous, rand_rose,
                    rand_circle, rand_polygon, rand_star, rand_ellipse, rand_spiral]

EXOTIC_GEN_FUNCS = [rand_torus, rand_figure8, rand_klein, rand_mobius, rand_ribbon,
                    rand_helix_ribbon, rand_sphere, rand_rack, rand_rail, rand_line]

def random_gen():
    return random.choice(ALL_GEN_FUNCS)()

# --- Transform param generators ---

def rand_rotation():
    return {"type": "rotation", "total_degrees": random.uniform(90, 2880),
            "origin_x": random.uniform(-50, 50), "origin_y": random.uniform(-50, 50)}

def rand_scale():
    return {"type": "scale", "start_scale": random.uniform(0.3, 3.0),
            "end_scale": random.uniform(0.1, 3.0)}

def rand_stretch():
    p = {"type": "stretch",
         "scale_x": random.uniform(0.2, 5.0), "scale_y": random.uniform(0.2, 5.0)}
    if random.random() > 0.4:
        p["end_scale_x"] = random.uniform(0.2, 5.0)
        p["end_scale_y"] = random.uniform(0.2, 5.0)
    return p

def rand_translation():
    return {"type": "translation",
            "start_x": random.uniform(-100, 100), "end_x": random.uniform(-100, 100),
            "start_y": random.uniform(-100, 100), "end_y": random.uniform(-100, 100)}

def rand_arc():
    return {"type": "arc", "radius": random.uniform(20, 250),
            "sweep_angle": random.uniform(90, 720),
            "start_angle": random.uniform(0, 360),
            "cycles": random.randint(1, 5)}

def rand_spiral_arc():
    ir = random.uniform(10, 100)
    return {"type": "spiral_arc", "inner_radius": ir,
            "outer_radius": ir + random.uniform(30, 200),
            "sweep_angle": random.uniform(360, 2880),
            "start_angle": random.uniform(0, 360)}

def rand_bend():
    return {"type": "bend", "radius": random.uniform(30, 400),
            "sweep_angle": random.uniform(30, 720)}

def rand_damping():
    return {"type": "damping", "decay_rate": random.uniform(0.005, 0.15),
            "duration": random.uniform(10, 150)}

def rand_noise():
    return {"type": "noise", "amplitude": random.uniform(0.5, 30),
            "frequency": random.uniform(5, 300)}

ALL_TX_FUNCS = [rand_rotation, rand_scale, rand_stretch, rand_translation,
                rand_arc, rand_spiral_arc, rand_bend, rand_damping, rand_noise]

def random_tx():
    return random.choice(ALL_TX_FUNCS)()

experiment_num = 0
def next_num():
    global experiment_num
    experiment_num += 1
    return experiment_num

# ============================================================
# Quick validation test
# ============================================================
print("=== Validation test ===")
test_spread, test_payload, test_err = make_request(
    [{"kind": "single", "params": {"type": "spirograph_gear", "fixed_teeth": 96,
     "rolling_teeth": 36, "tooth_pitch": 1.0, "hole_position": 0.7, "inside": "true", "cycles": 3}}])
if test_err:
    print(f"VALIDATION FAILED: {test_err}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    import sys; sys.exit(1)
print(f"Validation OK, spread={test_spread:.2f}")

# ============================================================
# CATEGORY 1: Deep chains (4-5 transforms) — 350 experiments
# ============================================================
print("=== Category 1: Deep chains (4-5 transforms) ===")

for i in range(350):
    gen = random_gen()
    n_tx = random.choice([4, 4, 4, 5, 5])
    txs = [random_tx() for _ in range(n_tx)]
    steps = [single(gen)] + [single(tx) for tx in txs]
    tx_types = [tx["type"] for tx in txs]
    name = f"deep_{next_num()}_{gen['type']}_{'_'.join(tx_types)}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 2: 3-way groups — 250 experiments
# ============================================================
print("=== Category 2: 3-way groups ===")

for i in range(250):
    branches = []
    bnames = []
    for _ in range(3):
        gen = random_gen()
        branch = [gen]
        n_tx = random.choice([0, 0, 1, 1, 2])
        for _ in range(n_tx):
            branch.append(random_tx())
        branches.append(branch)
        bnames.append(gen["type"])

    grp = group(branches)
    post = [single(random_tx()) for _ in range(random.choice([0, 1, 1, 2]))]
    steps = [grp] + post
    name = f"group3_{next_num()}_{'_'.join(bnames)}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 3: Groups with transforms on branches — 200 experiments
# ============================================================
print("=== Category 3: Groups with branch transforms ===")

for i in range(200):
    n_branches = random.choice([2, 2, 3])
    branches = []
    for _ in range(n_branches):
        gen = random_gen()
        branch = [gen]
        for _ in range(random.randint(1, 3)):
            branch.append(random_tx())
        branches.append(branch)

    grp = group(branches)
    steps = [grp]
    name = f"branchtx_{next_num()}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 4: Guilloche combinations — 150 experiments
# ============================================================
print("=== Category 4: Guilloche combos ===")

for i in range(80):
    gp = rand_guilloche()
    if random.random() > 0.5:
        gp["end_inner"] = gp["inner"] + random.uniform(-30, 30)
        gp["end_outer"] = gp["outer"] + random.uniform(-40, 40)
        gp["end_nodes"] = max(10, gp["nodes"] + random.uniform(-30, 30))
    txs = [random_tx() for _ in range(random.randint(2, 4))]
    steps = [single(gp)] + [single(tx) for tx in txs]
    name = f"guilloche_combo_{next_num()}"
    run_experiment(name, steps)

for i in range(70):
    gen2 = random_gen()
    gp = rand_guilloche()
    branches = [[gp], [gen2]]
    if random.random() > 0.5:
        branches.append([random_gen()])
    grp = group(branches)
    post = [single(random_tx()) for _ in range(random.randint(0, 2))]
    steps = [grp] + post
    name = f"guilloche_group_{next_num()}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 5: Stretch variations — 150 experiments
# ============================================================
print("=== Category 5: Stretch variations ===")

for i in range(150):
    gen = random_gen()
    sx, sy = random.uniform(0.2, 5.0), random.uniform(0.2, 5.0)
    stretch = {"type": "stretch", "scale_x": sx, "scale_y": sy}
    if random.random() > 0.3:
        stretch["end_scale_x"] = random.uniform(0.2, 5.0)
        stretch["end_scale_y"] = random.uniform(0.2, 5.0)
    extras = [random_tx() for _ in range(random.randint(1, 3))]
    steps = [single(gen), single(stretch)] + [single(tx) for tx in extras]
    name = f"stretch_{next_num()}_{gen['type']}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 6: Multiple same-type transforms — 150 experiments
# ============================================================
print("=== Category 6: Double/triple same transforms ===")

for i in range(150):
    gen = random_gen()
    tx_fn = random.choice(ALL_TX_FUNCS)
    n_same = random.choice([2, 2, 3])
    txs = [tx_fn() for _ in range(n_same)]
    if random.random() > 0.5:
        other = random.choice([f for f in ALL_TX_FUNCS if f != tx_fn])
        txs.append(other())
    steps = [single(gen)] + [single(tx) for tx in txs]
    name = f"multi_{txs[0]['type']}_{next_num()}_{gen['type']}_{n_same}x"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 7: Unconventional pairings — 150 experiments
# ============================================================
print("=== Category 7: Unconventional pairings ===")

UNCOMMON_PAIRS = [
    (rand_rack, rand_guilloche), (rand_rack, rand_harmonograph), (rand_rack, rand_lissajous),
    (rand_line, rand_harmonograph), (rand_line, rand_guilloche), (rand_line, rand_gear),
    (rand_spiral, rand_guilloche), (rand_spiral, rand_harmonograph),
    (rand_torus, rand_lissajous), (rand_torus, rand_gear), (rand_torus, rand_guilloche),
    (rand_figure8, rand_gear), (rand_figure8, rand_harmonograph),
    (rand_klein, rand_lissajous), (rand_klein, rand_gear),
    (rand_mobius, rand_gear), (rand_mobius, rand_harmonograph),
    (rand_sphere, rand_guilloche), (rand_sphere, rand_gear),
    (rand_ribbon, rand_gear), (rand_helix_ribbon, rand_lissajous),
    (rand_rail, rand_guilloche), (rand_rail, rand_harmonograph),
    (rand_polygon, rand_harmonograph), (rand_star, rand_harmonograph),
]

for fn1, fn2 in UNCOMMON_PAIRS:
    for _ in range(5):
        g1, g2 = fn1(), fn2()
        b1, b2 = [g1], [g2]
        if random.random() > 0.5:
            b1.append(random_tx())
        if random.random() > 0.5:
            b2.append(random_tx())
        grp = group([b1, b2])
        post = [single(random_tx()) for _ in range(random.randint(0, 2))]
        steps = [grp] + post
        name = f"unconventional_{next_num()}_{g1['type']}_{g2['type']}"
        run_experiment(name, steps)

# Fill remaining unconventional
while experiment_num < 1400:
    fn1 = random.choice(EXOTIC_GEN_FUNCS)
    fn2 = random.choice(COMMON_GEN_FUNCS)
    g1, g2 = fn1(), fn2()
    grp = group([[g1], [g2]])
    steps = [grp, single(random_tx())]
    name = f"unconventional_{next_num()}_{g1['type']}_{g2['type']}"
    run_experiment(name, steps)

print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 8: Symmetry experiments — 200 experiments
# ============================================================
print("=== Category 8: Symmetry experiments ===")

for i in range(200):
    gen = random_gen()
    n_fold = random.choice([3, 4, 5, 6, 7, 8, 10, 12])
    txs = [random_tx() for _ in range(random.randint(1, 3))]
    steps = [single(gen)] + [single(tx) for tx in txs]
    symmetry = {"n_fold": n_fold}
    if random.random() > 0.7:
        symmetry["mirror"] = "true"
    name = f"symmetry_{next_num()}_{gen['type']}_fold{n_fold}"
    run_experiment(name, steps, symmetry=symmetry)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 9: High-cycle generators — 100 experiments
# ============================================================
print("=== Category 9: High-cycle generators ===")

for i in range(100):
    cycles = random.randint(10, 50)
    gen_type = random.choice(["polygon", "star_shape", "circle", "ellipse"])
    if gen_type == "polygon":
        gen = {"type": "polygon", "sides": random.randint(3, 8), "radius": random.uniform(20, 100),
               "cycles": cycles, "rotation": random.uniform(0, 360)}
    elif gen_type == "star_shape":
        gen = {"type": "star_shape", "points": random.randint(3, 8),
               "outer_radius": random.uniform(30, 120), "inner_radius": random.uniform(5, 50),
               "cycles": cycles}
    elif gen_type == "circle":
        gen = {"type": "circle", "radius": random.uniform(20, 100),
               "end_radius": random.uniform(10, 120), "cycles": cycles}
    else:
        gen = {"type": "ellipse", "radius_x": random.uniform(15, 100),
               "radius_y": random.uniform(15, 100), "cycles": cycles}

    txs = [random_tx() for _ in range(random.randint(2, 4))]
    steps = [single(gen)] + [single(tx) for tx in txs]
    name = f"highcycle_{next_num()}_{gen_type}_c{cycles}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# CATEGORY 10: Drift-heavy patterns — 100 experiments
# ============================================================
print("=== Category 10: Drift-heavy patterns ===")

for i in range(100):
    gen_type = random.choice(["guilloche", "gear", "harmonograph", "ellipse", "circle", "star_shape"])
    if gen_type == "guilloche":
        gen = rand_guilloche()
        gen["end_inner"] = gen["inner"] + random.uniform(-40, 40)
        gen["end_outer"] = gen["outer"] + random.uniform(-50, 50)
        gen["end_nodes"] = max(10, gen["nodes"] + random.uniform(-50, 50))
    elif gen_type == "gear":
        gen = rand_gear()
        gen["end_hole_position"] = random.uniform(0.1, 1.3)
        gen["end_tooth_pitch"] = random.uniform(0.3, 3.0)
    elif gen_type == "harmonograph":
        gen = rand_harmonograph()
        gen["end_amp1"] = random.uniform(10, 180)
        gen["end_amp2"] = random.uniform(10, 180)
        gen["end_amp3"] = random.uniform(0, 150)
    elif gen_type == "ellipse":
        gen = rand_ellipse()
        gen["end_radius_x"] = random.uniform(10, 180)
        gen["end_radius_y"] = random.uniform(10, 180)
        gen["end_rotation"] = random.uniform(0, 360)
        gen["cycles"] = random.randint(5, 25)
    elif gen_type == "circle":
        gen = {"type": "circle", "radius": random.uniform(20, 120),
               "end_radius": random.uniform(10, 150), "cycles": random.randint(5, 25)}
    else:  # star_shape
        gen = rand_star()
        gen["end_outer_radius"] = random.uniform(20, 180)
        gen["end_inner_radius"] = random.uniform(3, 80)
        gen["end_rotation"] = random.uniform(-180, 180)
        gen["cycles"] = random.randint(5, 20)

    stretch = rand_stretch()
    stretch["end_scale_x"] = random.uniform(0.3, 4.0)
    stretch["end_scale_y"] = random.uniform(0.3, 4.0)
    txs = [stretch] + [random_tx() for _ in range(random.randint(1, 3))]
    steps = [single(gen)] + [single(tx) for tx in txs]
    name = f"drift_{next_num()}_{gen_type}"
    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# Fill remaining to 2000
# ============================================================
print(f"=== Filling remaining ({2000 - experiment_num} left) ===")

while experiment_num < 2000:
    strategy = random.choice(["deep_group", "symmetry_group", "exotic_chain", "surface_combo",
                               "4way_group", "guilloche_deep", "lissajous_deep"])

    if strategy == "deep_group":
        n_branches = random.choice([2, 3])
        branches = []
        for _ in range(n_branches):
            gen = random_gen()
            branch = [gen]
            for _ in range(random.randint(2, 4)):
                branch.append(random_tx())
            branches.append(branch)
        grp = group(branches)
        steps = [grp]
        name = f"deepgroup_{next_num()}"

    elif strategy == "symmetry_group":
        branches = [[random_gen()] for _ in range(random.choice([2, 3]))]
        grp = group(branches)
        steps = [grp, single(random_tx())]
        symmetry = {"n_fold": random.choice([3, 5, 6, 8, 10, 12])}
        run_experiment(f"symgroup_{next_num()}", steps, symmetry=symmetry)
        continue

    elif strategy == "exotic_chain":
        gen = random.choice(EXOTIC_GEN_FUNCS)()
        txs = [random_tx() for _ in range(random.randint(3, 5))]
        steps = [single(gen)] + [single(tx) for tx in txs]
        name = f"exotic_{next_num()}_{gen['type']}"

    elif strategy == "surface_combo":
        s1 = random.choice([rand_torus, rand_figure8, rand_klein, rand_mobius, rand_sphere])()
        s2 = random.choice(COMMON_GEN_FUNCS)()
        grp = group([[s1], [s2]])
        steps = [grp, single(random_tx())]
        name = f"surfcombo_{next_num()}"

    elif strategy == "4way_group":
        branches = [[random_gen()] for _ in range(4)]
        grp = group(branches)
        steps = [grp]
        name = f"group4_{next_num()}"

    elif strategy == "guilloche_deep":
        gen = rand_guilloche()
        gen["end_inner"] = gen["inner"] + random.uniform(-30, 30)
        gen["end_nodes"] = max(10, gen["nodes"] + random.uniform(-40, 40))
        txs = [random_tx() for _ in range(random.randint(3, 5))]
        steps = [single(gen)] + [single(tx) for tx in txs]
        name = f"guill_deep_{next_num()}"

    else:  # lissajous_deep
        gen = rand_lissajous()
        gen["end_amplitude_x"] = random.uniform(10, 180)
        gen["end_amplitude_y"] = random.uniform(10, 180)
        gen["end_phase"] = random.uniform(0, 360)
        txs = [random_tx() for _ in range(random.randint(3, 5))]
        steps = [single(gen)] + [single(tx) for tx in txs]
        name = f"liss_deep_{next_num()}"

    run_experiment(name, steps)
    if experiment_num % 100 == 0:
        print(f"  {experiment_num} done, {len(RESULTS)} ok, {len(FAILURES)} fail")

# ============================================================
# WRITE RESULTS
# ============================================================
print(f"\nDone! {len(RESULTS)} successes, {len(FAILURES)} failures out of {experiment_num}")

RESULTS.sort(key=lambda r: r["spread"], reverse=True)

output_path = "/Users/joe/spirograph-2/experiment_results_2k.md"

with open(output_path, "w") as f:
    f.write("# Experiment Results: 2000 Novel Pattern Experiments\n\n")
    f.write(f"**Total experiments**: {experiment_num}\n")
    f.write(f"**Successful**: {len(RESULTS)}\n")
    f.write(f"**Failed**: {len(FAILURES)}\n")
    if RESULTS:
        f.write(f"**Spread range**: {RESULTS[-1]['spread']:.2f} - {RESULTS[0]['spread']:.2f}\n\n")
    else:
        f.write("**No successful results**\n\n")

    if not RESULTS:
        f.write("## All experiments failed!\n\n")
        for fail in FAILURES[:20]:
            f.write(f"- {fail['name']}: {fail['error']}\n")
            f.write(f"  ```json\n  {json.dumps(fail['config'], indent=2)[:500]}\n  ```\n\n")
    else:
        # Top 50
        f.write("## Top 50 Patterns by Spread Score\n\n")
        for i, r in enumerate(RESULTS[:50]):
            f.write(f"### #{i+1}: {r['name']} (spread: {r['spread']:.2f})\n")
            f.write(f"```json\n{json.dumps(r['config'], indent=2)}\n```\n\n")

        # Best deep chains
        f.write("## Best Deep Chains (4+ transforms)\n\n")
        deep = [r for r in RESULTS if "deep_" in r["name"] or "exotic_" in r["name"] or "guill_deep" in r["name"] or "liss_deep" in r["name"]]
        for i, r in enumerate(deep[:20]):
            f.write(f"### Deep #{i+1}: {r['name']} (spread: {r['spread']:.2f})\n")
            f.write(f"```json\n{json.dumps(r['config'], indent=2)}\n```\n\n")

        # Best groups
        f.write("## Best Group Combinations\n\n")
        groups = [r for r in RESULTS if "group" in r["name"].lower() or "unconventional" in r["name"]
                  or "branchtx" in r["name"] or "surfcombo" in r["name"]]
        for i, r in enumerate(groups[:20]):
            f.write(f"### Group #{i+1}: {r['name']} (spread: {r['spread']:.2f})\n")
            f.write(f"```json\n{json.dumps(r['config'], indent=2)}\n```\n\n")

        # Best symmetry
        f.write("## Best Symmetry Combos\n\n")
        syms = [r for r in RESULTS if "symmetry_" in r["name"] or "symgroup" in r["name"]]
        for i, r in enumerate(syms[:20]):
            f.write(f"### Symmetry #{i+1}: {r['name']} (spread: {r['spread']:.2f})\n")
            f.write(f"```json\n{json.dumps(r['config'], indent=2)}\n```\n\n")

        # Best drift
        f.write("## Best Drift Patterns\n\n")
        drifts = [r for r in RESULTS if "drift_" in r["name"]]
        for i, r in enumerate(drifts[:20]):
            f.write(f"### Drift #{i+1}: {r['name']} (spread: {r['spread']:.2f})\n")
            f.write(f"```json\n{json.dumps(r['config'], indent=2)}\n```\n\n")

        # Worst patterns
        f.write("\n## Lowest Scoring Patterns (to avoid)\n\n")
        for r in RESULTS[-20:]:
            f.write(f"- **{r['name']}**: spread={r['spread']:.2f}\n")

    # Failures
    f.write("\n## Failed Patterns (to avoid)\n\n")
    # Summarize failure types
    err_counts = defaultdict(int)
    for fail in FAILURES:
        err_counts[fail["error"]] += 1
    for err, count in sorted(err_counts.items(), key=lambda x: -x[1]):
        f.write(f"- **{err}**: {count} failures\n")

    f.write(f"\nTotal failures: {len(FAILURES)}\n")

    if FAILURES:
        f.write("\n### Sample failed configs:\n\n")
        for fail in FAILURES[:10]:
            f.write(f"- **{fail['name']}**: {fail['error']}\n")

    # Summary analysis
    if RESULTS:
        f.write("\n## Summary: Generator + Transform Coverage\n\n")

        gen_scores = defaultdict(list)
        for r in RESULTS:
            # Extract generator type from the config
            steps = r["config"].get("steps", [])
            for s in steps:
                if s.get("kind") == "single":
                    t = s.get("params", {}).get("type", "")
                    if t in ["spirograph_gear", "harmonograph", "lissajous", "rose", "circle",
                             "polygon", "star_shape", "ellipse", "spiral_shape", "line", "rack",
                             "spirograph_rail", "guilloche", "torus", "figure8", "klein_bottle",
                             "mobius", "ribbon", "helix_ribbon", "sphere"]:
                        gen_scores[t].append(r["spread"])
                        break
                elif s.get("kind") == "group":
                    # Take first branch first module type
                    branches = s.get("branches", [])
                    if branches and branches[0]:
                        t = branches[0][0].get("type", "")
                        gen_scores[t].append(r["spread"])
                    break

        f.write("### Average spread by generator:\n\n")
        f.write("| Generator | Count | Avg Spread | Max Spread | Min Spread |\n")
        f.write("|-----------|-------|-----------|------------|------------|\n")
        for g in sorted(gen_scores.keys(), key=lambda x: -max(gen_scores[x]) if gen_scores[x] else 0):
            scores = gen_scores[g]
            if scores:
                f.write(f"| {g} | {len(scores)} | {sum(scores)/len(scores):.1f} | {max(scores):.1f} | {min(scores):.1f} |\n")

        # Category breakdown
        f.write("\n### Category performance:\n\n")
        categories = defaultdict(list)
        for r in RESULTS:
            cat = r["name"].split("_")[0]
            categories[cat].append(r["spread"])
        f.write("| Category | Count | Avg Spread | Max Spread |\n")
        f.write("|----------|-------|-----------|------------|\n")
        for cat in sorted(categories.keys(), key=lambda x: -max(categories[x])):
            scores = categories[cat]
            f.write(f"| {cat} | {len(scores)} | {sum(scores)/len(scores):.1f} | {max(scores):.1f} |\n")

print(f"Results written to {output_path}")
