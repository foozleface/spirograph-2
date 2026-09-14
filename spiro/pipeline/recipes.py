"""Pipelines worth looking at, at random.

Rolling every parameter of every module independently produces noise. These
are the shapes that turned out to be worth drawing — ratios that close, decay
rates that spiral rather than collapse, gear pairs whose greatest common
divisor leaves a pattern with lobes instead of a smear — with a range around
each number wide enough to keep surprising you.

They came from two sweeps of a few thousand generated patterns, scored and
sorted; the ones marked with a score are the survivors. Ported here from the
web UI's JavaScript, where they were trapped inside a React component. As data
in a module they can be tested, and the button that uses them is three lines.

A recipe is ``fn(r) -> {steps, stroke_width, symmetry}``. ``r`` is the little
random helper below, so a recipe never touches the global random state and a
seed makes the whole thing reproducible.
"""

import math
import random
import unicodedata

RECIPES = []


class _Rand:
    """pick / float / int, spelled the way the recipes read best."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def pick(self, options):
        return self.rng.choice(list(options))

    def f(self, low, high):
        """A float in range, to two decimals — enough for any of these."""
        return round(self.rng.uniform(low, high), 2)

    def i(self, low, high):
        return int(round(self.rng.uniform(low, high)))

    def chance(self, probability):
        return self.rng.random() < probability

    def jitter(self, spread):
        """A small signed nudge — how a frequency is detuned to make beats."""
        return (self.rng.random() - 0.5) * spread


def recipe(name):
    """Register a recipe under a name the UI can show."""
    def wrap(fn):
        fn.recipe_name = name
        RECIPES.append(fn)
        return fn
    return wrap


# -- the pieces a recipe is built from ---------------------------------------- #

def mod(module_type, **params):
    return dict(params, type=module_type)


def single(module_type, **params):
    return {"kind": "single", "params": mod(module_type, **params)}


def group(*branches):
    """Arms that run at once and sum. Each branch is a list of modules."""
    return {"kind": "group", "branches": [list(b) for b in branches]}


def rot(degrees):
    return single("rotation", total_degrees=degrees, origin_x=0, origin_y=0,
                  normalize=True)


def arc(radius, sweep):
    return single("arc", radius=radius, sweep_angle=sweep, start_angle=0,
                  cycles=1)


def spiral_arc(inner, outer, sweep):
    return single("spiral_arc", inner_radius=inner, outer_radius=outer,
                  sweep_angle=sweep, start_angle=0)


def noise(amplitude, frequency):
    return single("noise", amplitude=amplitude, frequency=frequency)


def bend(radius, sweep):
    return single("bend", radius=radius, sweep_angle=sweep)


def damp(rate, duration):
    return single("damping", decay_rate=rate, duration=duration)


def scale(start, end):
    return single("scale", start_scale=start, end_scale=end)


def stretch(x, y):
    return single("stretch", scale_x=x, scale_y=y)


# Pendulums three and four, silenced. A two-pendulum harmonograph is a
# different instrument from a four-pendulum one and most of these want the
# simpler one.
#
# Phases are in degrees — the module reads degrees. The first port of these
# recipes wrote radians, which the module read as a degree or two, so the
# four-pendulum figures came out with their pendulums nearly in phase.
QUIET = {"freq3": 0, "amp3": 0, "phase3": 0, "decay3": 0,
         "freq4": 0, "amp4": 0, "phase4": 0, "decay4": 0}

PRIMES = [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 67, 71, 79, 83, 89]


def _gcd(a, b):
    return math.gcd(int(a), int(b))


# -- harmonographs -------------------------------------------------------------- #

@recipe("Slow-decay four-frequency")
def _slow_decay(r):
    a, b = r.pick([(3, 2), (2, 3), (5, 4), (4, 3)])
    c, d = r.pick([(5, 4), (4, 3), (7, 5), (3, 2)])
    return {"steps": [single(
        "harmonograph",
        freq1=a, freq2=b + r.jitter(0.006), freq3=c, freq4=d + r.jitter(0.004),
        amp1=100, amp2=r.f(70, 90), amp3=r.f(40, 60), amp4=r.f(30, 50),
        phase1=0, phase2=r.f(29, 90), phase3=r.f(57, 115),
        phase4=r.f(86, 143),
        decay1=r.f(0.001, 0.004), decay2=r.f(0.001, 0.004),
        decay3=r.f(0.001, 0.004), decay4=r.f(0.001, 0.004),
        duration=r.f(100, 150), cycles=1)], "stroke_width": 0.1}


@recipe("Seven against five")
def _seven_five(r):
    a, b = r.pick([(7, 5), (5, 7), (7, 4), (4, 7)])
    return {"steps": [single(
        "harmonograph",
        freq1=a, freq2=b + r.jitter(0.006), freq3=r.pick([3, 2]),
        freq4=r.pick([4, 5]) + r.jitter(0.01),
        amp1=100, amp2=80, amp3=60, amp4=50,
        phase1=0, phase2=90, phase3=r.f(17, 40), phase4=r.f(86, 143),
        decay1=r.f(0.003, 0.005), decay2=r.f(0.002, 0.004),
        decay3=r.f(0.004, 0.006), decay4=r.f(0.003, 0.005),
        duration=r.f(50, 80), cycles=1)], "stroke_width": 0.1}


@recipe("Prime harmonics 2:3:5:7")
def _primes(r):
    return {"steps": [single(
        "harmonograph",
        freq1=2, freq2=3 + r.jitter(0.01), freq3=5, freq4=7 + r.jitter(0.006),
        amp1=100, amp2=80, amp3=60, amp4=50,
        phase1=0, phase2=90, phase3=r.f(17, 40), phase4=r.f(86, 143),
        decay1=r.f(0.003, 0.005), decay2=r.f(0.002, 0.004),
        decay3=r.f(0.004, 0.006), decay4=r.f(0.003, 0.005),
        duration=60, cycles=1)], "stroke_width": 0.1}


@recipe("Beat pattern — extreme detuning")
def _beats(r):
    base = r.pick([2, 3])
    return {"steps": [single(
        "harmonograph",
        freq1=base, freq2=base + r.f(0.03, 0.07),
        freq3=base + 1, freq4=base + 1 + r.f(0.04, 0.08),
        amp1=100, amp2=80, amp3=60, amp4=40,
        phase1=0, phase2=90, phase3=r.f(29, 86), phase4=r.f(115, 172),
        decay1=r.f(0.001, 0.003), decay2=r.f(0.002, 0.004),
        decay3=r.f(0.001, 0.002), decay4=r.f(0.001, 0.003),
        duration=r.f(80, 120), cycles=1)], "stroke_width": 0.1}


@recipe("Fast decay, spiralling in")
def _fast_decay(r):
    a, b = r.pick([(3, 2), (5, 4), (7, 5)])
    return {"steps": [single(
        "harmonograph",
        freq1=a, freq2=b + 0.005, freq3=r.pick([5, 3]),
        freq4=r.pick([7, 4]) + 0.003,
        amp1=120, amp2=100, amp3=80, amp4=60,
        phase1=0, phase2=90, phase3=29, phase4=115,
        decay1=r.f(0.015, 0.025), decay2=r.f(0.012, 0.02),
        decay3=r.f(0.02, 0.03), decay4=r.f(0.015, 0.025),
        duration=r.f(15, 30), cycles=1)], "stroke_width": 0.15}


@recipe("Butterfly — amplitude drift")
def _butterfly(r):
    a, b = r.pick([(2, 3), (3, 4), (5, 4)])
    decay = r.f(0.002, 0.005)
    return {"steps": [single(
        "harmonograph",
        freq1=a, amp1=r.f(100, 130), end_amp1=r.f(20, 40), phase1=0, decay1=decay,
        freq2=b + r.jitter(0.008), amp2=r.f(100, 130), end_amp2=r.f(40, 70),
        phase2=90, decay2=decay,
        freq3=1 + r.jitter(0.005), amp3=r.f(30, 55), end_amp3=r.f(5, 15),
        phase3=r.f(20, 60), decay3=decay,
        freq4=0, amp4=0, phase4=0, decay4=0,
        duration=r.f(80, 110), cycles=r.i(3, 5))], "stroke_width": 0.12}


@recipe("Harmonograph, turning")
def _harmonograph_rot(r):
    a, b = r.pick([(2, 3), (3, 4), (5, 4), (5, 3)])
    decay = r.f(0.004, 0.01)
    return {"steps": [
        single("harmonograph", freq1=a, amp1=100, phase1=0, decay1=decay,
               freq2=b + r.jitter(0.01), amp2=100, phase2=90, decay2=decay,
               duration=r.f(60, 90), cycles=r.i(3, 5), **QUIET),
        rot(r.pick([90, 120, 180]))], "stroke_width": 0.15}


@recipe("Fuzzy orbits — harmonograph beside a circle")
def _fuzzy_orbits(r):
    a, b = r.pick([(2, 3), (3, 4), (5, 4)])
    radius = r.pick([15, 20, 25, 30])
    cycles = r.i(15, 25) if radius < 20 else r.i(4, 8)
    return {"steps": [group(
        [mod("harmonograph", freq1=a, amp1=100, phase1=0, decay1=r.f(0.004, 0.008),
             freq2=b + 0.005, amp2=80, phase2=90, decay2=r.f(0.003, 0.006),
             duration=r.f(35, 50), cycles=1, **QUIET)],
        [mod("circle", radius=radius, cycles=cycles)])], "stroke_width": 0.12}


@recipe("Two harmonographs at once")
def _dual_harmonograph(r):
    a, b = r.pick([(2, 3), (3, 4), (5, 4)])
    c, d = r.pick([(3, 2), (4, 3), (5, 3)])
    return {"steps": [group(
        [mod("harmonograph", freq1=a, amp1=100, phase1=0, decay1=r.f(0.004, 0.008),
             freq2=b + r.jitter(0.01), amp2=90, phase2=90, decay2=r.f(0.004, 0.008),
             duration=r.f(40, 60), cycles=r.i(2, 4), **QUIET)],
        [mod("harmonograph", freq1=c, amp1=r.f(50, 70), phase1=r.f(30, 90),
             decay1=r.f(0.006, 0.012),
             freq2=d + r.jitter(0.01), amp2=r.f(50, 70), phase2=r.f(0, 60),
             decay2=r.f(0.006, 0.012),
             duration=r.f(40, 60), cycles=r.i(2, 4), **QUIET)]),
        rot(r.pick([90, 180, 270]))], "stroke_width": 0.1}


@recipe("Decay shell — harmonograph, circle and a slide")
def _decay_shell(r):
    a, b = r.pick([(2, 3), (3, 4), (5, 4)])
    return {"steps": [group(
        [mod("harmonograph", freq1=a, amp1=100, phase1=0, decay1=r.f(0.004, 0.009),
             freq2=b + 0.005, amp2=85, phase2=90, decay2=r.f(0.004, 0.009),
             duration=r.f(35, 55), cycles=r.i(2, 4), **QUIET)],
        [mod("circle", radius=r.f(15, 30), cycles=r.i(6, 14))],
        [mod("translation", start_x=0, end_x=r.f(60, 140), start_y=0, end_y=0,
             normalize=False)]),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.1}


@recipe("Harmonograph along an arc")
def _harmonograph_arc(r):
    a, b = r.pick([(3, 2), (2, 3), (5, 4), (4, 3)])
    return {"steps": [
        single("harmonograph", freq1=a, amp1=r.f(60, 80), phase1=0,
               decay1=r.f(0.006, 0.01),
               freq2=b + 0.004, amp2=r.f(60, 80), phase2=90,
               decay2=r.f(0.006, 0.01),
               duration=r.f(35, 50), cycles=r.i(2, 3), **QUIET),
        arc(r.f(160, 220), r.pick([180, 270])),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.1}


@recipe("Spiral galaxy")
def _galaxy(r):
    a, b = r.pick([(2, 3), (3, 2), (3, 4)])
    return {"steps": [
        single("harmonograph", freq1=a, amp1=r.f(40, 60), phase1=0,
               decay1=r.f(0.008, 0.015),
               freq2=b + 0.005, amp2=r.f(40, 60), phase2=90,
               decay2=r.f(0.008, 0.015),
               duration=r.f(25, 40), cycles=2, **QUIET),
        spiral_arc(r.f(15, 25), r.f(150, 200), r.pick([720, 1080, 1440]))],
        "stroke_width": 0.1}


# -- gears --------------------------------------------------------------------------- #

@recipe("Fibonacci gears")
def _fibonacci(r):
    fixed, rolling = r.pick([(233, 144), (144, 89), (89, 55)])
    return {"steps": [single(
        "spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
        tooth_pitch=r.f(0.8, 1.5), hole_position=r.f(0.7, 0.9),
        inside=True, cycles=1)], "stroke_width": 0.12}


@recipe("Classic gears, chosen for their common divisor")
def _classic_gear(r):
    fixed = r.pick([96, 105, 120, 144])
    candidates = [n for n in (24, 30, 32, 36, 40, 45, 48, 52, 56, 60, 63, 72)
                  if n < fixed and 3 <= _gcd(fixed, n) <= 12]
    rolling = r.pick(candidates) if candidates else 36
    return {"steps": [single(
        "spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
        tooth_pitch=r.f(4, 9), hole_position=r.f(0.55, 0.75),
        inside=True, cycles=1)], "stroke_width": 0.12}


@recipe("Concentric rings")
def _concentric(r):
    fixed = r.pick([100, 96, 120])
    rolling = r.pick([n for n in (37, 41, 43, 47) if n < fixed])
    return {"steps": [
        single("spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
               tooth_pitch=r.f(1.5, 3), hole_position=r.f(0.7, 0.9),
               inside=True, cycles=1),
        scale(1.0, r.f(0.4, 0.6)),
        rot(r.pick([90, 120, 180]))], "stroke_width": 0.12}


@recipe("Wreath — a drifting gear, bent round")
def _wreath(r):
    fixed = r.pick([96, 105, 120])
    rolling = r.pick([n for n in (36, 40, 45, 52) if n < fixed])
    return {"steps": [
        single("spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
               tooth_pitch=r.f(4, 7), hole_position=r.f(0.4, 0.55),
               end_hole_position=r.f(0.75, 0.9), inside=True, cycles=r.i(10, 20)),
        single("translation", start_x=0, end_x=r.f(150, 250), start_y=0, end_y=0,
               normalize=True),
        bend(r.f(170, 260), r.pick([180, 200, 240])),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.1}


@recipe("Gear scroll")
def _gear_scroll(r):
    return {"steps": [
        single("spirograph_gear", fixed_teeth=105, rolling_teeth=52,
               tooth_pitch=r.f(5, 8), hole_position=0.65, inside=True,
               cycles=r.i(10, 20)),
        single("translation", start_x=0, end_x=r.f(150, 250), start_y=0, end_y=0,
               normalize=True),
        rot(r.pick([90, 180, 360, 540])),
        single("spiral_shape", start_radius=5, end_radius=r.f(120, 170),
               turns=r.f(4, 6), cycles=1)], "stroke_width": 0.12}


@recipe("Hand-drawn ring — epitrochoid with noise")
def _hand_drawn_ring(r):
    return {"steps": [
        single("spirograph_gear", fixed_teeth=144,
               rolling_teeth=r.pick([55, 89, 73]), tooth_pitch=r.f(1.0, 1.8),
               hole_position=r.f(0.55, 0.75), inside=False, cycles=1),
        noise(r.f(1.5, 3.5), r.f(6, 14))], "stroke_width": 0.1}


@recipe("Epitrochoid, roughened and turned")
def _epitrochoid(r):
    fixed = r.pick([96, 105, 120, 144])
    rolling = r.pick([n for n in (36, 40, 45, 52, 55) if n < fixed])
    return {"steps": [
        single("spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
               tooth_pitch=r.f(1.0, 2.5), hole_position=r.f(0.55, 0.75),
               inside=False, cycles=1),
        noise(r.f(1.5, 3), r.f(6, 12)),
        rot(r.pick([90, 180, 360]))], "stroke_width": 0.1}


@recipe("Gear, deep chain")
def _gear_deep(r):
    fixed = r.pick([96, 100, 120])
    rolling = r.pick([n for n in (37, 41, 43, 47) if n < fixed])
    return {"steps": [
        single("spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
               tooth_pitch=r.f(1.5, 4), hole_position=r.f(0.65, 0.85),
               inside=True, cycles=1),
        noise(r.f(1, 2.5), r.f(8, 15)),
        rot(r.pick([120, 180, 270])),
        damp(r.f(0.008, 0.015), r.f(40, 60))], "stroke_width": 0.1}


@recipe("Gear and polygon together")
def _gear_polygon(r):
    fixed = r.pick([96, 105, 120])
    rolling = r.pick([n for n in (36, 40, 45, 52) if n < fixed])
    return {"steps": [group(
        [mod("spirograph_gear", fixed_teeth=fixed, rolling_teeth=rolling,
             tooth_pitch=r.f(3, 6), hole_position=r.f(0.55, 0.75),
             inside=True, cycles=1)],
        [mod("polygon", sides=r.pick([5, 6, 7, 8]), radius=r.f(30, 55),
             rotation=0, cycles=r.i(2, 4))]),
        rot(r.pick([90, 180, 270]))], "stroke_width": 0.1}


# -- lissajous, ellipses, roses ------------------------------------------------------- #

@recipe("Nautilus mesh")
def _nautilus(r):
    a, b = r.pick([(5, 6), (7, 8), (9, 8), (7, 6), (5, 4)])
    return {"steps": [
        single("lissajous", freq_x=a, freq_y=b, amplitude_x=r.f(100, 140),
               amplitude_y=r.f(100, 140), phase=r.f(40, 80), cycles=r.i(2, 4)),
        scale(1.0, r.f(0.2, 0.4)),
        rot(r.pick([120, 180, 270]))], "stroke_width": 0.1}


@recipe("Lissajous, high ratio")
def _lissajous_high(r):
    a, b = r.pick([(6, 5), (7, 8), (9, 8), (8, 7), (7, 6)])
    return {"steps": [
        single("lissajous", freq_x=a, freq_y=b, amplitude_x=r.f(100, 140),
               amplitude_y=r.f(100, 140), phase=r.f(30, 80), cycles=r.i(2, 4)),
        noise(r.f(1, 2.5), r.f(8, 14))], "stroke_width": 0.1}


@recipe("Lissajous, damped and stretched")
def _lissajous_damped(r):
    a, b = r.pick([(5, 4), (7, 6), (4, 3), (9, 8)])
    return {"steps": [
        single("lissajous", freq_x=a, freq_y=b, amplitude_x=r.f(90, 130),
               amplitude_y=r.f(90, 130), phase=r.f(40, 75), cycles=r.i(2, 4)),
        damp(r.f(0.008, 0.015), r.f(40, 60)),
        stretch(r.f(1.3, 2.0), 1.0)], "stroke_width": 0.12}


@recipe("Lens — an ellipse swapping its axes")
def _lens(r):
    rx, ry = r.f(140, 200), r.f(20, 40)
    return {"steps": [
        single("ellipse", radius_x=rx, radius_y=ry, end_radius_x=ry,
               end_radius_y=rx, cycles=r.i(100, 180), rotation=r.f(0, 90)),
        damp(r.f(0.01, 0.02), r.f(40, 70)),
        rot(r.pick([120, 180, 270]))], "stroke_width": 0.12}


@recipe("Ellipse, turning")
def _ellipse_rot(r):
    return {"steps": [
        single("ellipse", radius_x=r.f(100, 170), radius_y=r.f(60, 120),
               end_radius_x=r.f(25, 55), end_radius_y=r.f(15, 40),
               cycles=r.i(80, 180), rotation=r.f(0, 60)),
        rot(r.pick([90, 120, 180, 270, 360]))], "stroke_width": 0.1}


@recipe("Ellipse up a spiral")
def _ellipse_spiral(r):
    return {"steps": [
        single("ellipse", radius_x=r.f(40, 70), radius_y=r.f(25, 45),
               end_radius_x=r.f(15, 30), end_radius_y=r.f(10, 20),
               cycles=r.i(60, 120), rotation=r.f(0, 45)),
        spiral_arc(r.f(15, 25), r.f(140, 200), r.pick([720, 1080, 1440]))],
        "stroke_width": 0.1}


@recipe("Ellipse, deep chain")
def _ellipse_deep(r):
    return {"steps": [
        single("ellipse", radius_x=r.f(100, 160), radius_y=r.f(60, 100),
               end_radius_x=r.f(30, 60), end_radius_y=r.f(20, 40),
               cycles=r.i(80, 150), rotation=r.f(0, 60)),
        bend(r.f(180, 260), r.pick([120, 180, 200])),
        rot(r.pick([120, 180, 270])),
        noise(r.f(1, 3), r.f(6, 12))], "stroke_width": 0.08}


@recipe("Rose")
def _rose(r):
    petals, denom = r.pick([(5, 3), (7, 3), (7, 4), (8, 3), (5, 2)])
    return {"steps": [
        single("rose", k_num=petals, k_den=denom, radius=r.f(100, 140), cycles=1),
        rot(r.pick([36, 45, 60, 72]))],
        "stroke_width": 0.15, "symmetry": r.pick([0, 0, 3, 5]) or None}


@recipe("Rose, roughened")
def _rose_noise(r):
    petals, denom = r.pick([(5, 2), (7, 3), (8, 3), (5, 3), (7, 4)])
    return {"steps": [
        single("rose", k_num=petals, k_den=denom, radius=r.f(100, 140),
               cycles=r.i(2, 4)),
        noise(r.f(2, 4), r.f(6, 12)),
        damp(r.f(0.01, 0.02), r.f(40, 60))], "stroke_width": 0.12}


# -- surfaces --------------------------------------------------------------------------- #

@recipe("Trefoil — a surface, turning")
def _trefoil(r):
    kind = r.pick(["torus", "figure8", "mobius", "klein"])
    return {"steps": [
        single("klein_bottle" if kind == "klein" else kind, surface=kind,
               major_radius=r.f(100, 150), v_lines=r.i(30, 60),
               **({"width": r.f(40, 80)} if kind == "mobius"
                  else {"minor_radius": r.f(35, 65)}),
               view_angle_x=r.f(20, 50), view_angle_y=r.f(10, 40),
               view_angle_z=r.f(-15, 15)),
        rot(360)], "stroke_width": 0.12}


@recipe("Klein bottle mesh")
def _klein(r):
    return {"steps": [
        single("klein_bottle", surface="klein", major_radius=r.f(80, 120),
               minor_radius=r.f(30, 50), v_lines=r.i(40, 60),
               view_angle_x=r.f(25, 45), view_angle_y=r.f(15, 35)),
        rot(360)], "stroke_width": 0.1}


@recipe("Klein bottle, damped up a spiral")
def _klein_spiral(r):
    return {"steps": [
        single("klein_bottle", surface="klein", major_radius=r.f(80, 120),
               minor_radius=r.f(30, 50), v_lines=r.i(35, 55),
               view_angle_x=r.f(25, 45), view_angle_y=r.f(15, 35)),
        damp(r.f(0.008, 0.015), r.f(35, 55)),
        spiral_arc(r.f(20, 35), r.f(150, 200), r.pick([360, 720]))],
        "stroke_width": 0.1}


@recipe("Figure-eight torus")
def _figure8(r):
    return {"steps": [
        single("figure8", surface="figure8", major_radius=r.f(90, 130),
               minor_radius=r.f(30, 50), v_lines=r.i(35, 55),
               view_angle_x=r.f(15, 40), view_angle_y=r.f(5, 25)),
        rot(360)], "stroke_width": 0.1}


@recipe("Figure-eight, stretched")
def _figure8_stretch(r):
    return {"steps": [
        single("figure8", surface="figure8", major_radius=r.f(90, 130),
               minor_radius=r.f(30, 50), v_lines=r.i(35, 55),
               view_angle_x=r.f(15, 40), view_angle_y=r.f(5, 25)),
        stretch(r.f(1.5, 2.5), r.f(0.8, 1.0))], "stroke_width": 0.1}


@recipe("Torus, stretched across the sheet")
def _torus_wide(r):
    return {"steps": [
        single("torus", surface="torus", major_radius=r.f(90, 130),
               minor_radius=r.f(30, 55), v_lines=r.i(35, 55),
               view_angle_x=r.f(20, 45), view_angle_y=r.f(10, 35)),
        stretch(r.f(1.8, 3.0), 1.0)], "stroke_width": 0.1}


@recipe("Möbius, shrinking")
def _mobius(r):
    return {"steps": [
        single("mobius", surface="mobius", major_radius=r.f(100, 140),
               width=r.f(40, 70), v_lines=r.i(35, 55),
               view_angle_x=r.f(30, 50), view_angle_y=r.f(15, 30)),
        scale(1.0, r.f(0.3, 0.5)),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.1}


@recipe("Helix ribbon — a chain of circles")
def _helix_ribbon(r):
    return {"steps": [
        single("helix_ribbon", surface="helix_ribbon", major_radius=r.f(80, 120),
               width=r.f(30, 50), twists=r.pick([1, 2, 3]), v_lines=r.i(30, 50),
               view_angle_x=r.f(25, 40), view_angle_y=r.f(15, 30)),
        rot(360)], "stroke_width": 0.12}


@recipe("Ribbon, turning")
def _ribbon(r):
    return {"steps": [
        single("ribbon", surface="ribbon", major_radius=r.f(90, 130),
               width=r.f(40, 60), twists=r.pick([2, 3, 4]), v_lines=r.i(35, 50),
               view_angle_x=r.f(25, 40), view_angle_y=r.f(10, 25)),
        rot(360)], "stroke_width": 0.1}


@recipe("Sphere along an arc")
def _sphere(r):
    return {"steps": [
        single("sphere", surface="sphere", major_radius=r.f(50, 80),
               v_lines=r.i(25, 40)),
        arc(r.f(150, 220), r.pick([180, 270])),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.12}


# -- guilloche --------------------------------------------------------------------------- #

@recipe("Guilloche — the banknote pattern")
def _guilloche(r):
    return {"steps": [single(
        "guilloche", inner=r.f(50, 100), outer=r.f(160, 250),
        nodes=r.i(80, 170), div=r.pick(PRIMES),
        n0=r.i(4, 12), h0=r.f(5, 25), n1=r.i(8, 20), h1=r.f(8, 30))],
        "stroke_width": 0.08}


@recipe("Guilloche with a drifting envelope")
def _guilloche_drift(r):
    return {"steps": [single(
        "guilloche", inner=r.f(40, 80), end_inner=r.f(90, 130),
        outer=r.f(200, 260), end_outer=r.f(150, 200),
        nodes=r.i(100, 160), div=r.pick(PRIMES[:12]),
        n0=r.i(5, 10), h0=r.f(8, 18), n1=r.i(10, 18), h1=r.f(10, 22))],
        "stroke_width": 0.08}


@recipe("Guilloche, deep chain")
def _guilloche_deep(r):
    return {"steps": [
        single("guilloche", inner=r.f(50, 90), outer=r.f(170, 240),
               nodes=r.i(90, 160), div=r.pick([13, 17, 23, 29, 37, 41, 47, 53, 59, 67, 71]),
               n0=r.i(4, 10), h0=r.f(6, 20), n1=r.i(8, 18), h1=r.f(8, 25)),
        damp(r.f(0.008, 0.02), r.f(30, 60)),
        scale(1.0, r.f(0.4, 0.7)),
        noise(r.f(1, 3), r.f(6, 12))], "stroke_width": 0.1}


@recipe("Guilloche, stretched and turned")
def _guilloche_stretch(r):
    return {"steps": [
        single("guilloche", inner=r.f(60, 100), outer=r.f(160, 220),
               nodes=r.i(100, 150), div=r.pick([17, 23, 31, 37, 41, 53, 71]),
               n0=r.i(5, 8), h0=r.f(8, 15), n1=r.i(10, 16), h1=r.f(10, 20)),
        stretch(r.f(1.5, 2.5), 1.0),
        rot(r.pick([90, 180, 270, 360]))], "stroke_width": 0.08}


@recipe("Guilloche, shrinking")
def _guilloche_scale(r):
    return {"steps": [
        single("guilloche", inner=r.f(50, 90), outer=r.f(170, 240),
               nodes=r.i(80, 150), div=r.pick([17, 23, 31, 37, 41, 53, 59, 67, 71]),
               n0=r.i(4, 10), h0=r.f(6, 18), n1=r.i(8, 16), h1=r.f(8, 22)),
        scale(1.0, r.f(0.4, 0.7)),
        rot(r.pick([120, 180, 270, 360]))], "stroke_width": 0.08}


@recipe("Guilloche, ellipse and polygon at once")
def _guilloche_group(r):
    return {"steps": [group(
        [mod("guilloche", inner=r.f(40, 70), outer=r.f(130, 180),
             nodes=r.i(60, 100), div=r.pick([17, 23, 31, 37, 41, 53]),
             n0=r.i(3, 7), h0=r.f(5, 12), n1=r.i(6, 12), h1=r.f(6, 15))],
        [mod("ellipse", radius_x=r.f(50, 80), radius_y=r.f(30, 55),
             end_radius_x=r.f(15, 30), end_radius_y=r.f(10, 25),
             cycles=r.i(40, 80), rotation=0)],
        [mod("polygon", sides=r.pick([5, 6, 7, 8]), radius=r.f(30, 50),
             rotation=0, cycles=r.i(2, 4))])], "stroke_width": 0.1}


# -- racks, rails, lines, stars, polygons -------------------------------------------------- #

@recipe("Cloud lobes — a rack, bent")
def _rack_bend(r):
    return {"steps": [
        single("rack", gear_teeth=r.i(25, 40), tooth_pitch=r.f(4, 7),
               hole_position=r.f(0.6, 0.8), straight_teeth=r.i(30, 60),
               cycles=r.i(2, 4)),
        bend(r.f(170, 230), r.pick([180, 200, 240])),
        rot(r.pick([180, 270]))], "stroke_width": 0.15}


@recipe("Rack, bent and turned")
def _rack_bend_rot(r):
    return {"steps": [
        single("rack", gear_teeth=r.i(20, 40), tooth_pitch=r.f(4, 8),
               hole_position=r.f(0.6, 0.8), straight_teeth=r.i(30, 60),
               cycles=r.i(2, 5)),
        bend(r.f(150, 250), r.pick([180, 200, 240])),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.12}


@recipe("Rack up a spiral")
def _rack_spiral(r):
    return {"steps": [
        single("rack", gear_teeth=r.i(25, 40), tooth_pitch=r.f(3, 6),
               hole_position=r.f(0.55, 0.75), straight_teeth=r.i(25, 50),
               cycles=r.i(3, 5)),
        spiral_arc(r.f(20, 35), r.f(150, 200), r.pick([720, 1080]))],
        "stroke_width": 0.1}


@recipe("Rail along an arc")
def _rail_arc(r):
    return {"steps": [
        single("spirograph_rail", gear_teeth=r.i(25, 45), tooth_pitch=r.f(3, 6),
               hole_position=r.f(0.55, 0.8), rail_length=r.f(200, 400),
               cycles=r.i(1, 3)),
        arc(r.f(150, 250), r.pick([180, 270])),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.12}


@recipe("Rail, stretched wide")
def _rail_wide(r):
    return {"steps": [
        single("spirograph_rail", gear_teeth=r.i(30, 50), tooth_pitch=r.f(3, 5),
               hole_position=r.f(0.6, 0.8), rail_length=r.f(250, 400),
               cycles=r.i(1, 3)),
        stretch(r.f(1.5, 2.5), r.f(0.8, 1.2)),
        rot(r.pick([90, 180]))], "stroke_width": 0.1}


@recipe("Polygon up a spiral")
def _polygon_spiral(r):
    return {"steps": [
        single("polygon", sides=r.pick([5, 6, 7, 8]), radius=r.f(30, 50),
               rotation=0, cycles=r.i(3, 5)),
        spiral_arc(r.f(15, 25), r.f(140, 180), r.pick([720, 1080]))],
        "stroke_width": 0.12}


@recipe("Polygon spiral, roughened")
def _polygon_noise(r):
    return {"steps": [
        single("polygon", sides=r.pick([5, 6, 7, 8]), radius=r.f(25, 45),
               rotation=0, cycles=r.i(3, 6)),
        spiral_arc(r.f(15, 25), r.f(140, 180), r.pick([720, 1080, 1440])),
        noise(r.f(1, 2), r.f(8, 14))], "stroke_width": 0.1}


@recipe("Star beside a harmonograph")
def _star_harmonograph(r):
    a, b = r.pick([(3, 2), (2, 3), (5, 4)])
    return {"steps": [group(
        [mod("star_shape", points=r.pick([5, 6, 7]), outer_radius=r.f(50, 70),
             inner_radius=r.f(15, 30), rotation=0, cycles=2)],
        [mod("harmonograph", freq1=a, amp1=r.f(80, 100), phase1=0,
             decay1=r.f(0.005, 0.008),
             freq2=b + 0.005, amp2=r.f(80, 100), phase2=90,
             decay2=r.f(0.005, 0.008), duration=60, cycles=3, **QUIET)]),
        rot(r.pick([90, 120]))], "stroke_width": 0.12}


@recipe("Shrinking star spiral")
def _star_spiral(r):
    return {"steps": [
        single("star_shape", points=r.pick([5, 6, 7, 8, 9]),
               outer_radius=r.f(100, 150), inner_radius=r.f(25, 55),
               rotation=0, cycles=r.i(3, 5)),
        scale(1.3, r.f(0.2, 0.4)),
        rot(r.pick([270, 360, 540]))], "stroke_width": 0.12}


@recipe("Star, deep chain")
def _star_deep(r):
    return {"steps": [
        single("star_shape", points=r.pick([5, 7, 8]), outer_radius=r.f(50, 80),
               inner_radius=r.f(15, 30), rotation=0, cycles=r.i(2, 4)),
        arc(r.f(150, 220), r.pick([180, 270])),
        noise(r.f(1.5, 3), r.f(6, 10)),
        damp(r.f(0.01, 0.02), r.f(30, 50))], "stroke_width": 0.1}


@recipe("Star beside an ellipse")
def _star_ellipse(r):
    return {"steps": [group(
        [mod("star_shape", points=r.pick([5, 6, 7, 8]), outer_radius=r.f(60, 100),
             inner_radius=r.f(20, 40), rotation=0, cycles=r.i(2, 4))],
        [mod("ellipse", radius_x=r.f(80, 130), radius_y=r.f(50, 90),
             end_radius_x=r.f(20, 45), end_radius_y=r.f(15, 35),
             cycles=r.i(60, 120), rotation=r.f(0, 45))]),
        rot(r.pick([90, 120, 180]))], "stroke_width": 0.1}


@recipe("Textured spiral from a line")
def _line_spiral(r):
    return {"steps": [
        single("line", length=r.f(80, 180), rotation=0, cycles=r.i(2, 4)),
        spiral_arc(r.f(15, 25), r.f(140, 180), r.pick([720, 1080, 1440])),
        noise(r.f(2, 5), r.f(4, 8))], "stroke_width": 0.12}


@recipe("Line, bent and turned")
def _line_bend(r):
    return {"steps": [
        single("line", length=r.f(100, 250), rotation=r.f(0, 30), cycles=r.i(2, 5)),
        bend(r.f(120, 250), r.pick([120, 180, 240, 270])),
        rot(r.pick([180, 270, 360]))], "stroke_width": 0.12}


@recipe("Line, deep chain")
def _line_deep(r):
    return {"steps": [
        single("line", length=r.f(80, 180), rotation=0, cycles=r.i(2, 4)),
        damp(r.f(0.008, 0.018), r.f(30, 55)),
        stretch(r.f(1.2, 2.0), r.f(0.8, 1.2)),
        spiral_arc(r.f(15, 25), r.f(140, 190), r.pick([720, 1080])),
        noise(r.f(1, 3), r.f(6, 10))], "stroke_width": 0.1}


@recipe("Spiral, roughened")
def _spiral_noise(r):
    return {"steps": [
        single("spiral_shape", start_radius=r.f(3, 8), end_radius=r.f(120, 180),
               turns=r.f(4, 8), cycles=1),
        noise(r.f(3, 8), r.f(4, 10)),
        rot(r.pick([180, 360, 540]))], "stroke_width": 0.12}


# -- picking one ------------------------------------------------------------------------- #

def names():
    return [fn.recipe_name for fn in RECIPES]


def slug(name, words=2):
    """A short filename-ish stem from a recipe's name.

    "Torus, stretched across the sheet" -> "torus_stretched". The full name is
    shown in the panel; this only has to be short, lowercase and distinct
    enough to tell two placed patterns apart on the sheet.
    """
    # Fold accents away first: the slug becomes a filename, and "möbius" is
    # fine on this filesystem but not on every one a file might travel to.
    folded = unicodedata.normalize("NFKD", name.split("\u2014")[0])
    cleaned = "".join(c.lower() if (c.isalnum() or c.isspace()) else " "
                      for c in folded if not unicodedata.combining(c))
    parts = [w for w in cleaned.split()
             if w not in ("a", "an", "the", "and", "of", "at", "in", "on",
                          "with", "from", "beside", "against", "up", "once")]
    return "_".join(parts[:words]) or "pattern"


def random_pattern(rng=None, avoid=(), index=None):
    """One pattern, as the pieces a Document needs.

    ``avoid`` is a list of recently used indices — the button keeps the last
    forty so that pressing it repeatedly explores rather than circles. When
    everything has been used recently the constraint is dropped rather than
    returning nothing.

    Returns ``{index, name, steps, symmetry, output}``.
    """
    r = _Rand(rng)
    if index is None:
        choices = [i for i in range(len(RECIPES)) if i not in set(avoid)]
        index = r.pick(choices or range(len(RECIPES)))
    builder = RECIPES[index]
    made = builder(r)

    fold = made.get("symmetry")
    if not fold:
        # Most patterns are better for a fold or two, but not all of them, and
        # a pattern that is already symmetric gains nothing from more.
        fold = r.pick([3, 4, 5, 6, 8]) if r.chance(0.45) else 1
    symmetry = ({"n_fold": fold, "mirror": bool(fold > 1 and r.chance(0.4))}
                if fold > 1 else {})

    return {"index": index, "name": builder.recipe_name,
            "slug": slug(builder.recipe_name), "steps": made["steps"],
            "symmetry": symmetry,
            "output": {"stroke_width": made.get("stroke_width", 0.12)}}
