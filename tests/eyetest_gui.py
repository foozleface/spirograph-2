"""Eyetest: the window, step by step, as pictures.

Assertions pass while the picture is wrong — a strip of blank thumbnails, a
bracket drawn on the wrong rows, a slider with nothing beside it. So this
walks the window through what a person does and saves a PNG at every step
into ``tests/eyetest-results/gui/``; the pictures are the test, and every
one of them is read before anything is called done.

Runs offscreen (``QT_QPA_PLATFORM=offscreen``): the widgets paint exactly as
they do on screen, into pixmaps, without touching anyone's desktop.

    .venv/bin/python tests/eyetest_gui.py
"""

import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path  # noqa: E402

from PySide6.QtCore import QEvent, QEventLoop, Qt, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from spiro.ui import theme  # noqa: E402
from spiro.ui.gallery import GalleryDialog  # noqa: E402
from spiro.ui.main_window import MainWindow  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "eyetest-results" / "gui"
STEP = [0]
SHOTS = []


def pump(ms=60):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def wait_for(predicate, timeout=120.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        pump(40)
        if predicate():
            return True
    return False


def snap(widget, name):
    STEP[0] += 1
    path = OUT / ("%02d-%s.png" % (STEP[0], name))
    pump(80)
    widget.grab().save(str(path))
    SHOTS.append(path)
    print("  %s" % path.relative_to(ROOT))
    return path


def rendered(window):
    window.drawing = None
    window._render_now()
    return wait_for(lambda: window.drawing is not None)


app = QApplication.instance() or QApplication([])
app.setStyleSheet(theme.STYLESHEET)
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

window = MainWindow()
window.resize(1600, 950)
window.show()
pump(300)
rendered(window)
pump(200)

print("the window as it opens:")
snap(window, "fresh-window")
wait_for(lambda: not window.design.explainer.pending, timeout=60)
pump(100)
snap(window.design, "build-panel")

print("the gallery:")
gallery = GalleryDialog(window)
gallery.resize(640, 560)
gallery.show()
pump(400)
snap(gallery, "gallery")
gallery.filter.setText("wheel")
pump(60)
snap(gallery, "gallery-filtered")
gallery.close()

print("adding a table move and scoping it:")
window.design.insert_module("circle")
rendered(window)
window.design.insert_module("rotation")
rendered(window)
pump(150)
snap(window.design, "build-with-rotation-on-everything")
window.document.steps[2]["params"]["scope"] = 1
window.design.refresh(select=2)
rendered(window)
pump(150)
snap(window.design, "build-rotation-on-last-arm")
window.design.explain("total_degrees")
wait_for(lambda: not window.design.explainer.pending, timeout=60)
pump(150)
snap(window.design, "build-explainer-total-degrees")
snap(window, "window-rotation-on-last-arm")

print("the machine at a moment of the draw:")
count = window.render.sample_count()
window.render_panel.scrubber.setValue(count // 3)
pump(100)
snap(window.render_panel, "render-scrubbed-third")
window.render_panel.scrubber.setValue(count // 3)
window.render_panel.scrubber.setValue(count - 1)
window.design.strip.select(1)
window.design._select_step(1)
pump(100)
snap(window.render_panel, "render-highlight-step-2")

print("what a table move and a carriage path look like:")
window.document.steps = []
window.document.symmetry = {}
window.document.extras = {}
window.document.add_module("lissajous")
window.document.add_module("rotation")
window.document.steps[-1]["params"].update(total_degrees=-180)
window.document.add_module("rotation")
window.document.steps[-1]["params"].update(total_degrees=90, origin_x=30)
window.document.renew()
window.design.refresh(select=1)
rendered(window)
count = window.render.sample_count()
window.render_panel.scrubber.setValue(int(count * 0.3))
pump(150)
snap(window, "lissajous-rotation-selected-30pct")
window.design.strip.select(2)
window.design._select_step(2)
pump(100)
snap(window.render_panel, "lissajous-second-rotation-selected")
window.design.strip.select(0)
window.design._select_step(0)
pump(100)
snap(window.render_panel, "lissajous-arm-selected")
window.render_panel.scrubber.setValue(count - 1)

print("one of the good ones:")
window._open_path(str(ROOT / "joe_fun" / "harmonograph-shell.ini"))
wait_for(lambda: window.drawing is not None and "harmonograph-shell" in window.render.caption)
pump(200)
snap(window, "joe-harmonograph-shell")
count = window.render.sample_count()
window.render_panel.scrubber.setValue(int(count * 0.55))
pump(100)
snap(window.render_panel, "joe-shell-scrubbed")
window.design.strip.select(2)
window.design._select_step(2)
pump(100)
snap(window.render_panel, "joe-shell-arc-path-selected")
window.design.strip.select(1)
window.design._select_step(1)
window.render_panel.scrubber.setValue(count - 1)
pump(100)
snap(window.render_panel, "joe-shell-rotation-selected-end")
window.design.strip.select(0)
window.design._select_step(0)
window.design.explain("freq2")
wait_for(lambda: not window.design.explainer.pending, timeout=60)
pump(150)
snap(window.design, "joe-shell-explainer-freq2")
window.render_panel.scrubber.setValue(count - 1)
window.design.more_toggle.setChecked(True) if hasattr(window.design, "more_toggle") else None
pump(100)
snap(window.design, "joe-shell-build-more")

print("finishing:")
window.design.strip.select(1)
window.design._select_step(1)
window.design.finishing_toggle.setChecked(True)
pump(60)
snap(window.design, "finishing-open")
window.design.finishing.editors["symmetry"]["n_fold"].setValue(5)   # no tick first
rendered(window)
pump(150)
snap(window, "window-with-symmetry")
window.design.finishing.editors["clip"]["radius"].setValue(120)
rendered(window)
pump(150)
window.design.params_area.verticalScrollBar().setValue(
    window.design.params_area.verticalScrollBar().maximum())
pump(60)
snap(window.design, "finishing-clip-switched-on-by-editing")
snap(window, "window-symmetry-and-clip")
window.design.finishing.boxes["symmetry"].setChecked(False)
window.design.finishing.boxes["clip"].setChecked(False)
window.design.finishing_toggle.setChecked(False)

print("ideas:")
window.left_tabs.setCurrentWidget(window.ideas)
window.ideas.request_thumbnails()
wait_for(lambda: window.ideas._arrived >= len(window.ideas._wanted), timeout=300)
pump(200)
snap(window.ideas, "ideas")
window.ideas.filter.setText("harmonograph")
pump(60)
snap(window.ideas, "ideas-filtered")
window.ideas.filter.setText("")

print("files, paper:")
window.left_tabs.setCurrentWidget(window.library)
pump(60)
snap(window.library, "files")
window.left_tabs.setCurrentWidget(window.design)
window._place()
pump(200)
snap(window, "paper-after-place")

print("turning it on the paper:")
import math  # noqa: E402

from PySide6.QtGui import QMouseEvent  # noqa: E402

item = window.scene.items[-1]
item.move_to(240, 110)
item.set_width(110)
window.canvas.fit()
window.canvas.select(item.item_id)
window._scene_changed()
pump(120)
snap(window.canvas, "paper-turn-knob")
knob = window.canvas.rotate_knob(item)
rad = math.radians(58 - 90)
target = window.canvas.to_px(item.x_mm + 70 * math.cos(rad),
                             item.y_mm + 70 * math.sin(rad))
window.canvas.mousePressEvent(QMouseEvent(QEvent.MouseButtonPress, knob, knob,
                                          Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
window.canvas.mouseMoveEvent(QMouseEvent(QEvent.MouseMove, target, target,
                                         Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
pump(80)
snap(window.canvas, "paper-turning-protractor")
window.canvas.mouseReleaseEvent(QMouseEvent(QEvent.MouseButtonRelease, target, target,
                                            Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
pump(80)
snap(window, "paper-turned")
print("  turned to %.1f deg" % item.rotation_deg)

print("surprise me:")
window._randomize()
wait_for(lambda: window.drawing is not None and window.document.name in window.render.caption)
pump(200)
snap(window, "surprise-me")
count = window.render.sample_count()
window.render_panel.scrubber.setValue(int(count * 0.4))
pump(100)
snap(window.render_panel, "surprise-me-scrubbed")
print("  steps:", [s["params"]["type"] for s in window.document.steps])

window.close()
pump(100)
print()
print("%d screenshots in %s" % (len(SHOTS), OUT.relative_to(ROOT)))
