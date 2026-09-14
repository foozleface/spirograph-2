"""A pipeline as data, and that data as INI text.

The generator reads INI files and always has; the UI holds a list of steps.
This module is the one place the two meet, so neither the app nor the web
server has to know how a group's branches are spelled.

A *spec* is a plain dict, JSON-round-trippable, which is what makes it a good
document format::

    {"steps":    [ {"kind": "single", "params": {...}},
                   {"kind": "group",  "branches": [[{...}, {...}], [{...}]]} ],
     "output":   {"width": 800, ...},
     "sampling": {"initial_samples": 80000, ...},
     "symmetry": {"n_fold": 6, "mirror": true}}

Steps run in series. A group's branches run *simultaneously* from the origin
and their outputs sum — independent drawing arms on one machine.
"""

from spiro.pipeline.registry import TYPE_TO_MODULE

OUTPUT_DEFAULTS = {
    "width": 800, "height": 800, "stroke_width": 0.3,
    "stroke_color": "#000000", "background_color": "#ffffff",
    "margin": 0.08, "filename": "/dev/null",
}

SAMPLING_DEFAULTS = {
    "initial_samples": 80000, "output_samples": 12000, "use_arc_length": "true",
}

# What a plot is always sampled at, whatever the preview used.
#
# Facet depth on a plotted curve goes as chord^2 / 8R, so a coarse point count
# leaves visible flats wherever the radius of curvature is small — the outer
# lobes of a spirograph. Previewing at Draft is fine; plotting is slow and
# physical, so it always runs at Ultra.
#
# use_arc_length is pinned with it: it is what makes the chord between points
# constant. Without it the point count alone doesn't help, because sampling
# stays uniform in the curve parameter and the lobes — where the pen covers the
# most distance per step — go back to being the coarsest part of the plot.
PLOT_SAMPLING = {
    "initial_samples": 1000000, "output_samples": 100000, "use_arc_length": "true",
}


def _fmt(value):
    """INI spelling of a Python value. configparser reads `true`/`false`, not
    `True`/`False`."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _emit(lines, section, params):
    """One module's section, with the UI's type name mapped to its module."""
    lines.append("[%s]" % section)
    for key, value in params.items():
        if key == "type" and value in TYPE_TO_MODULE:
            lines.append("type = %s" % TYPE_TO_MODULE[value])
        else:
            lines.append("%s = %s" % (key, _fmt(value)))
    lines.append("")


def _emit_steps(lines, steps):
    """Every step's sections, returning the names for the [pipeline] line."""
    names = []
    for index, step in enumerate(steps):
        kind = step.get("kind", "single")
        if kind == "single":
            name = "s%d" % index
            _emit(lines, name, step["params"])
            names.append(name)
            continue

        branches = step.get("branches") or []
        # Legacy shape: a flat list of modules meant one module per branch.
        if not branches and isinstance(step.get("params"), list):
            branches = [[p] for p in step["params"]]

        branch_names = []
        for bi, branch in enumerate(branches):
            chain = []
            for mi, params in enumerate(branch):
                name = "grp%d_b%d_m%d" % (index, bi, mi)
                _emit(lines, name, params)
                chain.append(name)
            branch_names.append(", ".join(chain))

        group = "grp_%d" % index
        lines.append("[%s]" % group)
        lines.append("type = group")
        lines.append("modules = %s" % " | ".join(branch_names))
        lines.append("")
        names.append(group)
    return names


def build_ini(steps=None, output=None, sampling=None, symmetry=None,
              arms=None, global_mods=None, pipeline=None):
    """INI text for a pipeline spec.

    ``steps`` is the current shape. ``arms``/``global_mods``/``pipeline`` are
    the two older ones, kept because saved files and the web UI still send
    them; they are folded into the same output.
    """
    lines = []

    if steps:
        names = _emit_steps(lines, steps)
    elif arms:
        names = []
        if len(arms) > 1:
            for ai, arm in enumerate(arms):
                chain = []
                for mi, params in enumerate(arm):
                    name = "arm%d_mod%d" % (ai, mi)
                    _emit(lines, name, params)
                    chain.append(name)
                group = "arm_%d" % ai
                lines.append("[%s]" % group)
                lines.append("type = group")
                lines.append("modules = %s" % ", ".join(chain))
                lines.append("")
                names.append(group)
        else:
            for mi, params in enumerate(arms[0]):
                name = "mod_%d" % mi
                _emit(lines, name, params)
                names.append(name)
        for mi, params in enumerate(global_mods or []):
            name = "global_%d" % mi
            _emit(lines, name, params)
            names.append(name)
    elif pipeline:
        names = []
        for mi, params in enumerate(pipeline):
            name = "mod_%d" % mi
            _emit(lines, name, params)
            names.append(name)
    else:
        names = []

    head = ["[pipeline]", "modules = %s" % ", ".join(names), ""]

    tail = []
    out = dict(OUTPUT_DEFAULTS, **(output or {}))
    tail.append("[output]")
    tail += ["%s = %s" % (k, _fmt(v)) for k, v in out.items()]
    tail.append("")

    samp = dict(SAMPLING_DEFAULTS, **(sampling or {}))
    tail.append("[sampling]")
    tail += ["%s = %s" % (k, _fmt(v)) for k, v in samp.items()]
    tail.append("")

    if symmetry:
        tail.append("[symmetry]")
        tail += ["%s = %s" % (k, _fmt(v)) for k, v in symmetry.items()]
        tail.append("")

    return "\n".join(head + lines + tail)
