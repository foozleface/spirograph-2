"""Gate for the randomizer: every recipe still draws something.

The recipes are hand-tuned parameter ranges, and a module whose parameters
change out from under one of them fails silently — the button produces a blank
sheet or a traceback instead of a pattern. So the gate is the blunt one: build
each recipe with a fixed seed, run it, and require real curves out.

Sampled coarsely, which is what makes running sixty-one pipelines a test rather
than an errand. Run:  .venv/bin/python tests/test_recipes.py
"""

import contextlib
import io
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spiro.pipeline import recipes, run  # noqa: E402
from spiro.pipeline.document import Document  # noqa: E402
from spiro.pipeline.registry import MODULE_DEFS  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-60s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


COARSE = {"initial_samples": 12000, "output_samples": 600}


def global_state_untouched():
    """Building a pattern must not advance the global RNG — a program that
    seeds `random` for its own reasons should not have that stolen."""
    random.seed(1)
    before = random.random()
    random.seed(1)
    recipes.random_pattern(random.Random(5))
    return random.random() == before


def modules_of(steps):
    for step in steps:
        if step.get("kind") == "group":
            for branch in step.get("branches", []):
                for params in branch:
                    yield params
        else:
            yield step["params"]


# -- the table ---------------------------------------------------------------- #

print("the recipe table:")
check("there are recipes", len(recipes.RECIPES) > 40)
check("every one has a name", all(fn.recipe_name for fn in recipes.RECIPES))
check("the names are distinct", len(set(recipes.names())) == len(recipes.names()))
check("every slug is a usable filename stem",
      all(recipes.slug(n).replace("_", "").isalnum() and recipes.slug(n).isascii()
          for n in recipes.names()))

unknown = set()
for index in range(len(recipes.RECIPES)):
    made = recipes.random_pattern(random.Random(7), index=index)
    unknown |= {p.get("type") for p in modules_of(made["steps"])
                if p.get("type") not in MODULE_DEFS}
check("every module a recipe names exists in the registry", not unknown, unknown)

# -- reproducibility ------------------------------------------------------------ #

print("reproducibility:")
one = recipes.random_pattern(random.Random(99), index=3)
two = recipes.random_pattern(random.Random(99), index=3)
check("the same seed gives the same pattern", one == two)
check("a different seed does not",
      recipes.random_pattern(random.Random(100), index=3) != one)
check("a recipe never touches the global random state", global_state_untouched())

# -- avoiding repeats -------------------------------------------------------------- #

print("not repeating itself:")
avoid = list(range(len(recipes.RECIPES) - 1))
check("with all but one recently used, it picks the one left",
      recipes.random_pattern(random.Random(3), avoid=avoid)["index"]
      == len(recipes.RECIPES) - 1)
check("with everything used it still returns something",
      recipes.random_pattern(random.Random(3),
                             avoid=range(len(recipes.RECIPES)))["index"] is not None)

seen = {recipes.random_pattern(random.Random(seed))["index"] for seed in range(40)}
check("unseeded picks spread over the table", len(seen) > 15, len(seen))

# -- every recipe draws -------------------------------------------------------------- #

print("every recipe draws something:")
broken = []
tiny = []
for index, fn in enumerate(recipes.RECIPES):
    made = recipes.random_pattern(random.Random(1234 + index), index=index)
    document = Document(steps=made["steps"], symmetry=made["symmetry"],
                        output=made["output"], sampling=dict(COARSE))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            drawing = run(document.to_ini())
    except Exception as exc:
        broken.append("%s: %s: %s" % (fn.recipe_name, type(exc).__name__, exc))
        continue
    if drawing.point_count < 100 or drawing.width <= 0 or drawing.height <= 0:
        tiny.append("%s: %d points, %.2f x %.2f"
                    % (fn.recipe_name, drawing.point_count, drawing.width,
                       drawing.height))

check("none of them raise", not broken, "; ".join(broken[:3]))
check("none of them come out empty or degenerate", not tiny, "; ".join(tiny[:3]))
print("    (%d recipes run)" % len(recipes.RECIPES))

# -- what comes back is a document ------------------------------------------------------ #

print("the shape handed to the app:")
made = recipes.random_pattern(random.Random(11))
check("it carries an index, a name, a slug, steps and a stroke width",
      {"index", "name", "slug", "steps", "symmetry", "output"} <= set(made)
      and made["output"].get("stroke_width"))
check("symmetry is either absent or a real fold",
      not made["symmetry"] or made["symmetry"]["n_fold"] > 1)
check("the steps go straight into a Document",
      Document(steps=made["steps"], symmetry=made["symmetry"]).to_ini()
      .startswith("[pipeline]"))

folds = [bool(recipes.random_pattern(random.Random(s))["symmetry"])
         for s in range(60)]
check("some come out symmetric and some do not", any(folds) and not all(folds))

print()
print("recipes: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
