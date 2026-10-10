"""Words on the paper.

A block of text is stored the way a pattern is: as INI text, so a sheet, the
session file, the plot's re-generation and the Open browser all carry it
without knowing it is not a pipeline. :func:`spiro.pipeline.engine.run`
hands an INI with a ``[text]`` section and no ``[pipeline]`` to
:func:`render`, which returns an ordinary :class:`Drawing`.

Two kinds of font:

* **single line** — the Hershey fonts: every letter is strokes, so the pen
  draws each line of a letter once. What a plotter is for.
* **outline** — any font installed on the machine, drawn as its outline: the
  pen goes round each letter. Needs the Qt application to be running.

Size is the height of a capital letter, in millimetres, so ten means a
capital H ten millimetres tall whatever the font. The drawing reports that
height in its own units as ``style["cap_height"]``, which is how the window
turns millimetres into a box size and back.
"""

import configparser
import json

import numpy as np

HERSHEY_PREFIX = "hershey:"
OUTLINE_PREFIX = "outline:"

# The Hershey faces worth offering, in the order they are offered. The
# symbol sets (astrology, music, markers...) are not text.
HERSHEY_FONTS = [
    ("futural", "Sans"),
    ("futuram", "Sans, heavier"),
    ("rowmans", "Roman"),
    ("rowmand", "Roman, double"),
    ("rowmant", "Roman, triple"),
    ("timesr", "Times"),
    ("timesi", "Times italic"),
    ("timesrb", "Times bold"),
    ("timesib", "Times bold italic"),
    ("scripts", "Script"),
    ("scriptc", "Script, heavier"),
    ("cursive", "Cursive"),
    ("gothiceng", "Gothic English"),
    ("gothicger", "Gothic German"),
    ("gothicita", "Gothic Italian"),
    ("greek", "Greek"),
    ("cyrillic", "Cyrillic"),
]
DEFAULT_FONT = HERSHEY_PREFIX + "futural"
ALIGNS = ("left", "center", "right")
LINE_SPACING = 1.7          # baseline to baseline, in capital heights
OUTLINE_PX = 100.0          # outline fonts are laid out at this pixel size

_hershey = {}               # font name -> loaded HersheyFonts


def build_text_ini(text, font=DEFAULT_FONT, align="left", line_spacing=LINE_SPACING):
    """The INI for a block of text."""
    if align not in ALIGNS:
        raise ValueError("align must be one of %s" % ", ".join(ALIGNS))
    config = configparser.ConfigParser(interpolation=None)
    config["text"] = {"text": json.dumps(text), "font": font, "align": align,
                      "line_spacing": "%g" % float(line_spacing)}
    lines = []
    for section in config.sections():
        lines.append("[%s]" % section)
        lines += ["%s = %s" % (k, v) for k, v in config[section].items()]
        lines.append("")
    return "\n".join(lines)


def is_text_ini(ini_text):
    """Is this INI a block of text rather than a pattern?"""
    if not ini_text or "[text]" not in ini_text:
        return False
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read_string(ini_text)
    except configparser.Error:
        return False
    return config.has_section("text") and not config.has_section("pipeline")


def parse(ini_text):
    """``{"text", "font", "align", "line_spacing"}`` from a text INI."""
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(ini_text)
    section = config["text"]
    return {"text": json.loads(section.get("text", '""')),
            "font": section.get("font", DEFAULT_FONT),
            "align": section.get("align", "left"),
            "line_spacing": section.getfloat("line_spacing", LINE_SPACING)}


def font_label(font):
    """What a font is called in the window."""
    if font.startswith(HERSHEY_PREFIX):
        name = font[len(HERSHEY_PREFIX):]
        return dict(HERSHEY_FONTS).get(name, name)
    return font[len(OUTLINE_PREFIX):] if font.startswith(OUTLINE_PREFIX) else font


def missing_letters(text, font):
    """The characters of ``text`` this font cannot draw — the Hershey fonts
    hold printable ASCII only, so a dash or an accent is left out."""
    letters = {c for c in text if c not in "\n\r\t "}
    if font.startswith(OUTLINE_PREFIX):
        from PySide6.QtGui import QFont, QFontMetricsF
        metrics = QFontMetricsF(QFont(font[len(OUTLINE_PREFIX):]))
        return sorted(c for c in letters if not metrics.inFont(c))
    return sorted(c for c in letters if not 32 < ord(c) < 127)


# -- drawing it ---------------------------------------------------------------- #

def render(ini_text):
    """The :class:`Drawing` for a text INI: y up, like every generator."""
    from spiro.pipeline.engine import Drawing
    spec = parse(ini_text)
    lines = spec["text"].split("\n")
    if not spec["text"].strip():
        raise ValueError("there is no text to draw")
    font = spec["font"]
    if font.startswith(OUTLINE_PREFIX):
        laid, cap = _outline_lines(lines, font[len(OUTLINE_PREFIX):])
    else:
        name = font[len(HERSHEY_PREFIX):] if font.startswith(HERSHEY_PREFIX) else font
        laid, cap = _hershey_lines(lines, name)
    paths = _arrange(laid, cap, spec["align"], spec["line_spacing"])
    if not paths:
        raise ValueError("none of these letters are in the font %s" % font_label(font))
    combined = np.concatenate(paths)
    return Drawing(paths=paths,
                   min_x=float(combined.real.min()), max_x=float(combined.real.max()),
                   min_y=float(combined.imag.min()), max_y=float(combined.imag.max()),
                   style={"cap_height": cap, "text": True}, ini_text=ini_text)


def _hershey_lines(lines, name):
    """Each line as ``(strokes, width)``, strokes y-up from the baseline."""
    try:
        from HersheyFonts import HersheyFonts
    except ImportError:                  # pragma: no cover - installed by run_gui.sh
        raise ValueError("single-line fonts need the Hershey-Fonts package "
                         "(pip install Hershey-Fonts)")
    font = _hershey.get(name)
    if font is None:
        if name not in HersheyFonts().default_font_names:
            raise ValueError("no single-line font called %r" % name)
        font = HersheyFonts()
        font.load_default_font(name)
        _hershey[name] = font
    base = font.render_options["base_line"]
    cap = float(base - font.render_options["cap_line"])
    space = cap * 0.5
    laid = []
    for line in lines:
        strokes = []
        for stroke in font.strokes_for_text(line):
            points = np.array([complex(x, base - y) for x, y in stroke])
            if len(points) > 1:
                strokes.append(points)
        if strokes:
            right = max(float(s.real.max()) for s in strokes)
            left = min(float(s.real.min()) for s in strokes)
        else:
            left, right = 0.0, len(line) * space
        laid.append((strokes, left, right))
    return laid, cap


def _outline_lines(lines, family):
    """Each line as ``(outlines, left, right)``, from an installed font."""
    from PySide6.QtGui import QFont, QFontMetricsF, QGuiApplication, QPainterPath
    if QGuiApplication.instance() is None:
        raise ValueError("outline fonts are drawn by the window; open the app")
    qfont = QFont(family)
    qfont.setPixelSize(int(OUTLINE_PX))
    cap = QFontMetricsF(qfont).capHeight() or OUTLINE_PX * 0.7
    laid = []
    for line in lines:
        path = QPainterPath()
        path.addText(0, 0, qfont, line)
        outlines = [np.array([complex(p.x(), -p.y()) for p in polygon])
                    for polygon in path.toSubpathPolygons()]
        outlines = [o for o in outlines if len(o) > 1]
        width = QFontMetricsF(qfont).horizontalAdvance(line)
        if outlines:
            left = min(float(o.real.min()) for o in outlines)
            right = max(float(o.real.max()) for o in outlines)
        else:
            left, right = 0.0, width
        laid.append((outlines, left, right))
    return laid, float(cap)


def _arrange(laid, cap, align, line_spacing):
    """Stack the lines down the page, each aligned within the widest."""
    widest = max((right - left for _, left, right in laid), default=0.0)
    paths = []
    for index, (strokes, left, right) in enumerate(laid):
        width = right - left
        shift = {"left": 0.0, "center": (widest - width) / 2,
                 "right": widest - width}[align] - left
        drop = -index * cap * float(line_spacing)       # in capital heights
        paths += [s + complex(shift, drop) for s in strokes]
    return paths
