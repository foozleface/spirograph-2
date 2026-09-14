"""``app/optimize.js`` -- the saxi-style path optimizer, ported exactly.

Deterministic: the greedy nearest-neighbour reorder uses a uniform spatial
grid whose dimensions come from ``Math.round`` (ties toward +inf) and whose
tie-breaks follow bucket insertion order, so the same input yields the same
output in both languages. The SVG bridge keeps the original's quirks: output
paths are UNCLOSED (``<path ...>`` with no ``</path>``) and the tail is
everything from the LAST ``"</"`` -- which drops the ``</g>`` of a BUSY
document. Faithful, not repaired.
"""

import math
import re

from axiplot._jsnum import js_round, js_str, js_truthy

INF = float("inf")


def _dist2(a, b):
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    return dx * dx + dy * dy


def _dist(a, b):
    return math.sqrt(_dist2(a, b))


def path_length(pts):
    total = 0
    for i in range(1, len(pts)):
        total += _dist(pts[i - 1], pts[i])
    return total


def pen_up_travel(paths):
    total = 0
    for i in range(1, len(paths)):
        prev, cur = paths[i - 1], paths[i]
        if not prev or not cur:
            continue
        total += _dist(prev[-1], cur[0])
    return total


def draw_length(paths):
    # A plain loop, NOT sum(): CPython 3.12+ sum() uses Neumaier
    # compensated summation for floats, which differs from JS accumulation
    # in the last ulp on long lists.
    total = 0.0
    for p in paths:
        total += path_length(p)
    return total


def merge(paths, tolerance):
    if not paths:
        return []
    tol2 = tolerance * tolerance
    out = [list(paths[0])]
    for i in range(1, len(paths)):
        last = out[-1]
        n = paths[i]
        lp = last[-1]
        if _dist2(lp, n[0]) <= tol2:
            k = 0
            while k < len(n) and _dist2(lp, n[k]) <= tol2:
                k += 1
            last.extend(n[k:])
        else:
            out.append(list(n))
    return out


def elide_shorter_than(paths, min_length):
    if not (min_length > 0):
        return paths
    return [p for p in paths if path_length(p) >= min_length]


def dedup_points(pts, epsilon):
    if not (epsilon > 0) or len(pts) < 2:
        return pts
    eps2 = epsilon * epsilon
    out = [pts[0]]
    for i in range(1, len(pts)):
        if _dist2(out[-1], pts[i]) > eps2:
            out.append(pts[i])
    if len(out) == 1:
        out.append(pts[-1])
    return out


def reorder(paths):
    """``reorder`` -- greedy nearest-neighbour over path endpoints with
    reversal, seeded from path 0, uniform-grid accelerated."""
    n = len(paths)
    if n <= 1:
        return list(paths)

    def endpt(i):
        p = paths[i >> 1]
        return p[-1] if (i & 1) else p[0]

    min_x = min_y = INF
    max_x = max_y = -INF
    for i in range(2 * n):
        p = endpt(i)
        if p["x"] < min_x:
            min_x = p["x"]
        if p["y"] < min_y:
            min_y = p["y"]
        if p["x"] > max_x:
            max_x = p["x"]
        if p["y"] > max_y:
            max_y = p["y"]
    span_x = max(1e-6, max_x - min_x)
    span_y = max(1e-6, max_y - min_y)
    dim_cap = max(1, math.ceil(math.sqrt(2 * n)) + 1)
    cols = js_round(math.sqrt(n * span_x / span_y))
    cols = cols if js_truthy(cols) else 1
    cols = min(dim_cap, max(1, int(cols)))
    rows = js_round((2 * n) / cols)
    rows = rows if js_truthy(rows) else 1
    rows = min(dim_cap, max(1, int(rows)))
    cw = span_x / cols
    ch = span_y / rows

    def cx(x):
        return min(cols - 1, max(0, math.floor((x - min_x) / cw)))

    def cy(y):
        return min(rows - 1, max(0, math.floor((y - min_y) / ch)))

    grid = {}
    used = bytearray(n)

    def add_pt(i):
        p = endpt(i)
        k = cx(p["x"]) * rows + cy(p["y"])
        grid.setdefault(k, []).append(i)

    for i in range(2, 2 * n):
        add_pt(i)

    def nearest(frm):
        gx = cx(frm["x"])
        gy = cy(frm["y"])
        best = -1
        best_d = INF
        for r in range(max(cols, rows) + 1):
            for ix in range(gx - r, gx + r + 1):
                if ix < 0 or ix >= cols:
                    continue
                for iy in range(gy - r, gy + r + 1):
                    if iy < 0 or iy >= rows:
                        continue
                    if (r > 0 and gx - r < ix < gx + r
                            and gy - r < iy < gy + r):
                        continue
                    bucket = grid.get(ix * rows + iy)
                    if not bucket:
                        continue
                    for ei in bucket:
                        if used[ei >> 1]:
                            continue
                        d = _dist2(frm, endpt(ei))
                        if d < best_d:
                            best_d = d
                            best = ei
            if best >= 0 and r >= 1:
                ring_min = (r - 1) * min(cw, ch)
                if ring_min * ring_min > best_d:
                    break
        return best

    out = [paths[0]]
    used[0] = 1
    cur = endpt(1)
    remaining = n - 1
    while remaining > 0:
        nn = nearest(cur)
        if nn < 0:
            break
        pid = nn >> 1
        used[pid] = 1
        remaining -= 1
        out.append(list(reversed(paths[pid])) if (nn & 1) else paths[pid])
        cur = endpt((pid << 1) if (nn & 1) else (pid << 1) | 1)
    if len(out) < n:
        for i in range(n):
            if not used[i]:
                out.append(paths[i])
    return out


def optimize(paths, opts=None):
    """dedup -> reorder -> elide -> merge, the saxi replan order."""
    opts = opts or {}
    p = paths
    if opts.get("pointJoinRadius", 0) > 0:
        p = [dedup_points(pl, opts["pointJoinRadius"]) for pl in p]
    if opts.get("sort") is not False:
        p = reorder(p)
    if opts.get("minPathLength", 0) > 0:
        p = elide_shorter_than(p, opts["minPathLength"])
    if opts.get("pathJoinRadius", 0) > 0:
        p = merge(p, opts["pathJoinRadius"])
    return p


# The JS writes its optimized paths as `<path ...>` and never closes them, so
# the document it produces is not well-formed XML. The Electron app got away
# with it because vpype rewrote the file before anything parsed it; a strict
# parser (lxml, which the in-process AxiDraw driver uses) refuses it outright.
# Closing the tag is the default here. Set this True to get the JS's spelling
# back -- the parity gate does, because its fixture came off the JS.
JS_UNCLOSED_PATHS = False


# ---- SVG bridge ------------------------------------------------------------ #

_NUM_RE = re.compile(r"-?\d*\.?\d+(?:e[-+]?\d+)?", re.I)
_PATH_TAG_RE = re.compile(r"<path\b([^>]*?)\bd=\"([^\"]*)\"([^>]*)>", re.I)
_FIRST_PATH_RE = re.compile(r"<path\b", re.I)


def parse_svg_paths(svg):
    paths = []
    for m in _PATH_TAG_RE.finditer(svg):
        nums = _NUM_RE.findall(m.group(2))
        if len(nums) < 4:
            continue
        pts = []
        for i in range(0, len(nums) - 1, 2):
            pts.append({"x": float(nums[i]), "y": float(nums[i + 1])})
        paths.append(pts)
    # JS `svg.slice(0, svg.search(...))` with no match is slice(0, -1) --
    # drops the last character. Faithful.
    first = _FIRST_PATH_RE.search(svg)
    head = svg[:first.start()] if first else svg[:-1]
    tail = svg[svg.rfind("</"):]
    return {"paths": paths, "head": head, "tail": tail}


def _num(n):
    return js_round(n * 1000) / 1000


def pts_to_d(pts):
    if not pts:
        return ""
    d = "M %s %s" % (js_str(_num(pts[0]["x"])), js_str(_num(pts[0]["y"])))
    for i in range(1, len(pts)):
        d += " L %s %s" % (js_str(_num(pts[i]["x"])), js_str(_num(pts[i]["y"])))
    return d


def _document_tail(svg):
    """Everything after the last path, so the document closes as it opened.

    ``parse_svg_paths`` keeps the JS's tail -- ``svg[svg.rfind("</"):]``, which
    is just ``</svg>`` and throws away the ``</g>`` the head opened. Fine for a
    parser that tolerates it, fatal for one that does not.
    """
    last = None
    for last in _PATH_TAG_RE.finditer(svg):
        pass
    if last is None:
        return svg[svg.rfind("</"):]
    rest = svg[last.end():]
    if rest.startswith("</path>"):
        rest = rest[len("</path>"):]
    return rest


def optimize_svg(svg, opts=None):
    parsed = parse_svg_paths(svg)
    paths = parsed["paths"]
    if not paths:
        empty = {"paths": 0, "drawLen": 0, "penUpLen": 0}
        return {"svg": svg, "before": empty, "after": empty}
    before = stats(paths)
    out = optimize(paths, opts)
    after = stats(out)
    tag_m = _PATH_TAG_RE.search(svg)
    pre = tag_m.group(1) if tag_m else ' fill="none" stroke="black"'
    post = tag_m.group(3) if tag_m else ' stroke-width="1"'
    close = "" if JS_UNCLOSED_PATHS else "</path>"
    body = "".join('<path%sd="%s"%s>%s' % (pre, pts_to_d(pts), post, close)
                   for pts in out)
    tail = parsed["tail"] if JS_UNCLOSED_PATHS else _document_tail(svg)
    return {"svg": parsed["head"] + body + tail,
            "before": before, "after": after}


def stats(paths):
    return {"paths": len(paths), "drawLen": draw_length(paths),
            "penUpLen": pen_up_travel(paths)}
