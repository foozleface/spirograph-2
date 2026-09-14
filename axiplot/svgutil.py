"""``app/svgutil.js`` -- pure-string SVG root-tag helpers.

The AxiDraw binary reads physical size from the root width/height, so before
plotting the root is restated in millimetres while the coordinate viewBox
stays unchanged. Numbers are formatted the way JS template interpolation
formats them (``js_str``), and rounding is ``Math.round`` (``js_round``).
"""

import math
import re

from axiplot._jsnum import js_round, js_str

MM_PER_IN = 25.4

_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.I)
_ATTR_RE = re.compile(r"([a-zA-Z_:][-\w:.]*)\s*=\s*\"([^\"]*)\"")


def parse_root(svg):
    m = _ROOT_RE.search(svg)
    if not m:
        raise ValueError("no <svg> root element found")
    tag = m.group(0)
    attrs = {a.group(1): a.group(2) for a in _ATTR_RE.finditer(tag)}
    return {"tag": tag, "attrs": attrs, "index": m.start(), "length": len(tag)}


def _parse_float(s):
    """JS ``parseFloat`` -- leading-prefix parse, NaN on failure."""
    m = re.match(r"\s*[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?", str(s or ""), re.I)
    return float(m.group(0)) if m else float("nan")


def get_view_box(svg):
    attrs = parse_root(svg)["attrs"]
    if "viewBox" in attrs:
        parts = re.split(r"[\s,]+", attrs["viewBox"].strip())
        if len(parts) == 4:
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                nums = None
            if nums is not None and all(math.isfinite(n) for n in nums):
                return {"x": nums[0], "y": nums[1], "w": nums[2], "h": nums[3]}
    w = _parse_float(attrs.get("width"))
    h = _parse_float(attrs.get("height"))
    if math.isfinite(w) and math.isfinite(h):
        return {"x": 0, "y": 0, "w": w, "h": h}
    raise ValueError("cannot determine SVG coordinate box "
                     "(no viewBox or numeric width/height)")


def set_root_attr(svg, name, value):
    root = parse_root(svg)
    tag = root["tag"]
    attr_re = re.compile(r"(\s%s)\s*=\s*\"[^\"]*\"" % re.escape(name), re.I)
    if attr_re.search(tag):
        tag = attr_re.sub(lambda m: '%s="%s"' % (m.group(1), value), tag, count=1)
    else:
        tag = re.sub(r"<svg\b", '<svg %s="%s"' % (name, value), tag, count=1, flags=re.I)
    return svg[:root["index"]] + tag + svg[root["index"] + root["length"]:]


def set_physical_size_mm(svg, width_mm, height_mm):
    """``setPhysicalSizeMm`` -- returns {svg, widthMm, heightMm}."""
    vb = get_view_box(svg)
    out = svg
    if "viewBox" not in parse_root(out)["attrs"]:
        out = set_root_attr(out, "viewBox",
                            "0 0 %s %s" % (js_str(vb["w"]), js_str(vb["h"])))
    out = set_root_attr(out, "width", "%smm" % js_str(round4(width_mm)))
    out = set_root_attr(out, "height", "%smm" % js_str(round4(height_mm)))
    return {"svg": out, "widthMm": width_mm, "heightMm": height_mm}


def fit_to_bed(width_mm, height_mm, bed_w_mm, bed_h_mm):
    direct = min(bed_w_mm / width_mm, bed_h_mm / height_mm)
    rotated = min(bed_w_mm / height_mm, bed_h_mm / width_mm)
    use_rotate = rotated > direct
    scale = min(1, rotated if use_rotate else direct)
    return {"widthMm": width_mm * scale, "heightMm": height_mm * scale,
            "scale": scale, "autoRotate": use_rotate,
            "fits": (rotated if use_rotate else direct) >= 1}


def px_to_mm(px, dpi=96):
    return px / dpi * MM_PER_IN


def round4(n, places=4):
    f = 10 ** places
    return js_round(n * f) / f
