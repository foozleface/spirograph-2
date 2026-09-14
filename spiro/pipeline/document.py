"""A pattern as a document: steps, output, sampling, symmetry — and its file.

``build_ini`` writes; this reads, and holds the thing being edited. Round
tripping matters more than it looks: a person loads a file someone else wrote,
nudges one number and saves it back, and every step, group and drift value they
did not touch has to survive that.
"""

import configparser
from dataclasses import dataclass, field
from pathlib import Path

from spiro.pipeline.ini import (OUTPUT_DEFAULTS, SAMPLING_DEFAULTS, build_ini)
from spiro.pipeline.registry import MODULE_DEFS

# Which UI type a `surface` section really is — the reverse of the registry's
# TYPE_TO_MODULE, keyed by the module's own `surface` parameter.
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
    return params


@dataclass
class Document:
    """One pattern being edited."""

    steps: list = field(default_factory=list)
    output: dict = field(default_factory=dict)
    sampling: dict = field(default_factory=dict)
    symmetry: dict = field(default_factory=dict)
    path: object = None                 # Path it was loaded from, or None
    name: str = "untitled"

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
            kind = (config.get(section, "type", fallback=section).strip()
                    if config.has_section(section) else section)
            if kind != "group":
                steps.append({"kind": "single",
                              "params": _section_params(config, section)})
                continue
            branches = []
            for branch in config.get(section, "modules", fallback="").split("|"):
                chain = [_section_params(config, n.strip())
                         for n in branch.split(",") if n.strip()]
                if chain:
                    branches.append(chain)
            steps.append({"kind": "group", "branches": branches})

        def section(name):
            return ({k: _coerce(v) for k, v in config.items(name)}
                    if config.has_section(name) else {})

        output = section("output")
        output.pop("filename", None)     # never carry someone else's output path
        stem = Path(path).stem if path else "untitled"
        return cls(steps=steps, output=output, sampling=section("sampling"),
                   symmetry=section("symmetry"), path=Path(path) if path else None,
                   name=name or stem)

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
        return build_ini(steps=self.steps, output=self.output,
                         sampling=sampling, symmetry=symmetry)

    def save(self, path=None):
        path = Path(path or self.path)
        path.write_text(self.to_ini())
        self.path = path
        self.name = path.stem
        return path

    # -- editing --------------------------------------------------------------- #

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
