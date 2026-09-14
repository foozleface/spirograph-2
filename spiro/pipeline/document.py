"""A pattern as a document: steps, output, sampling, symmetry — and its file.

``build_ini`` writes; this reads, and holds the thing being edited. Round
tripping matters more than it looks: a person loads a file someone else wrote,
nudges one number and saves it back, and every step, group and drift value they
did not touch has to survive that.
"""

import configparser
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path

from spiro.pipeline.ini import (OUTPUT_DEFAULTS, SAMPLING_DEFAULTS, build_ini)
from spiro.pipeline.registry import MODULE_DEFS, is_arm, modernise

# Which UI type a `surface` section really is — the reverse of the registry's
# TYPE_TO_MODULE, keyed by the module's own `surface` parameter.
_tokens = count(1)

_SURFACE_TO_TYPE = {
    "torus": "torus", "mobius": "mobius", "klein": "klein_bottle",
    "klein_bottle": "klein_bottle", "sphere": "sphere", "figure8": "figure8",
    "ribbon": "ribbon", "helix_ribbon": "helix_ribbon",
}


def _coerce(text):
    """INI values are strings; give back the number or bool one obviously is."""
    lowered = text.strip().lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def _section_params(config, name):
    """One module section as a params dict, including its `type`."""
    params = {}
    if not config.has_section(name):
        return {"type": name}
    for key, value in config.items(name):
        if key == "modules":
            continue
        params[key] = value.strip() if key == "type" else _coerce(value)
    params.setdefault("type", name)
    if params["type"] == "surface":
        params["type"] = _SURFACE_TO_TYPE.get(str(params.get("surface", "")), "torus")
    return modernise(params)


@dataclass
class Document:
    """One pattern being edited."""

    steps: list = field(default_factory=list)
    output: dict = field(default_factory=dict)
    sampling: dict = field(default_factory=dict)
    symmetry: dict = field(default_factory=dict)
    # The sections that are neither modules nor settings: pen_lift, moire.
    extras: dict = field(default_factory=dict)
    path: object = None                 # Path it was loaded from, or None
    name: str = "untitled"
    # Identity, not content: what says "the thing on the paper came from THIS
    # pattern". A name cannot do that job — two patterns can share one.
    token: int = field(default_factory=lambda: next(_tokens))

    # -- reading ------------------------------------------------------------- #

    @classmethod
    def from_ini(cls, text, path=None, name=None):
        config = configparser.ConfigParser()
        config.read_string(text)

        steps = []
        names = [n.strip() for n in
                 config.get("pipeline", "modules", fallback="").split(",")
                 if n.strip()]
        for section in names:
            steps.extend(_flatten(config, section))

        def section(name):
            return ({k: _coerce(v) for k, v in config.items(name)}
                    if config.has_section(name) else {})

        output = section("output")
        output.pop("filename", None)     # never carry someone else's output path
        extras = {name_: section(name_) for name_ in ("pen_lift", "moire")
                  if config.has_section(name_)}
        stem = Path(path).stem if path else "untitled"
        return cls(steps=steps, output=output, sampling=section("sampling"),
                   symmetry=section("symmetry"), extras=extras,
                   path=Path(path) if path else None, name=name or stem)

    @classmethod
    def load(cls, path):
        path = Path(path)
        return cls.from_ini(path.read_text(), path)

    # -- writing ------------------------------------------------------------- #

    def to_ini(self, sampling_override=None):
        sampling = dict(self.sampling)
        if sampling_override:
            sampling.update(sampling_override)
        symmetry = self.symmetry
        if symmetry and int(symmetry.get("n_fold", 1)) <= 1 \
                and not symmetry.get("mirror"):
            symmetry = {}
        # A moire section regenerates its own module list from the pipeline,
        # so a stale one from a loaded file must not survive an edit.
        extras = {name: dict(values) for name, values in self.extras.items() if values}
        if "moire" in extras:
            extras["moire"].pop("modules", None)
        return build_ini(steps=self.steps, output=self.output,
                         sampling=sampling, symmetry=symmetry, extras=extras)

    def save(self, path=None):
        path = Path(path or self.path)
        path.write_text(self.to_ini())
        self.path = path
        self.name = path.stem
        return path

    # -- editing --------------------------------------------------------------- #

    def effect(self, section):
        """The pen_lift or moire settings, creating the dict on first use."""
        return self.extras.setdefault(section, {})

    def drop_effect(self, section):
        self.extras.pop(section, None)

    def single_step_params(self):
        """``(section name, label, param name)`` for every parameter a moire
        pass could vary — the single steps only, because a group's sections are
        named by branch and position and a person should not have to know that.
        """
        from spiro.pipeline.registry import MODULE_DEFS
        out = []
        for index, step in enumerate(self.steps):
            if step.get("kind") == "group":
                continue
            params = step["params"]
            spec = MODULE_DEFS.get(params.get("type"))
            if not spec:
                continue
            for key, meta in spec["params"].items():
                if meta.get("type") in ("int", "float") and "drift_for" not in meta:
                    out.append(("s%d" % index, "%d. %s → %s"
                                % (index + 1, spec["label"],
                                   meta.get("desc") or key), key))
        return out

    def renew(self):
        """This is a different pattern now — open, new, or randomised.

        Anything already on the paper stops tracking it, which is what you
        want: placing, then loading something else, then editing that, must
        not reach back and redraw the first one.
        """
        self.token = next(_tokens)
        return self.token

    def add_module(self, module_type, index=None):
        """Append (or insert) a step holding one module at its defaults."""
        from spiro.pipeline.registry import defaults_for
        step = {"kind": "single", "params": defaults_for(module_type)}
        self.steps.insert(len(self.steps) if index is None else index, step)
        return step

    def remove_step(self, index):
        if 0 <= index < len(self.steps):
            return self.steps.pop(index)
        return None

    def move_step(self, index, delta):
        target = index + delta
        if 0 <= index < len(self.steps) and 0 <= target < len(self.steps):
            self.steps[index], self.steps[target] = self.steps[target], self.steps[index]
            return target
        return index

    def make_group(self, index):
        """Turn a single step into a group of one branch, so a second arm can
        be added beside it."""
        step = self.steps[index]
        if step.get("kind") == "group":
            return step
        self.steps[index] = {"kind": "group", "branches": [[step["params"]]]}
        return self.steps[index]

    def add_branch(self, index, module_type):
        from spiro.pipeline.registry import defaults_for
        step = self.make_group(index)
        step["branches"].append([defaults_for(module_type)])
        return step

    def modules_in(self, index):
        """Every module of a step, as ``(label, params)`` — one for a single
        step, one per module per branch for a group."""
        step = self.steps[index]
        if step.get("kind") != "group":
            return [("", step["params"])]
        out = []
        for bi, branch in enumerate(step.get("branches", [])):
            for mi, params in enumerate(branch):
                out.append(("arm %d.%d" % (bi + 1, mi + 1), params))
        return out

    def describe_step(self, index):
        step = self.steps[index]
        if step.get("kind") != "group":
            return _label(step["params"])
        arms = [" -> ".join(_label(p) for p in branch)
                for branch in step.get("branches", [])]
        return " | ".join(arms) or "empty group"

    # -- defaults ---------------------------------------------------------------- #

    def effective_output(self):
        return dict(OUTPUT_DEFAULTS, **self.output)

    def effective_sampling(self):
        return dict(SAMPLING_DEFAULTS, **self.sampling)

    def is_empty(self):
        return not self.steps


def _label(params):
    spec = MODULE_DEFS.get(params.get("type"))
    return spec["label"] if spec else str(params.get("type", "?"))


def _flatten(config, section):
    """A section as flat steps — a group's branches written out with scopes.

    A group is parentheses: a transform inside a branch acts on that branch's
    arms alone. Written flat, that is the same transform with ``scope`` set
    to the number of arms the branch has added so far — the runner's
    "last k arms" is exactly the branch. So the tree becomes a list, and
    nothing about the drawing changes (the pipeline gate holds the two
    equal). Nested groups flatten the same way, the arm count carrying
    through.

    Returns a list of single steps.
    """
    kind = (config.get(section, "type", fallback=section).strip()
            if config.has_section(section) else section)
    if kind != "group":
        return [{"kind": "single", "params": _section_params(config, section)}]
    out = []
    for branch in config.get(section, "modules", fallback="").split("|"):
        arms = 0
        for name in (n.strip() for n in branch.split(",") if n.strip()):
            inner = _flatten(config, name)
            for step in inner:
                params = step["params"]
                if is_arm(params["type"]):
                    arms += 1
                elif params.get("scope", "all") == "all":
                    params["scope"] = arms
                # a scope the file already set counts arms within its own
                # nested branch, a subset of ours: keep it
            out.extend(inner)
    return out
