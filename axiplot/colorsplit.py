"""``app/colorsplit.js`` -- split a BUSY SVG into per-stroke-color layers.

Pure string surgery, no XML parsing: BUSY's SVG is uniform enough that the
wrapper is preserved verbatim and only the ``<path>`` elements are bucketed.
The regexes are transliterated exactly; note ``</path>`` is REQUIRED by the
path regex (which is why the generator serializes with outerHTML -- see
Phase 6's notes).
"""

import re

_RGB_RE = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", re.I)
_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.I)
_XMLDECL_RE = re.compile(r"^\s*<\?xml[^>]*\?>", re.I)
_PATH_RE = re.compile(r"<path\b[\s\S]*?</path>")
_STROKE_RE = re.compile(r"\bstroke\s*=\s*\"([^\"]*)\"", re.I)


def rgb_to_hex(rgb):
    m = _RGB_RE.search(str(rgb))
    if not m:
        return None
    return "#%02x%02x%02x" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def parse_rgb(s):
    """``parseRgb`` -- "rgb(r,g,b)" -> [r, g, b] or None."""
    m = _RGB_RE.search(str(s))
    return [int(m.group(1)), int(m.group(2)), int(m.group(3))] if m else None


def _root_tag(svg):
    m = _ROOT_RE.search(svg)
    if not m:
        raise ValueError("no <svg> root")
    return m.group(0), m.end()


def parse(svg):
    """``parse`` -- {xmlDecl, open, preamble, suffix, paths:[{el, stroke}]}."""
    decl_m = _XMLDECL_RE.match(svg)
    xml_decl = decl_m.group(0) if decl_m else ""
    open_tag, content_start = _root_tag(svg)
    first_path = svg.find("<path", content_start)
    if first_path < 0:
        raise ValueError("no <path> elements")
    last_close = svg.rfind("</path>")
    after_paths = last_close + len("</path>")
    preamble = svg[content_start:first_path]
    suffix = svg[after_paths:]
    region = svg[first_path:after_paths]

    paths = []
    for m in _PATH_RE.finditer(region):
        el = m.group(0)
        sm = _STROKE_RE.search(el)
        stroke = sm.group(1).strip() if sm else "none"
        paths.append({"el": el, "stroke": stroke})
    return {"xmlDecl": xml_decl, "open": open_tag, "preamble": preamble,
            "suffix": suffix, "paths": paths}


def _head(parsed):
    return ((parsed["xmlDecl"] + "\n" if parsed["xmlDecl"] else "")
            + parsed["open"] + parsed["preamble"])


def split_by_color(svg):
    """``splitByColor`` -- one layer per stroke value, in first-appearance
    order. Returns {open, count, layers:[{color, hex, count, indexFirstSeen,
    svg}]}."""
    parsed = parse(svg)
    buckets = {}
    for i, p in enumerate(parsed["paths"]):
        b = buckets.get(p["stroke"])
        if b is None:
            b = {"color": p["stroke"], "hex": rgb_to_hex(p["stroke"]),
                 "els": [], "indexFirstSeen": i}
            buckets[p["stroke"]] = b
        b["els"].append(p["el"])
    head = _head(parsed)
    layers = [{"color": b["color"], "hex": b["hex"], "count": len(b["els"]),
               "indexFirstSeen": b["indexFirstSeen"],
               "svg": head + "".join(b["els"]) + parsed["suffix"]}
              for b in sorted(buckets.values(),
                              key=lambda b: b["indexFirstSeen"])]
    return {"open": parsed["open"], "count": len(parsed["paths"]),
            "layers": layers}


def split_by_groups(svg, groups):
    """``splitByGroups`` -- one layer per color GROUP (pen quantization).
    groups: [{"colors": [stroke, ...], "label": str}]."""
    parsed = parse(svg)
    head = _head(parsed)
    out = []
    for g in groups:
        color_set = set(g["colors"])
        els = [p["el"] for p in parsed["paths"] if p["stroke"] in color_set]
        out.append({"label": g.get("label"), "colors": list(g["colors"]),
                    "count": len(els),
                    "svg": head + "".join(els) + parsed["suffix"]})
    return out


def color_summary(svg):
    """``colorSummary`` -- counts only, no per-layer SVG strings."""
    parsed = parse(svg)
    buckets = {}
    for i, p in enumerate(parsed["paths"]):
        b = buckets.get(p["stroke"])
        if b is None:
            b = {"color": p["stroke"], "hex": rgb_to_hex(p["stroke"]),
                 "count": 0, "indexFirstSeen": i}
            buckets[p["stroke"]] = b
        b["count"] += 1
    return {"total": len(parsed["paths"]),
            "colors": sorted(buckets.values(),
                             key=lambda b: b["indexFirstSeen"])}
