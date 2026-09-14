"""``app/calibration.js`` -- the pen-registration calibration sheet.

Three stacked figures (bullseye / vertical fan / horizontal stack); pen *i*
draws one ring, one vertical and one horizontal line at index *i*. Pure
geometry in millimetres; numbers round through ``Math.round(n*1000)/1000``
and format as JS strings, so the SVG output is byte-comparable.
"""

from axiplot._jsnum import js_round, js_str

MM_PER_IN = 25.4

DEFAULTS = {
    "pens": 7,
    "spacingMm": 1.5,
    "innerRadiusMm": 6,
    "lineLenMm": 25,
    "blockGapMm": MM_PER_IN / 2,
    "marginMm": 20,
    "strokeMm": 0.12,
    "set": 0,
    "columns": 8,
    "setGapMm": 6,
}


def _r2(n):
    return js_round(n * 1000) / 1000


def layout(opts=None):
    c = dict(DEFAULTS, **(opts or {}))
    n = max(1, int(js_round(c["pens"])))
    s = c["spacingMm"]
    r_max = c["innerRadiusMm"] + (n - 1) * s
    fan_w = (n - 1) * s
    stack_h = (n - 1) * s
    block_w = max(2 * r_max, c["lineLenMm"], fan_w)

    set_i = max(0, int(js_round(c.get("set") or 0)))
    set_pitch = _r2(block_w + c["setGapMm"])
    origin_x = _r2(c["marginMm"] + set_i * set_pitch)
    cx = _r2(origin_x + block_w / 2)

    bull = {"cx": cx, "cy": _r2(c["marginMm"] + r_max),
            "rMin": _r2(c["innerRadiusMm"]), "rMax": _r2(r_max)}
    v_top = _r2(c["marginMm"] + 2 * r_max + c["blockGapMm"])
    vert = {"top": v_top, "bottom": _r2(v_top + c["lineLenMm"]),
            "x0": _r2(cx - fan_w / 2), "width": _r2(fan_w)}
    h_top = _r2(vert["bottom"] + c["blockGapMm"])
    horiz = {"y0": h_top, "x0": _r2(cx - c["lineLenMm"] / 2),
             "x1": _r2(cx + c["lineLenMm"] / 2), "height": _r2(stack_h)}

    out = dict(c)
    out.update({
        "n": n, "set": set_i, "cx": cx, "bull": bull, "vert": vert,
        "horiz": horiz, "blockW": _r2(block_w), "setPitch": set_pitch,
        "originX": origin_x,
        "inkRight": _r2(origin_x + block_w),
        "inkBottom": _r2(h_top + stack_h),
        "extentW": _r2(origin_x + block_w + c["marginMm"]),
        "extentH": _r2(h_top + stack_h + c["marginMm"]),
    })
    return out


def fits_bed(geo, bed_w_mm, bed_h_mm):
    return {"fits": geo["inkRight"] <= bed_w_mm and geo["inkBottom"] <= bed_h_mm,
            "inkRight": geo["inkRight"], "inkBottom": geo["inkBottom"],
            "extentW": geo["extentW"], "extentH": geo["extentH"]}


def _line(x0, y0, x1, y1):
    return "M%s,%sL%s,%s" % (js_str(_r2(x0)), js_str(_r2(y0)),
                             js_str(_r2(x1)), js_str(_r2(y1)))


def _circle(cx, cy, r):
    return ("M%s,%sA%s,%s 0 1 0 %s,%s" % (
        js_str(_r2(cx - r)), js_str(_r2(cy)), js_str(_r2(r)), js_str(_r2(r)),
        js_str(_r2(cx + r)), js_str(_r2(cy)))
        + "A%s,%s 0 1 0 %s,%s" % (
        js_str(_r2(r)), js_str(_r2(r)), js_str(_r2(cx - r)), js_str(_r2(cy))))


def pen_paths(index, geo):
    g = dict(DEFAULTS, **geo)
    i = max(0, int(js_round(index)))
    s = g["spacingMm"]
    x = g["vert"]["x0"] + i * s
    y = g["horiz"]["y0"] + i * s
    return [
        _circle(g["cx"], g["bull"]["cy"], g["innerRadiusMm"] + i * s),
        _line(x, g["vert"]["top"], x, g["vert"]["bottom"]),
        _line(g["horiz"]["x0"], y, g["horiz"]["x1"], y),
    ]


def _path_el(d, color):
    return '<path d="%s" stroke="%s"></path>' % (d, color)


def _svg_wrap(g, bed, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" '
            % (js_str(_r2(bed["wMm"])), js_str(_r2(bed["hMm"])))
            + 'viewBox="0 0 %s %s">' % (js_str(_r2(bed["wMm"])),
                                        js_str(_r2(bed["hMm"])))
            + '<g fill="none" stroke-width="%s" stroke-linecap="round">%s</g></svg>'
            % (js_str(g["strokeMm"]), body))


def pen_svg(geo, bed, index, color=None):
    g = dict(DEFAULTS, **geo)
    if index < 0 or index >= g["n"]:
        raise ValueError("pen %d is outside a %d-pen sheet" % (index + 1, g["n"]))
    body = "".join(_path_el(d, color or "#000000") for d in pen_paths(index, g))
    return _svg_wrap(g, bed, body)


def pen_svg_sets(geo, bed, index, color=None, sets=None):
    g = dict(DEFAULTS, **geo)
    cols = sorted(sets) if sets else [g.get("set") or 0]
    if index < 0 or index >= g["n"]:
        raise ValueError("pen %d is outside a %d-pen sheet" % (index + 1, g["n"]))
    body = ""
    for set_i in cols:
        gs = layout(dict(g, set=set_i))
        body += "".join(_path_el(d, color or "#000000")
                        for d in pen_paths(index, gs))
    return _svg_wrap(g, bed, body)


def sheet_svg(geo, bed, pens=None):
    g = dict(DEFAULTS, **geo)
    pen_list = pens if pens else [{"color": "#000000"} for _ in range(g["n"])]
    body = ""
    for i, p in enumerate(pen_list[:g["n"]]):
        body += "".join(_path_el(d, p.get("color") or "#000000")
                        for d in pen_paths(i, g))
    return _svg_wrap(g, bed, body)
