"""Keeping the machine awake while there is a plot to finish.

A plot is hours of the operator not touching the keyboard, which is exactly
what an idle timer is looking for: this desktop suspends after 30 minutes on
mains and 20 on battery, and a suspend in the middle of a plot is a ruined
sheet -- the carriage stops where it is and the paper cannot be re-registered.

The lock is taken from ``systemd-logind``, the same place GNOME's own "don't
sleep, a video is playing" comes from, so it is visible in ``systemd-inhibit
--list`` and dies with the process that took it. There is no D-Bus dependency:
``systemd-inhibit`` holds the lock for the lifetime of a command, and the
command here is a ``cat`` reading a pipe we own. Close the pipe -- deliberately
on the way out, or by being killed -- and ``cat`` sees EOF, ``systemd-inhibit``
exits, and logind drops the lock. Nothing can leak a lock that outlives us.

``idle`` is what stops the idle timer; ``sleep`` also refuses an explicit
``systemctl suspend`` (which then says who is blocking it, and takes ``-i`` to
override). The lid switch is deliberately NOT held: closing the lid is a
decision, not an accident, and it stays the operator's to make.
"""

import shutil
import subprocess

WHAT = "idle:sleep"


class SleepInhibitor:
    """A logind inhibitor lock, held for as long as this object is started.

    Best-effort by design: a machine with no logind still plots. ``reason``
    says what happened either way, because an inhibitor that silently did not
    take is worse than none at all -- it is a suspend nobody expected.
    """

    def __init__(self, why="A plot is running", who="BUSY plotter", what=WHAT):
        self.why = why
        self.who = who
        self.what = what
        self.proc = None
        self.reason = "not started"

    def active(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        if self.active():
            return True
        exe = shutil.which("systemd-inhibit")
        if not exe:
            self.reason = "no systemd-inhibit on this machine"
            return False
        try:
            self.proc = subprocess.Popen(
                [exe, "--what=%s" % self.what, "--who=%s" % self.who,
                 "--why=%s" % self.why, "--mode=block", "cat"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        except Exception as exc:
            self.proc = None
            self.reason = str(exc)
            return False
        self.reason = "holding %s" % self.what
        return True

    def stop(self):
        """Give the lock back. Closing the pipe is what does it; the wait is
        only so the process is reaped."""
        if self.proc is None:
            return
        proc, self.proc = self.proc, None
        try:
            if proc.stdin:
                proc.stdin.close()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        self.reason = "released"

    def describe(self):
        if self.active():
            return "sleep and idle-suspend held off while this is open"
        return "NOT holding sleep off — %s" % self.reason

    # Usable as a context manager, which is what a CLI plot wants.
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()
        return False
