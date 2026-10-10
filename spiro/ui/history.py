"""Undo and redo for the pattern in Build.

A snapshot is the document's own content — steps, finishing, output — as
JSON text, so two snapshots are equal exactly when the pattern is. The
window records one each time the pattern is about to be drawn: a slider
dragged across fifty values redraws once at the end of the drag, and so
undoes as one step, not fifty.

Opening, starting or picking another pattern begins a new history; undo
walks back through edits to *this* pattern, not into the last one.
"""

import copy
import json

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
