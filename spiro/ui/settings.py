"""The app's own settings stores, by name.

One place that knows the organisation name and, more to the point, builds
each store with an explicit format: ``QSettings(org, app)`` on macOS goes
to the system preferences whatever path was set, so a window under test
would read -- and write -- the desktop app's own settings, and the session
saved beside them. The four-argument form honours ``setDefaultFormat`` and
``setPath``, which is what the gates set before making a window.
"""
from PySide6.QtCore import QSettings

ORGANISATION = "spirograph-2"


def store(name):
    """The settings store ``name`` ("app", "plotter", "notify")."""
    return QSettings(QSettings.defaultFormat(), QSettings.UserScope, ORGANISATION, name)
