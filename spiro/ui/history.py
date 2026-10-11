"""Undo and redo: for the pattern in Build, and for the paper.

A snapshot is the document's own content — steps, finishing, output — as
JSON text, so two snapshots are equal exactly when the pattern is. The
window records one each time the pattern is about to be drawn: a slider
dragged across fifty values redraws once at the end of the drag, and so
undoes as one step, not fifty.

Opening, starting or picking another pattern begins a new history; undo
walks back through edits to *this* pattern, not into the last one.

The paper has a line of its own (:class:`SceneHistory`): what is on it,
where, how big, at what angle, on which pen, and the pens themselves. Its
snapshots keep the items themselves, so a pattern taken off the paper comes
back with its curves, without being drawn again. The window steps back
through whichever of the two changed last.
"""

import copy
import json

from spiro.text import is_text_ini

LIMIT = 200          # snapshots kept


def snapshot(document):
    return json.dumps({"steps": document.steps,
                       "symmetry": document.symmetry,
                       "extras": document.extras,
                       "output": document.output}, sort_keys=True, default=str)


def restore(document, text):
    state = json.loads(text)
    document.steps = copy.deepcopy(state["steps"])
    document.symmetry = state["symmetry"]
    document.extras = state["extras"]
    document.output = state["output"]


class History:
    """A line of snapshots with a place in it."""

    def __init__(self, document):
        self.document = document
        self.reset()

    def reset(self):
        """The document as it is now is where undo stops."""
        self.past = [snapshot(self.document)]
        self.future = []

    def record(self):
        """Note the document if it has changed since the last note.
        Returns whether it had."""
        now = snapshot(self.document)
        if now == self.past[-1]:
            return False
        self.past.append(now)
        del self.past[:-LIMIT]
        self.future = []
        return True

    def can_undo(self):
        return len(self.past) > 1

    def can_redo(self):
        return bool(self.future)

    def undo(self):
        self.record()                    # an edit not yet drawn is still an edit
        if not self.can_undo():
            return False
        self.future.append(self.past.pop())
        restore(self.document, self.past[-1])
        return True

    def redo(self):
        if not self.can_redo():
            return False
        self.past.append(self.future.pop())
        restore(self.document, self.past[-1])
        return True


def scene_snapshot(scene, linked_token=None):
    """``(key, state)`` for the paper. ``key`` compares equal exactly when
    the paper is the same; ``state`` holds what :func:`restore_scene` needs.

    A linked item's curves are left out of the key: they follow Build, which
    has its own history, and a redraw arriving is not an edit.
    """
    rows, state = [], []
    for item in scene.items:
        place = (item.item_id, item.x_mm, item.y_mm, item.h_mm,
                 item.rotation_deg, item.pen, item.visible, item.name)
        # Rounded for comparing only: the place put back is the exact one.
        compared = (item.item_id, round(item.x_mm, 6), round(item.y_mm, 6),
                    round(item.h_mm, 6), round(item.rotation_deg, 6), item.pen,
                    item.visible, item.name)
        linked = linked_token is not None and item.source == linked_token
        # A pattern's curves change only by following Build; text changes
        # when it is edited here, so only text's own INI is part of the key.
        text = getattr(item.drawing, "ini_text", "")
        ink = text if is_text_ini(text) else ""
        rows.append(compared + (ink,))
        state.append((item, place, item.drawing, linked))
    pens = [pen.to_dict() for pen in scene.pens]
    key = json.dumps([rows, pens], default=str)
    return key, (state, pens)


def restore_scene(scene, state):
    from spiro.scene.scene import Pen
    items, pens = state
    restored = []
    for item, place, drawing, linked in items:
        (_, item.x_mm, item.y_mm, item.h_mm, item.rotation_deg, item.pen,
         item.visible, item.name) = place
        if not linked and item.drawing is not drawing:
            item.drawing = drawing
            item._unit = None
        restored.append(item)
    scene.items = restored
    scene.pens = [Pen.from_dict(p) for p in pens]


class SceneHistory:
    """The paper's line of snapshots. Same shape as :class:`History`."""

    def __init__(self, scene, linked=lambda: None):
        self.scene = scene
        self.linked = linked             # the token of the item Build follows
        self.reset()

    def _now(self):
        return scene_snapshot(self.scene, self.linked())

    def reset(self):
        self.past = [self._now()]
        self.future = []

    def record(self):
        now = self._now()
        if now[0] == self.past[-1][0]:
            return False
        self.past.append(now)
        del self.past[:-LIMIT]
        self.future = []
        return True

    def can_undo(self):
        return len(self.past) > 1

    def can_redo(self):
        return bool(self.future)

    def undo(self):
        self.record()
        if not self.can_undo():
            return False
        self.future.append(self.past.pop())
        restore_scene(self.scene, self.past[-1][1])
        return True

    def redo(self):
        if not self.can_redo():
            return False
        self.past.append(self.future.pop())
        restore_scene(self.scene, self.past[-1][1])
        return True
