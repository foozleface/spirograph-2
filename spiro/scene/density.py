"""Ink density, and lifting the pen before the paper tears.

A fountain pen (a Kakuno, 0.3 mm nib) wets the paper, and after about five
passes over the same spot the wet fibres tear. So the plot is simulated in
the order the machine will draw it, on a grid of cells half a nib across,
counting how many times the nib's swath has come over each cell; a stroke
that would carry a cell past the limit is lifted over the heavy ink and put
down again after it.

Where the pen comes up and goes down is chosen with care, because a
fountain pen leaves a mark where it lands, invisible in dense ink and ugly
on clean paper: the lift and the landing are placed *inside* the heavy
stretch, at least an inset in from its ends, on the least-inked cell to be
found within a couple of millimetres of the edge, so that repeated lifts
through one region spread their marks rather than piling them up. A
stretch that begins at the path's own start, or runs to its end, is simply
not drawn: the pen is up there anyway. Some overlap is fine, and a heavy
stretch too short to lift over -- narrower than two insets and a nib -- is
drawn through.

Resolution matters, and so does time, so the work is in two levels. The
whole plot is counted once on the fine grid (vectorised, no lifting) and
that map says which cells can ever reach the limit. Only path stretches
through those regions, widened by a coarse cell, go through the lifting
logic; elsewhere the pen cannot be over heavy ink, since lifting only ever
lowers a count. After lifting, the pieces that will be drawn are counted
again from scratch on the full fine grid. If any cell is still over the
limit the pen is lifted sooner and lands closer to the edge, and the whole
thing is simulated again, until the limit holds -- or until nothing more
can be done, which is reported, not hidden.

Everything here is in paper millimetres, y down, as :meth:`PlacedItem.paths_mm`
gives it. Pure functions and a grid or two; nothing here knows about Qt.
"""
import numpy as np

INSETS_MM = (1.0, 0.7, 0.5, 0.3)
SLACK_CELLS = 20                       # cells that may go one pass over the limit: a few, not a band
MIN_PIECE_MM = 6.0                     # the shortest stretch worth putting the pen down for
MIN_SKIP_MM = 1.5                      # the shortest stretch worth lifting the pen over
CHUNK_MM = 25.0                        # a long path is counted this much at a time
MIN_INSET_MM = 0.1                     # never closer to the edge of the heavy ink than this
INSET_REACH_MM = 1.5                   # how much further in the landing may go, for a lighter cell
COARSE_CELLS = 20                      # a coarse cell, in fine cells (3 mm at a 0.3 mm nib)


def resample(path, step):
    """The polyline ``path`` with points no further apart than ``step``,
    with each point's arc length. Returns ``(points, s)``."""
    pts = np.asarray(path, dtype=complex)
    if len(pts) < 2:
        return pts, np.zeros(len(pts))
    seg = np.abs(np.diff(pts))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    if s[-1] <= 0:
        return pts[:1], np.zeros(1)
    n = int(np.ceil(s[-1] / step)) + 1
    grid = np.linspace(0.0, s[-1], max(n, 2))
    sample = np.unique(np.concatenate([grid, s]))     # every vertex kept: no corner cut
    return np.interp(sample, s, pts.real) + 1j * np.interp(sample, s, pts.imag), sample


class InkGrid:
    """How many times the nib has come over each cell of the paper.

    Cells are half a nib across; the nib's swath over a point is the 2 x 2
    block of cells round it. A *visit* is one continuous passage of the
    swath over a cell: a path that lingers in a cell counts once, a path
    that leaves and comes back counts twice.
    """

    def __init__(self, width_mm, height_mm, nib_mm):
        self.nib = float(nib_mm)
        self.cell = self.nib / 2
        self.step = self.cell / 2
        self.w = int(np.ceil(width_mm / self.cell)) + 3
        self.h = int(np.ceil(height_mm / self.cell)) + 3
        self.counts = np.zeros(self.h * self.w, dtype=np.int32)

    def cells_of(self, points):
        """The cell under each point's centre, clipped to the grid."""
        ix = np.clip(np.floor(np.asarray(points).real / self.cell).astype(np.int64), 0, self.w - 1)
        iy = np.clip(np.floor(np.asarray(points).imag / self.cell).astype(np.int64), 0, self.h - 1)
        return iy * self.w + ix

    def _stamp(self, points):
        """(cell, point index) for every cell under the nib at every point,
        sorted by cell then index."""
        fx = np.asarray(points).real / self.cell - 0.5
        fy = np.asarray(points).imag / self.cell - 0.5
        ix = np.clip(np.floor(fx).astype(np.int64), 0, self.w - 2)
        iy = np.clip(np.floor(fy).astype(np.int64), 0, self.h - 2)
        idx = np.arange(len(fx))
        cells = np.concatenate([(iy + dy) * self.w + ix + dx
                                for dy in (0, 1) for dx in (0, 1)])
        index = np.concatenate([idx] * 4)
        order = np.lexsort((index, cells))
        return cells[order], index[order]

    def visits(self, points, keep=None):
        """The visits a path makes: ``(cells, first, last)``, the cell and
        the first and last point index of each continuous passage, in
        (cell, index) order. ``keep`` is a mask over the points: only
        visits touching a kept point are returned."""
        cells, index = self._stamp(points)
        if keep is not None:
            wanted = np.asarray(keep)[index]       # each pair carries its point's index
            cells, index = cells[wanted], index[wanted]
        if len(cells) == 0:
            empty = np.zeros(0, dtype=np.int64)
            return empty, empty, empty
        new = np.concatenate([[True], (cells[1:] != cells[:-1]) | (index[1:] - index[:-1] > 1)])
        starts = np.flatnonzero(new)
        ends = np.concatenate([starts[1:] - 1, [len(cells) - 1]])
        return cells[starts], index[starts], index[ends]

    def count(self, paths):
        """Add every path's visits to the counts (no lifting). One stamp
        for the whole plot: the paths are strung together with a gap in
        the point index between them, so no visit runs across two."""
        chunks = []
        for path in paths:
            pts, _ = resample(path, self.step)
            if len(pts):
                chunks.append(pts)
        if not chunks:
            return self
        points = np.concatenate(chunks)
        gaps = np.zeros(len(points), dtype=np.int64)
        at = 0
        for n, chunk in enumerate(chunks):
            gaps[at:at + len(chunk)] = 2 * n
            at += len(chunk)
        cells, index = self._stamp(points)
        index = index + gaps[index]
        new = np.concatenate([[True], (cells[1:] != cells[:-1]) | (index[1:] - index[:-1] > 1)])
        self.counts += np.bincount(cells[new], minlength=len(self.counts)).astype(np.int32)
        return self

    def max_passes(self):
        return int(self.counts.max()) if len(self.counts) else 0

    def hot_cells(self, limit):
        return int(np.count_nonzero(self.counts > limit))

    def candidate_mask(self, threshold):
        """Which coarse cells hold a fine cell at ``threshold`` or more,
        widened by one coarse cell each way; as a function of points."""
        hot = (self.counts >= threshold).reshape(self.h, self.w)
        cw = int(np.ceil(self.w / COARSE_CELLS))
        ch = int(np.ceil(self.h / COARSE_CELLS))
        padded = np.zeros((ch * COARSE_CELLS, cw * COARSE_CELLS), dtype=bool)
        padded[:self.h, :self.w] = hot
        coarse = padded.reshape(ch, COARSE_CELLS, cw, COARSE_CELLS).any(axis=(1, 3))
        grown = coarse.copy()
        grown[1:, :] |= coarse[:-1, :]
        grown[:-1, :] |= coarse[1:, :]
        grown[:, 1:] |= coarse[:, :-1]
        grown[:, :-1] |= coarse[:, 1:]

        def at(points):
            cx = np.clip((np.asarray(points).real / self.cell / COARSE_CELLS).astype(int), 0, cw - 1)
            cy = np.clip((np.asarray(points).imag / self.cell / COARSE_CELLS).astype(int), 0, ch - 1)
            return grown[cy, cx]
        return at


def guard(paths, grid, threshold, inset_mm, candidates=None, reach_mm=INSET_REACH_MM, limit=None,
          min_piece_mm=MIN_PIECE_MM, min_skip_mm=MIN_SKIP_MM, chunk_mm=CHUNK_MM):
    """Draw ``paths`` in order onto ``grid``, lifting the pen inside any
    stretch whose cells have already been come over ``threshold`` times.

    Returns ``(pieces, lifts, per_path)``: the paths as the machine should
    draw them -- each cut into the pieces drawn with the pen down -- how
    many times the pen was lifted, and how many pieces each path became.
    ``candidates`` is a function of points saying where lifting can be
    needed at all (see :meth:`InkGrid.candidate_mask`); elsewhere a path
    is taken as it is.

    A long path is walked ``chunk_mm`` at a time, so that the ink it lays
    down is counted as it goes: a pass the path itself left off never
    counts towards lifting over a later stretch, which is what left white
    gaps in a drawing that is one long line.

    No piece shorter than ``min_piece_mm`` is put down where it can be
    helped: a fountain pen barely inks a dab that short, and each one costs
    a lift and a landing mark. Two cuts with only a crumb between them
    become one cut, and a crumb at either end of the path is left off with
    the cut beside it -- but only where other ink already lies under the
    whole crumb; on bare paper the crumb is drawn. Nor is the pen lifted
    over less than ``min_skip_mm``: up and straight back down is a landing
    mark for nothing.
    """
    min_skip = max(grid.nib, min_skip_mm)
    limit = threshold if limit is None else limit
    pieces, lifts, per_path = [], 0, []
    for path in paths:
        pts, s = resample(path, grid.step)
        if len(pts) < 2:
            pieces.append(np.asarray(path, dtype=complex))
            per_path.append(1)
            continue
        keep = candidates(pts) if candidates is not None else None
        if keep is not None and not keep.any():
            # nowhere near heavy ink: drawn whole, counted whole
            cells, _, _ = grid.visits(pts)
            np.add.at(grid.counts, cells, 1)
            pieces.append(np.asarray(path, dtype=complex))
            per_path.append(1)
            continue
        total = s[-1]
        # every visit of the path, found once; each is decided in the chunk
        # where it begins, against what is drawn by then
        cells, first, last = grid.visits(pts, keep)
        if keep is not None:
            # the part outside the candidate regions is counted plainly
            others, _, _ = grid.visits(pts, ~keep)
            np.add.at(grid.counts, others, 1)
        chunk = np.minimum((s[first] / chunk_mm).astype(np.int64), int(total // chunk_mm))
        cuts = []
        for k in np.unique(chunk):
            mine = chunk == k
            cuts = _chunk_cuts(cells[mine], first[mine], last[mine], pts, s, grid, cuts,
                               threshold, inset_mm, reach_mm, limit, min_skip)
        cuts = [c for c in cuts if not _draw_through(c, pts, s, grid, limit, min_skip)]
        cuts = _no_crumbs(cuts, pts, s, grid, min_piece_mm)
        if not cuts:
            pieces.append(np.asarray(path, dtype=complex))
            per_path.append(1)
            continue
        lifts += len(cuts)
        cut = _cut(path, cuts)
        pieces.extend(cut)
        per_path.append(len(cut))
    return pieces, lifts, per_path


def _chunk_cuts(cells, first, last, pts, s, grid, cuts, threshold, inset_mm, reach_mm,
                limit, min_skip):
    """The path's ``cuts`` so far, with those for one chunk's visits added
    (``cells``, ``first``, ``last`` as :meth:`InkGrid.visits` gives them),
    and the visits that are drawn counted onto ``grid``. A visit inside a
    cut already made is not drawn and not counted."""
    if cuts:
        ups = np.array([u for u, _ in cuts])
        downs = np.array([d for _, d in cuts])
        which = np.searchsorted(ups, s[first], side="right") - 1
        gone = (which >= 0) & (s[last] <= downs[np.clip(which, 0, len(downs) - 1)])
        cells, first, last = cells[~gone], first[~gone], last[~gone]
    if not len(cells):
        return cuts
    # A visit is hot when the cell has had `threshold` visits before it:
    # what is drawn already, plus this chunk's own earlier visits of the
    # same cell. The visits come sorted by cell, so the rank within a
    # cell's group is the count of earlier ones in the chunk.
    group_start = np.concatenate([[True], cells[1:] != cells[:-1]])
    rank = np.arange(len(cells)) - np.maximum.accumulate(np.where(group_start, np.arange(len(cells)), 0))
    hot = grid.counts[cells] + rank >= threshold
    np.add.at(grid.counts, cells, 1)
    if not hot.any():
        return cuts
    # the hot visits as arc-length stretches, merged into runs: a new run
    # starts where a stretch begins after everything before it has ended
    a = s[first[hot]]
    b = s[last[hot]]
    order = np.argsort(a, kind="stable")
    a, b = a[order], b[order]
    reach = np.maximum.accumulate(b)
    starts = np.concatenate([[True], a[1:] > reach[:-1] + grid.step])
    run_first = np.flatnonzero(starts)
    run_last = np.concatenate([run_first[1:] - 1, [len(a) - 1]])
    runs = list(zip(a[run_first], reach[run_last]))
    total = s[-1]
    # ink under the nib, per point, near the runs
    i_lo = max(0, np.searchsorted(s, runs[0][0] - 3 * (inset_mm + reach_mm)) - 1)
    i_hi = min(len(s), np.searchsorted(s, runs[-1][1] + 3 * (inset_mm + reach_mm)) + 1)
    sw = s[i_lo:i_hi]
    load = grid.counts[grid.cells_under(pts[i_lo:i_hi])].max(axis=1)
    new = []
    last_down = cuts[-1][1] if cuts else -1.0
    for s_a, s_b in runs:
        at_start = s_a <= grid.step
        at_end = s_b >= total - grid.step
        # Where to lift and where to land: a spot the paper can still take
        # one more pass on, as near the edge of the saturated stretch as
        # there is one -- inside it for choice, since that is where a
        # landing mark hides, else just outside, where the ink is one pass
        # short of the limit and still dense to the eye. The marks of the
        # loops that cross one band then spread along the band's edge
        # instead of piling onto its first cell.
        if at_start:
            up = 0.0
        else:
            up = _landing(load, sw, s_a, limit, inset_mm, reach_mm, inward=+1,
                          lo=max(last_down, s_a - inset_mm), hi=min(s_a + inset_mm + reach_mm, s_b))
        if at_end:
            down = total
        else:
            down = _landing(load, sw, s_b, limit, inset_mm, reach_mm, inward=-1,
                            lo=max(s_b - inset_mm - reach_mm, up), hi=min(s_b + inset_mm, total))
        shortest = grid.nib if at_start or at_end else min_skip
        if down - up < shortest:
            i0, i1 = np.searchsorted(sw, up, side="left"), np.searchsorted(sw, down, side="right")
            if load[i0:i1].max(initial=0) <= limit:
                continue                  # drawn through: the paper takes it
            # too short to be worth a landing, but drawing it would tear:
            # lift, over as much of the covered ink round it as makes the
            # lift worth one
            up, down = _widen(load, sw, up, down, shortest, lo=max(last_down, 0.0), hi=total)
        new.append((up, down))
        last_down = down
    if new:
        # what is skipped is not drawn: give those cells their visits back,
        # in one go -- a visit is skipped when it lies within a cut
        ups = np.array([u for u, _ in new])
        downs = np.array([d for _, d in new])
        which = np.searchsorted(ups, s[first], side="right") - 1
        inside = (which >= 0) & (s[last] <= downs[np.clip(which, 0, len(downs) - 1)])
        np.subtract.at(grid.counts, cells[inside], 1)
    out = list(cuts)
    for up, down in new:
        if out and up <= out[-1][1] + grid.step:
            out[-1] = (out[-1][0], max(out[-1][1], down))     # overlaps the last cut: one cut
        else:
            out.append((up, down))
    return out


def _draw_through(cut, pts, s, grid, limit, min_skip):
    """True for a lift too short to be worth its landing -- a stub left at
    a chunk edge -- whose stretch the paper can take after all; its visits
    are then put on the grid."""
    up, down = cut
    if up <= 0 or down >= s[-1] or down - up >= min_skip:
        return False
    i0, i1 = np.searchsorted(s, up, side="left"), np.searchsorted(s, down, side="right")
    if i1 - i0 < 1:
        return True
    cells, _, _ = grid.visits(pts[i0:i1])
    if grid.counts[cells].max(initial=0) + 1 > limit:
        return False
    np.add.at(grid.counts, cells, 1)
    return True


def _widen(load, s, up, down, length, lo, hi):
    """``(up, down)`` grown evenly towards ``length`` of arc, between ``lo``
    and ``hi``, over points where other ink lies under the nib (``load``
    counts this pass too, so at least 2) -- never onto bare paper."""
    i_up = np.searchsorted(s, up, side="left")
    i_down = min(np.searchsorted(s, down, side="right") - 1, len(s) - 1)
    while s[i_down] - s[i_up] < length:
        grew = False
        if i_up > 0 and s[i_up - 1] >= lo and load[i_up - 1] >= 2:
            i_up -= 1
            grew = True
        if s[i_down] - s[i_up] >= length:
            break
        if i_down < len(s) - 1 and s[i_down + 1] <= hi and load[i_down + 1] >= 2:
            i_down += 1
            grew = True
        if not grew:
            break
    return min(up, float(s[i_up])), max(down, float(s[i_down]))


def _no_crumbs(cuts, pts, s, grid, min_piece_mm):
    """``cuts`` with the crumbs between them, and at the path's ends, left
    off too -- where the ink already on the paper covers the whole crumb.
    A crumb left off gives its cells their visits back."""
    total = s[-1]

    def bare_or_drop(lo, hi):
        """True (and the crumb's visits taken off the grid) when ink lies
        under the whole crumb besides its own pass."""
        i0, i1 = np.searchsorted(s, lo, side="left"), np.searchsorted(s, hi, side="right")
        if i1 - i0 < 2:
            return True
        under = grid.counts[grid.cells_under(pts[i0:i1])].max(axis=1)
        if (under < 2).any():                   # nothing but its own pass under the nib: white paper
            return False
        cells, _, _ = grid.visits(pts[i0:i1])
        np.subtract.at(grid.counts, cells, 1)
        return True

    out = []
    for up, down in cuts:
        if out and up - out[-1][1] < min_piece_mm and bare_or_drop(out[-1][1], up):
            out[-1] = (out[-1][0], down)
        else:
            out.append((up, down))
    if out and 0.0 < out[0][0] < min_piece_mm and bare_or_drop(0.0, out[0][0]):
        out[0] = (0.0, out[0][1])
    if out and out[-1][1] < total and total - out[-1][1] < min_piece_mm \
            and bare_or_drop(out[-1][1], total):
        out[-1] = (out[-1][0], total)
    return out


def _landing(load, s, edge, limit, inset_mm, reach_mm, inward, lo, hi):
    """The arc length at which to lift or land beside the edge of a
    saturated stretch at ``edge``.

    Inside the stretch for choice -- that is where a landing mark hides --
    but only as far in as every cell on the way still has room for one
    more pass, since the pen draws from the edge to the landing; aiming
    for ``inset_mm`` in. If the very edge is already at the limit the
    pen cannot touch it, so the landing goes outside: the nearest point
    with room, no further than the inset. ``inward`` is +1 when inside
    lies at greater arc length."""
    i0, i1 = np.searchsorted(s, lo, side="left"), np.searchsorted(s, hi, side="right")
    if i1 <= i0:
        return edge
    span = s[i0:i1]
    room = load[i0:i1] < limit
    depth = (span - edge) * inward              # > 0 inside, < 0 outside
    order = np.argsort(depth)
    inside = order[depth[order] >= 0]
    if len(inside) and room[inside[0]]:
        # the prefix of the inside with room, edge first
        prefix = inside[:int(np.argmin(np.concatenate([room[inside], [False]])))]
        deep = prefix[depth[prefix] >= MIN_INSET_MM]
        if len(deep):
            return float(span[deep[np.argmin(np.abs(depth[deep] - inset_mm))]])
    outside = order[depth[order] < 0][::-1]     # nearest the edge first
    ok = outside[room[outside]]
    if len(ok):
        return float(span[ok[0]])
    return edge


def _lightest(load, s, lo, hi):
    """The arc length between ``lo`` and ``hi`` where the nib is over the
    least-inked cells (``load`` is the ink under the nib at each point of
    ``s``) -- where a landing mark will show least -- nearest ``lo``
    among equals."""
    if hi <= lo:
        return lo
    i0, i1 = np.searchsorted(s, lo, side="left"), np.searchsorted(s, hi, side="right")
    if i1 <= i0:
        return lo
    return float(s[i0 + int(np.argmin(load[i0:i1]))])


def _cells_under(self, points):
    fx = np.asarray(points).real / self.cell - 0.5
    fy = np.asarray(points).imag / self.cell - 0.5
    ix = np.clip(np.floor(fx).astype(np.int64), 0, self.w - 2)
    iy = np.clip(np.floor(fy).astype(np.int64), 0, self.h - 2)
    return np.stack([(iy + dy) * self.w + ix + dx for dy in (0, 1) for dx in (0, 1)], axis=1)


InkGrid.cells_under = _cells_under


def _cut(path, cuts):
    """``path`` with the arc-length stretches in ``cuts`` taken out, as the
    pieces that remain, each ending and starting exactly at the cut."""
    pts = np.asarray(path, dtype=complex)
    seg = np.abs(np.diff(pts))
    s = np.concatenate([[0.0], np.cumsum(seg)])

    def at(length):
        return complex(np.interp(length, s, pts.real), np.interp(length, s, pts.imag))

    out = []
    start = 0.0
    for up, down in cuts:
        keep = pts[(s > start) & (s < up)]
        piece = np.concatenate([[at(start)], keep, [at(up)]])
        if len(piece) >= 2 and up > start:
            out.append(piece)
        start = down
    keep = pts[s > start]
    piece = np.concatenate([[at(start)], keep])
    if len(piece) >= 2 and s[-1] > start:
        out.append(piece)
    return out


def plan(paths, width_mm, height_mm, nib_mm=0.3, max_passes=5, insets=INSETS_MM,
         slack_cells=SLACK_CELLS):
    """Lift the pen so that no cell of the paper is come over more than
    ``max_passes`` times, if it can be done: the pieces to draw, and a
    report.

    Tries the gentlest plan first -- lift only at the limit, with the
    deepest inset -- and checks it by counting the drawn pieces afresh on
    the full grid. When the paper would still tear, lifts sooner and lands
    closer to the edge of the heavy ink, and tries again. A few cells one
    pass over -- ``slack_cells`` of them at most -- are let through: the
    paper takes a handful of extra touches, and lifting sooner to clear
    them would cut the plot at every crossing. ``report["ok"]`` says
    whether the limit was met; ``report["max_passes"]`` is the worst cell
    either way and ``report["hot_cells"]`` how many cells are over.
    """
    paths = [np.asarray(p, dtype=complex) for p in paths if len(p) >= 2]
    before = InkGrid(width_mm, height_mm, nib_mm).count(paths)
    report = {"nib_mm": nib_mm, "limit": max_passes, "slack_cells": slack_cells,
              "before": before.max_passes(), "hot_before": before.hot_cells(max_passes),
              "cell_mm": before.cell}
    if before.max_passes() <= max_passes:
        report.update(ok=True, lifts=0, threshold=None, inset_mm=None,
                      max_passes=before.max_passes(), hot_cells=0, tries=0,
                      pieces_per_path=[1] * len(paths))
        return paths, report
    best = None
    tries = 0
    detail = []                   # (threshold, inset, worst, hot cells, lifts) per try
    previous_threshold_best = None
    for threshold in range(max_passes, 1, -1):
        candidates = before.candidate_mask(threshold)
        threshold_best = None
        last = None
        for inset in insets:
            tries += 1
            grid = InkGrid(width_mm, height_mm, nib_mm)
            pieces, lifts, per_path = guard(paths, grid, threshold, inset, candidates, limit=max_passes)
            check = InkGrid(width_mm, height_mm, nib_mm).count(pieces)
            result = (check.max_passes(), check.hot_cells(max_passes), pieces, lifts, threshold, inset, per_path)
            detail.append((threshold, inset, result[0], result[1], lifts))
            if best is None or result[:2] < best[:2]:
                best = result
            if threshold_best is None or result[:2] < threshold_best:
                threshold_best = result[:2]
            if check.max_passes() <= max_passes + 1 and result[1] <= slack_cells:
                report.update(ok=True, lifts=lifts, threshold=threshold, inset_mm=inset,
                              max_passes=check.max_passes(), hot_cells=result[1], tries=tries,
                              pieces_per_path=per_path, tries_detail=detail)
                return pieces, report
            if last == result[:2]:
                break                 # a closer landing changed nothing; lift sooner instead
            last = result[:2]
        if previous_threshold_best == threshold_best:
            break                     # lifting sooner changed nothing: what is left cannot be lifted over
        previous_threshold_best = threshold_best
    worst, hot, pieces, lifts, threshold, inset, per_path = best
    report.update(ok=False, lifts=lifts, threshold=threshold, inset_mm=inset,
                  max_passes=worst, hot_cells=hot, tries=tries, pieces_per_path=per_path,
                  tries_detail=detail)
    return pieces, report


# -- a picture of what the guard did ----------------------------------------------- #

def preview_svg(strokes, report, width_mm, height_mm, nib_mm=0.3, limit=5, before=None):
    """An SVG of a guarded plot for the eye: the paper's ink map underneath
    (cells at the limit in amber, over it in red), the strokes as the
    machine will draw them, and a ring where each piece starts -- where a
    fountain pen will leave its landing mark. ``strokes`` are
    ``(pen_index, opacity, path)`` as :meth:`Scene.guarded_strokes` gives
    them; ``before`` is the unguarded grid, counted if not given."""
    paths = [path for _, _, path in strokes]
    grid = before or InkGrid(width_mm, height_mm, nib_mm).count(paths)
    counts = grid.counts.reshape(grid.h, grid.w)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" '
           'viewBox="0 0 %g %g">' % (width_mm, height_mm, width_mm, height_mm),
           '<rect width="%g" height="%g" fill="#ffffff"/>' % (width_mm, height_mm)]
    for level, color in ((limit, "#f0b429"), (limit + 1, "#d7263d")):
        ys, xs = np.nonzero(counts >= level)
        if len(xs):
            out.append('<g fill="%s">' % color)
            out.extend('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f"/>'
                       % (x * grid.cell, y * grid.cell, grid.cell, grid.cell)
                       for x, y in zip(xs, ys))
            out.append('</g>')
    out.append('<g fill="none" stroke="#222222" stroke-width="%g" stroke-opacity="0.35" '
               'stroke-linecap="round">' % nib_mm)
    out.extend('<path d="%s"/>' % _path_data_short(path) for path in paths)
    out.append('</g>')
    if report.get("lifts"):
        out.append('<g fill="none" stroke="#1f6fb4" stroke-width="0.15">')
        out.extend('<circle cx="%.3f" cy="%.3f" r="0.6"/>' % (p[0].real, p[0].imag) for p in paths)
        out.append('</g>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


def _path_data_short(points):
    pts = np.asarray(points)
    return "M %.3f,%.3f " % (pts[0].real, pts[0].imag) + " ".join(
        "L %.3f,%.3f" % (p.real, p.imag) for p in pts[1:])


def main(argv=None):
    """``python -m spiro.scene.density sheet.sheet.json out.svg``: regenerate
    a sheet's patterns at plot quality, run the ink guard as the plot would,
    print its report, and write the picture.

    ``python -m spiro.scene.density pattern.ini out.svg [width_mm]``: the
    one pattern alone on the AxiDraw's bed, at that width (or fitted as
    "Place on paper" would), the same way."""
    import sys
    import time
    from pathlib import Path
    from spiro.pipeline import PLOT_SAMPLING, run
    from spiro.pipeline.document import Document, at_sampling
    from spiro.scene.paper import Paper
    from spiro.scene.scene import Scene, item_inis
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (2, 3):
        print(main.__doc__)
        return 2
    source = Path(args[0])
    if source.name.endswith(".sheet.json"):
        data = Scene.read(source)
        drawings = [run(at_sampling(text, PLOT_SAMPLING)) for text in item_inis(data)]
        scene = Scene.from_dict(data, drawings)
    else:
        scene = Scene(paper=Paper.from_axidraw(3))
        drawing = run(Document.load(str(source)).to_ini(PLOT_SAMPLING))
        item = scene.add(drawing, name=source.stem)
        if len(args) == 3:
            item.set_width(float(args[2]))
        scene.ensure_pen_colors(scene.item_inks(item))
    started = time.time()
    strokes, report = scene.guarded_strokes()
    report["seconds"] = round(time.time() - started, 1)
    shown = {k: v for k, v in report.items() if k != "pieces_per_path"}
    print(shown)
    before = InkGrid(scene.paper.width_mm, scene.paper.height_mm, scene.nib_mm).count(
        [path for _, _, path in scene.plot_strokes()])
    svg = preview_svg(strokes, report, scene.paper.width_mm, scene.paper.height_mm,
                      scene.nib_mm, scene.max_passes, before)
    with open(args[1], "w") as f:
        f.write(svg)
    print("wrote", args[1])
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
