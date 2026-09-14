"""INI text in, point arrays out. No files, no server, no Qt.

The generator modules (``main.py`` and the shapes beside it) are untouched;
this is the harness that drives them: read the config, run each layer's
pipeline, apply pen-lift and symmetry, and hand back the curves *in their own
coordinates* along with the box they occupy.

Not normalising here is the point. The old code scaled every result into an
800x800 box on the way out, so the caller could never ask "how wide is this
pattern, really?" — and two callers that each re-fitted the result to their own
box disagreed about where the drawing was. A ``Drawing`` knows its own bounds;
:mod:`spiro.scene` is what decides how many millimetres of paper it covers.
"""

import configparser
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# The generator modules live at the repository root and import each other by
# bare name (`from arc import ...`), so the root has to be importable.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass
class Drawing:
    """One generated pattern: its curves, its extent, and how to ink it.

    ``paths`` are complex arrays in source units — whatever the pipeline
    produced. ``min_x``/``max_x``/``min_y``/``max_y`` bound all of them
    together, which is what preserves the relationship between symmetry copies
    and pen-lift fragments when the whole thing is scaled.
    """

    paths: list = field(default_factory=list)
    min_x: float = 0.0
    max_x: float = 0.0
    min_y: float = 0.0
    max_y: float = 0.0
    style: dict = field(default_factory=dict)
    ini_text: str = ""

    @property
    def width(self):
        w = self.max_x - self.min_x
        return w if w > 0 else 1.0

    @property
    def height(self):
        h = self.max_y - self.min_y
        return h if h > 0 else 1.0

    @property
    def aspect(self):
        return self.width / self.height

    @property
    def center(self):
        return complex((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    @property
    def point_count(self):
        return sum(len(p) for p in self.paths)

    def fitted(self, box_w, box_h, margin=0.0, flip_y=True):
        """The curves scaled to sit inside a ``box_w`` x ``box_h`` box, centred,
        with ``margin`` as a fraction of the box left clear on every side.

        Aspect ratio is preserved: the pattern touches the box on its tight
        axis and is centred on the other. One rule, used everywhere, is the
        whole reason the canvas and the plotter now agree.

        ``flip_y`` mirrors the result about the box's horizontal centre line.
        The generators work in the usual mathematical sense, y upwards; SVG,
        Qt and the plotter bed all count y downwards from the top-left, and
        every current consumer is one of those — so it defaults to on. Turn it
        off to stay in the generator's own frame.
        """
        inner_w = box_w * (1 - 2 * margin)
        inner_h = box_h * (1 - 2 * margin)
        scale = min(inner_w / self.width, inner_h / self.height)
        shift = complex(box_w / 2, box_h / 2) - self.center * scale
        placed = [p * scale + shift for p in self.paths]
        if flip_y:
            placed = [p.real + 1j * (box_h - p.imag) for p in placed]
        return placed


def _style(config):
    def f(key, default):
        return config.getfloat("output", key, fallback=default)
    return {
        "width": f("width", 800.0),
        "height": f("height", 800.0),
        "margin": f("margin", 0.08),
        "stroke_width": f("stroke_width", 0.3),
        "stroke_color": config.get("output", "stroke_color", fallback="#000000"),
        "bg_color": config.get("output", "background_color", fallback="#ffffff"),
        "close_path": config.getboolean("output", "close_path", fallback=False),
    }


def run(ini_text, reload_generators=False):
    """Run a pipeline and return its :class:`Drawing`.

    ``reload_generators`` re-imports ``main`` first, which is how the running
    app picks up an edit to a generator module without a restart.
    """
    import importlib
    if reload_generators and "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    from main import run_single_pipeline, expand_moire_config

    config = configparser.ConfigParser()
    config.read_string(ini_text)
    expand_moire_config(config)

    style = _style(config)

    def s_int(key, default):
        return config.getint("sampling", key, fallback=default)

    initial = s_int("initial_samples", 80000)
    output = s_int("output_samples", 12000)
    arc_len = config.getboolean("sampling", "use_arc_length", fallback=True)
    scroll = config.getfloat("sampling", "scroll_repeats", fallback=1.0)

    start = complex(config.getfloat("output", "start_x", fallback=0.0),
                    config.getfloat("output", "start_y", fallback=0.0))

    paths = []
    layers = [s for s in config.sections() if s.startswith("layer.")]
    if layers:
        for section in layers:
            names = [m.strip() for m in config.get(section, "modules").split(",")]
            paths.append(run_single_pipeline(
                config, names,
                config.getint(section, "initial_samples", fallback=initial),
                config.getint(section, "output_samples", fallback=output),
                config.getboolean(section, "use_arc_length", fallback=arc_len),
                start, label=section.split(".", 1)[1],
                scroll_repeats=config.getfloat(section, "scroll_repeats", fallback=scroll)))
    else:
        names = [m.strip() for m in config.get("pipeline", "modules").split(",")]
        paths.append(run_single_pipeline(config, names, initial, output, arc_len,
                                         start, scroll_repeats=scroll))

    if config.has_section("pen_lift"):
        from pen_lift import apply_pen_lift
        lifted = []
        for pts in paths:
            lifted.extend(apply_pen_lift(pts, config))
        paths = lifted

    n_fold = config.getint("symmetry", "n_fold", fallback=1)
    mirror = config.getboolean("symmetry", "mirror", fallback=False)
    if n_fold > 1 or mirror:
        from symmetry import apply_symmetry
        cx = config.getfloat("symmetry", "center_x", fallback=0.0)
        cy = config.getfloat("symmetry", "center_y", fallback=0.0)
        expanded = []
        for pts in paths:
            expanded.extend(apply_symmetry(pts, n_fold, mirror, cx, cy))
        paths = expanded

    combined = np.concatenate(paths)
    return Drawing(paths=paths,
                   min_x=float(combined.real.min()), max_x=float(combined.real.max()),
                   min_y=float(combined.imag.min()), max_y=float(combined.imag.max()),
                   style=style, ini_text=ini_text)


def normalize(drawing, width=None, height=None, margin=None):
    """The legacy fit: expand the canvas to the pattern's aspect ratio, then
    scale the pattern into it.

    Kept because the SVG export and the web UI still describe a drawing as
    "paths inside a canvas of this size". New code should use
    :meth:`Drawing.fitted`, which fits into a box it is *given* rather than
    inventing one.

    Returns ``(paths, actual_width, actual_height)``.
    """
    width = drawing.style["width"] if width is None else width
    height = drawing.style["height"] if height is None else height
    margin = drawing.style["margin"] if margin is None else margin

    if drawing.aspect > width / height:
        actual_w, actual_h = height * drawing.aspect, height
    else:
        actual_w, actual_h = width, width / drawing.aspect

    return drawing.fitted(actual_w, actual_h, margin), actual_w, actual_h
