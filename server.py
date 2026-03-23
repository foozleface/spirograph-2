"""
FastAPI server for the Spirograph-2 modular pattern generator.
Wraps the existing INI-config pipeline to expose:
  - GET  /api/modules       — list available module types + params
  - GET  /api/examples      — list example INI configs
  - POST /api/generate      — generate SVG from JSON config
  - GET  /                  — React frontend
"""
import configparser
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any

# Ensure spirograph-2 modules are importable
SPIRO_DIR = Path(__file__).parent
sys.path.insert(0, str(SPIRO_DIR))

app = FastAPI(title="Spirograph-2")


# --------------------------------------------------------------------------- #
# Module registry: type -> {param: default}
# --------------------------------------------------------------------------- #
MODULE_DEFS = {
    "spirograph_gear": {
        "category": "generator",
        "label": "Spirograph Gear",
        "desc": "Classic two-gear spirograph (hypotrochoid / epitrochoid)",
        "params": {
            "fixed_teeth":       {"type": "int",   "default": 96,   "min": 10,  "max": 300, "desc": "Fixed gear teeth"},
            "rolling_teeth":     {"type": "int",   "default": 36,   "min": 5,   "max": 200, "desc": "Rolling gear teeth"},
            "tooth_pitch":       {"type": "float", "default": 1.0,  "min": 0.1, "max": 5.0, "step": 0.1, "desc": "Size per tooth"},
            "end_tooth_pitch":   {"type": "float", "default": 1.0,  "min": 0.1, "max": 5.0, "step": 0.1, "desc": "End value", "drift_for": "tooth_pitch"},
            "hole_position":     {"type": "float", "default": 0.7,  "min": 0.0, "max": 1.5, "step": 0.05, "desc": "Pen hole (0=center, 1=edge)"},
            "end_hole_position": {"type": "float", "default": 0.7,  "min": 0.0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "inside":            {"type": "bool",  "default": True,  "desc": "Inside (hypo) vs outside (epi)"},
            "cycles":            {"type": "float", "default": 1.0,  "min": 1,   "max": 50, "step": 1, "desc": "Repetitions"},
        },
    },
    "harmonograph": {
        "category": "generator",
        "label": "Harmonograph",
        "desc": "Pendulum drawing simulator (2-4 pendulums)",
        "params": {
            "freq1":  {"type": "float", "default": 2.0,   "min": 0.1, "max": 10, "step": 0.1, "desc": "Pendulum 1 freq"},
            "amp1":   {"type": "float", "default": 100.0, "min": 1,   "max": 200, "desc": "Pendulum 1 amp"},
            "end_amp1": {"type": "float", "default": 100.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp1"},
            "phase1": {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Pendulum 1 phase°"},
            "decay1": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 1 decay"},
            "freq2":  {"type": "float", "default": 3.0,   "min": 0.1, "max": 10, "step": 0.1, "desc": "Pendulum 2 freq"},
            "amp2":   {"type": "float", "default": 100.0, "min": 1,   "max": 200, "desc": "Pendulum 2 amp"},
            "end_amp2": {"type": "float", "default": 100.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp2"},
            "phase2": {"type": "float", "default": 90.0,  "min": 0,   "max": 360, "desc": "Pendulum 2 phase°"},
            "decay2": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 2 decay"},
            "freq3":  {"type": "float", "default": 0.0,   "min": 0,   "max": 10, "step": 0.1, "desc": "Pendulum 3 freq (0=off)"},
            "amp3":   {"type": "float", "default": 0.0,   "min": 0,   "max": 200, "desc": "Pendulum 3 amp"},
            "end_amp3": {"type": "float", "default": 0.0, "min": 0, "max": 200, "desc": "End value", "drift_for": "amp3"},
            "phase3": {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Pendulum 3 phase°"},
            "decay3": {"type": "float", "default": 0.0,   "min": 0,   "max": 0.1, "step": 0.005, "desc": "Pendulum 3 decay"},
            "duration": {"type": "float", "default": 60.0, "min": 10, "max": 200, "desc": "Simulation duration"},
            "cycles":   {"type": "float", "default": 1.0,  "min": 1, "max": 10, "step": 1, "desc": "Repetitions"},
        },
    },
    "lissajous": {
        "category": "generator",
        "label": "Lissajous",
        "desc": "Oscilloscope-style frequency ratio patterns",
        "params": {
            "freq_x":          {"type": "int",   "default": 3,    "min": 1, "max": 12, "desc": "X frequency"},
            "freq_y":          {"type": "int",   "default": 2,    "min": 1, "max": 12, "desc": "Y frequency"},
            "amplitude_x":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "X amplitude"},
            "end_amplitude_x": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "amplitude_x"},
            "amplitude_y":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "Y amplitude"},
            "end_amplitude_y": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "amplitude_y"},
            "phase":           {"type": "float", "default": 90.0, "min": 0, "max": 360, "desc": "Phase offset°"},
            "end_phase":       {"type": "float", "default": 90.0, "min": 0, "max": 360, "desc": "End value", "drift_for": "phase"},
            "cycles":          {"type": "float", "default": 0,    "min": 0, "max": 20, "step": 1, "desc": "Cycles (0=auto)"},
        },
    },
    "rose": {
        "category": "generator",
        "label": "Rose Curve",
        "desc": "Rhodonea petal patterns: r = cos(k·θ)",
        "params": {
            "k_num":      {"type": "int",   "default": 3,    "min": 1, "max": 12, "desc": "k numerator"},
            "k_den":      {"type": "int",   "default": 1,    "min": 1, "max": 8,  "desc": "k denominator"},
            "radius":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "Petal radius"},
            "end_radius": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "radius"},
            "cycles":     {"type": "float", "default": 0,    "min": 0, "max": 20, "step": 1, "desc": "Cycles (0=auto)"},
        },
    },
    "circle": {
        "category": "generator",
        "label": "Circle",
        "desc": "Simple circle with optional animation",
        "params": {
            "radius":     {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "Radius"},
            "end_radius": {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "radius"},
            "sweep":      {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Sweep \u00b1"},
            "sweep_n":    {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Sweep per rev"},
            "cycles":     {"type": "float", "default": 1.0,  "min": 1,  "max": 500, "step": 1, "desc": "Repetitions"},
        },
    },
    "polygon": {
        "category": "generator",
        "label": "Polygon",
        "desc": "Regular polygon (triangle, square, hex, ...)",
        "params": {
            "sides":      {"type": "int",   "default": 5,    "min": 3, "max": 20, "desc": "Number of sides"},
            "radius":     {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "Radius"},
            "end_radius": {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End value", "drift_for": "radius"},
            "cycles":     {"type": "float", "default": 1.0,  "min": 1, "max": 50, "step": 1, "desc": "Repetitions"},
            "rotation":       {"type": "float", "default": 0.0,  "min": 0, "max": 360, "desc": "Rotation°"},
            "end_rotation":   {"type": "float", "default": 0.0,  "min": 0, "max": 360, "desc": "End value", "drift_for": "rotation"},
        },
    },
    "star_shape": {
        "category": "generator",
        "label": "Star",
        "desc": "Pointed star with inner/outer vertices",
        "params": {
            "points":           {"type": "int",   "default": 5,    "min": 3,  "max": 20, "desc": "Points"},
            "outer_radius":     {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "Outer radius"},
            "end_outer_radius": {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "outer_radius"},
            "inner_radius":     {"type": "float", "default": 19.1, "min": 1,  "max": 200, "desc": "Inner radius"},
            "end_inner_radius": {"type": "float", "default": 19.1, "min": 1,  "max": 200, "desc": "End value", "drift_for": "inner_radius"},
            "cycles":           {"type": "float", "default": 1.0,  "min": 1,  "max": 50, "step": 1, "desc": "Repetitions"},
            "rotation":         {"type": "float", "default": -90,  "min": -180, "max": 180, "desc": "Rotation°"},
            "end_rotation":     {"type": "float", "default": -90,  "min": -180, "max": 180, "desc": "End value", "drift_for": "rotation"},
        },
    },
    "spiral_shape": {
        "category": "generator",
        "label": "Spiral",
        "desc": "Archimedean spiral (linear radius growth)",
        "params": {
            "start_radius": {"type": "float", "default": 0.0,  "min": 0, "max": 100, "desc": "Start radius"},
            "end_radius":   {"type": "float", "default": 50.0, "min": 5, "max": 200, "desc": "End radius"},
            "turns":        {"type": "float", "default": 3.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Turns"},
            "cycles":       {"type": "float", "default": 1.0,  "min": 1, "max": 10, "step": 1, "desc": "Repetitions"},
        },
    },
    "guilloche": {
        "category": "generator",
        "label": "Guilloche",
        "desc": "Engine-turning pattern (banknote/certificate style)",
        "params": {
            "inner":     {"type": "float", "default": 60.0,  "min": 5,   "max": 200, "desc": "Inner radius"},
            "end_inner": {"type": "float", "default": 60.0,  "min": 5,   "max": 200, "desc": "End value", "drift_for": "inner"},
            "outer":     {"type": "float", "default": 180.0, "min": 20,  "max": 400, "desc": "Outer radius"},
            "end_outer": {"type": "float", "default": 180.0, "min": 20,  "max": 400, "desc": "End value", "drift_for": "outer"},
            "nodes":     {"type": "float", "default": 120.0, "min": 10,  "max": 300, "desc": "Wave oscillations"},
            "end_nodes": {"type": "float", "default": 120.0, "min": 10,  "max": 300, "desc": "End value", "drift_for": "nodes"},
            "div":       {"type": "int",   "default": 37,    "min": 7,   "max": 97,  "desc": "Overlap (use primes)"},
            "n0":        {"type": "float", "default": 6.0,   "min": 0,   "max": 30,  "desc": "Inner envelope waves"},
            "h0":        {"type": "float", "default": 10.0,  "min": 0,   "max": 50,  "desc": "Inner envelope amp"},
            "n1":        {"type": "float", "default": 12.0,  "min": 0,   "max": 30,  "desc": "Outer envelope waves"},
            "h1":        {"type": "float", "default": 15.0,  "min": 0,   "max": 50,  "desc": "Outer envelope amp"},
            "cycles":    {"type": "float", "default": 1.0,   "min": 1,   "max": 10,  "step": 1, "desc": "Cycles"},
        },
    },
    "rotation": {
        "category": "transform",
        "label": "Rotation",
        "desc": "Spin pattern around center as it draws",
        "params": {
            "total_degrees": {"type": "float", "default": 360.0, "min": 0, "max": 3600, "desc": "Total rotation°"},
            "origin_x":      {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Origin X"},
            "origin_y":      {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Origin Y"},
            "normalize":     {"type": "bool",  "default": True,   "desc": "Normalize timing"},
        },
    },
    "scale": {
        "category": "transform",
        "label": "Scale",
        "desc": "Grow/shrink pattern over time",
        "params": {
            "start_scale": {"type": "float", "default": 1.0, "min": 0.01, "max": 5, "step": 0.1, "desc": "Start scale"},
            "end_scale":   {"type": "float", "default": 1.0, "min": 0.01, "max": 5, "step": 0.1, "desc": "End value", "drift_for": "start_scale"},
            "normalize":   {"type": "bool",  "default": True, "desc": "Normalize timing"},
        },
    },
    "translation": {
        "category": "transform",
        "label": "Translation",
        "desc": "Slide pattern along a line as it draws",
        "params": {
            "start_x":  {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Start X"},
            "end_x":    {"type": "float", "default": 100.0, "min": -200, "max": 200, "desc": "End value", "drift_for": "start_x"},
            "start_y":  {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "Start Y"},
            "end_y":    {"type": "float", "default": 0.0,   "min": -200, "max": 200, "desc": "End value", "drift_for": "start_y"},
            "normalize": {"type": "bool", "default": True,  "desc": "Normalize timing"},
        },
    },
    "arc": {
        "category": "transform",
        "label": "Arc Path",
        "desc": "Slide pattern along circular arc",
        "params": {
            "radius":      {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Arc radius"},
            "start_angle": {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Start angle°"},
            "sweep_angle": {"type": "float", "default": 180.0, "min": 10, "max": 720, "desc": "Sweep°"},
            "cycles":      {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
            "normalize":   {"type": "bool",  "default": True,  "desc": "Normalize timing"},
        },
    },
    "spiral_arc": {
        "category": "transform",
        "label": "Spiral Path",
        "desc": "Slide pattern along spiral path",
        "params": {
            "inner_radius": {"type": "float", "default": 20.0,  "min": 0,  "max": 200, "desc": "Inner radius"},
            "outer_radius": {"type": "float", "default": 160.0, "min": 10, "max": 300, "desc": "Outer radius"},
            "start_angle":  {"type": "float", "default": 0.0,   "min": 0,  "max": 360, "desc": "Start angle°"},
            "sweep_angle":  {"type": "float", "default": 720.0, "min": 10, "max": 2880, "desc": "Sweep°"},
            "normalize":    {"type": "bool",  "default": True,   "desc": "Normalize timing"},
        },
    },
    "torus": {
        "category": "generator",
        "label": "Torus",
        "desc": "3D torus (donut shape)",
        "params": {
            "surface":      {"type": "str", "default": "torus", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Tube radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "mobius": {
        "category": "generator",
        "label": "Mobius Strip",
        "desc": "Single-sided twisted strip",
        "params": {
            "surface":      {"type": "str", "default": "mobius", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "width":        {"type": "float", "default": 60.0,  "min": 5,  "max": 200, "desc": "Strip width"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 30.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 15.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "klein_bottle": {
        "category": "generator",
        "label": "Klein Bottle",
        "desc": "Non-orientable surface (self-intersecting)",
        "params": {
            "surface":      {"type": "str", "default": "klein", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Body radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Neck radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 30.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "sphere": {
        "category": "generator",
        "label": "Sphere",
        "desc": "3D sphere wireframe",
        "params": {
            "surface":      {"type": "str", "default": "sphere", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "figure8": {
        "category": "generator",
        "label": "Figure-8 Torus",
        "desc": "Self-intersecting figure-8 torus",
        "params": {
            "surface":      {"type": "str", "default": "figure8", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Tube radius"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "ribbon": {
        "category": "generator",
        "label": "Twisted Ribbon",
        "desc": "Ribbon with configurable twists",
        "params": {
            "surface":      {"type": "str", "default": "ribbon", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Ring radius"},
            "width":        {"type": "float", "default": 60.0,  "min": 5,  "max": 200, "desc": "Ribbon width"},
            "twists":       {"type": "float", "default": 2.0,   "min": 0,  "max": 8, "step": 0.5, "desc": "Half-twists"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 25.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 10.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "helix_ribbon": {
        "category": "generator",
        "label": "Helix Ribbon",
        "desc": "Rising helical ribbon",
        "params": {
            "surface":      {"type": "str", "default": "helix_ribbon", "hidden": True},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Helix radius"},
            "width":        {"type": "float", "default": 40.0,  "min": 5,  "max": 200, "desc": "Ribbon width"},
            "twists":       {"type": "float", "default": 1.0,   "min": 0,  "max": 8, "step": 0.5, "desc": "Half-twists"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 30.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 15.0,  "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
        "_module": "surface",
    },
    "line": {
        "category": "generator",
        "label": "Line",
        "desc": "Straight lines with timing control",
        "params": {
            "length":      {"type": "float", "default": 100.0, "min": 1,   "max": 500, "desc": "Length"},
            "end_length":  {"type": "float", "default": 100.0, "min": 1,   "max": 500, "desc": "End value", "drift_for": "length"},
            "cycles":      {"type": "float", "default": 1.0,   "min": 1,   "max": 50, "step": 1, "desc": "Cycles"},
            "stroke_time": {"type": "float", "default": 1.0,   "min": 0.01, "max": 1, "step": 0.01, "desc": "Stroke time (0-1)"},
            "rotation":    {"type": "float", "default": 0.0,   "min": 0,   "max": 360, "desc": "Direction"},
        },
    },
    "ellipse": {
        "category": "generator",
        "label": "Ellipse",
        "desc": "Oval with independent X/Y radii",
        "params": {
            "radius_x":     {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "Radius X"},
            "end_radius_x": {"type": "float", "default": 50.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "radius_x"},
            "radius_y":     {"type": "float", "default": 30.0, "min": 5,  "max": 200, "desc": "Radius Y"},
            "end_radius_y": {"type": "float", "default": 30.0, "min": 5,  "max": 200, "desc": "End value", "drift_for": "radius_y"},
            "rotation":     {"type": "float", "default": 0.0,  "min": 0,  "max": 360, "desc": "Rotation"},
            "end_rotation": {"type": "float", "default": 0.0,  "min": 0,  "max": 360, "desc": "End value", "drift_for": "rotation"},
            "sweep":        {"type": "float", "default": 0.0,  "min": -100, "max": 100, "step": 1, "desc": "Sweep \u00b1"},
            "sweep_n":      {"type": "float", "default": 1.0,  "min": 0.5, "max": 20, "step": 0.5, "desc": "Sweep per rev"},
            "cycles":       {"type": "float", "default": 1.0,  "min": 1,  "max": 500, "step": 1, "desc": "Cycles"},
        },
    },
    "rack": {
        "category": "generator",
        "label": "Rack",
        "desc": "Gear rolling around stadium-shaped track",
        "params": {
            "straight_teeth": {"type": "int",   "default": 50,   "min": 5,  "max": 200, "desc": "Straight teeth"},
            "end_teeth":      {"type": "int",   "default": 24,   "min": 5,  "max": 100, "desc": "End curve teeth"},
            "gear_teeth":     {"type": "int",   "default": 24,   "min": 5,  "max": 100, "desc": "Gear teeth"},
            "tooth_pitch":    {"type": "float", "default": 2.0,  "min": 0.1, "max": 5, "step": 0.1, "desc": "Tooth pitch"},
            "hole_position":  {"type": "float", "default": 0.75, "min": 0, "max": 1.5, "step": 0.05, "desc": "Pen hole"},
            "end_hole_position": {"type": "float", "default": 0.75, "min": 0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "laps":           {"type": "int",   "default": 1,    "min": 1, "max": 20, "desc": "Laps"},
            "cycles":         {"type": "float", "default": 1.0,  "min": 1, "max": 20, "step": 1, "desc": "Cycles"},
            "scale":          {"type": "float", "default": 1.0,  "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
        },
    },
    "spirograph_rail": {
        "category": "generator",
        "label": "Rail",
        "desc": "Gear rolling along linear rail",
        "params": {
            "rail_length":   {"type": "float", "default": 200.0, "min": 10, "max": 500, "desc": "Rail length"},
            "gear_teeth":    {"type": "int",   "default": 40,    "min": 5,  "max": 100, "desc": "Gear teeth"},
            "tooth_pitch":   {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Tooth pitch"},
            "hole_position": {"type": "float", "default": 0.6,   "min": 0, "max": 1.5, "step": 0.05, "desc": "Pen hole"},
            "end_hole_position": {"type": "float", "default": 0.6, "min": 0, "max": 1.5, "step": 0.05, "desc": "End value", "drift_for": "hole_position"},
            "passes":        {"type": "int",   "default": 2,     "min": 1, "max": 20, "desc": "Passes"},
            "cycles":        {"type": "float", "default": 1.0,   "min": 1, "max": 20, "step": 1, "desc": "Cycles"},
            "rail_angle":    {"type": "float", "default": 0.0,   "min": 0, "max": 360, "desc": "Rail angle"},
        },
    },
    "bend": {
        "category": "transform",
        "label": "Bend",
        "desc": "Wrap flat pattern into arc (X to angle, Y to radius)",
        "params": {
            "radius":      {"type": "float", "default": 200.0, "min": 10,  "max": 500, "desc": "Bend radius"},
            "start_angle": {"type": "float", "default": 0.0,   "min": -180, "max": 360, "desc": "Start angle"},
            "sweep_angle": {"type": "float", "default": 90.0,  "min": 10,  "max": 720, "desc": "Sweep"},
        },
    },
    "damping": {
        "category": "transform",
        "label": "Damping",
        "desc": "Exponential decay toward center",
        "params": {
            "decay_rate":     {"type": "float", "default": 0.02, "min": 0, "max": 0.2, "step": 0.005, "desc": "Decay rate"},
            "end_decay_rate": {"type": "float", "default": 0.02, "min": 0, "max": 0.2, "step": 0.005, "desc": "End value", "drift_for": "decay_rate"},
            "duration":       {"type": "float", "default": 60.0, "min": 1, "max": 200, "desc": "Duration"},
        },
    },
    "noise": {
        "category": "transform",
        "label": "Noise",
        "desc": "Smooth random perturbation (hand-drawn look)",
        "params": {
            "amplitude":     {"type": "float", "default": 5.0,  "min": 0.1, "max": 50, "desc": "Amplitude"},
            "end_amplitude": {"type": "float", "default": 5.0,  "min": 0,   "max": 50, "desc": "End value", "drift_for": "amplitude"},
            "frequency":     {"type": "float", "default": 50.0, "min": 1,   "max": 500, "desc": "Frequency"},
            "seed":          {"type": "int",   "default": 42,   "min": 0,   "max": 9999, "desc": "Seed"},
        },
    },
    "stretch": {
        "category": "transform",
        "label": "Stretch",
        "desc": "Non-uniform X/Y scaling — elongate along either axis",
        "params": {
            "scale_x":     {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "X scale"},
            "end_scale_x": {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "End value", "drift_for": "scale_x"},
            "scale_y":     {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "Y scale"},
            "end_scale_y": {"type": "float", "default": 1.0, "min": 0.1, "max": 10, "step": 0.1, "desc": "End value", "drift_for": "scale_y"},
        },
    },
}


# --------------------------------------------------------------------------- #
# Curated examples
# --------------------------------------------------------------------------- #
def _list_examples():
    """Return list of example INI files with metadata."""
    examples = []
    autogen = SPIRO_DIR / "claude_autogen"
    if autogen.is_dir():
        for ini in sorted(autogen.glob("*.ini")):
            text = ini.read_text()
            # first comment line as description
            desc = ""
            for line in text.splitlines():
                if line.startswith("#") or line.startswith(";"):
                    desc = line.lstrip("#; ").strip()
                    break
            svg = ini.with_suffix(".svg")
            examples.append({
                "name": ini.stem.replace("_", " ").title(),
                "file": ini.name,
                "desc": desc,
                "has_svg": svg.exists(),
            })
    return examples


# --------------------------------------------------------------------------- #
# API endpoints
# --------------------------------------------------------------------------- #

@app.get("/api/modules")
def api_modules():
    return MODULE_DEFS


@app.get("/api/examples")
def api_examples():
    return _list_examples()


@app.get("/api/example/{filename}")
def api_example_config(filename: str):
    """Return the raw INI text for an example."""
    path = SPIRO_DIR / "claude_autogen" / filename
    if not path.exists() or not path.suffix == ".ini":
        raise HTTPException(404, "Example not found")
    return {"ini": path.read_text()}


@app.get("/api/example-svg/{filename}")
def api_example_svg(filename: str):
    """Return pre-rendered SVG for an example."""
    svg_name = Path(filename).stem + ".svg"
    path = SPIRO_DIR / "claude_autogen" / svg_name
    if not path.exists():
        # Also check root dir
        path = SPIRO_DIR / svg_name
    if not path.exists():
        raise HTTPException(404, "SVG not found")
    return Response(content=path.read_text(), media_type="image/svg+xml")


class GenerateRequest(BaseModel):
    steps: list[dict[str, Any]] = []  # [{kind:'single',params:{...}}, {kind:'group',params:[{...},...]}]
    pipeline: list[dict[str, Any]] = []  # legacy single flat pipeline
    arms: list[list[dict[str, Any]]] = []  # legacy parallel arms
    global_mods: list[dict[str, Any]] = []
    output: dict[str, Any] = {}
    sampling: dict[str, Any] = {}
    symmetry: dict[str, Any] = {}


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    """Generate SVG from a JSON pipeline definition."""
    try:
        ini = _build_ini(req)
        svg = _run_pipeline(ini)
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


class GenerateIniRequest(BaseModel):
    ini: str


@app.post("/api/generate-ini")
def api_generate_ini(req: GenerateIniRequest):
    """Generate SVG from raw INI text."""
    try:
        svg = _run_pipeline(req.ini)
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/api/generate-points")
def api_generate_points(req: GenerateRequest):
    """Generate point arrays as JSON for canvas rendering."""
    try:
        ini = _build_ini(req)
        normalized, cfg = _run_pipeline_points(ini)
        # Convert complex arrays to [[x,y], ...] lists
        paths = []
        for pts in normalized:
            paths.append([[round(float(p.real), 2), round(float(p.imag), 2)] for p in pts])
        return {
            "paths": paths,
            "config": cfg,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.get("/api/ini-files")
def api_ini_files():
    """List all .ini files in the project directory and subdirectories."""
    skip_dirs = {".git", ".venv", "node_modules", "__pycache__", "output"}
    files = []
    for ini in sorted(SPIRO_DIR.rglob("*.ini")):
        rel = ini.relative_to(SPIRO_DIR)
        # Skip hidden/venv/output dirs
        if any(part in skip_dirs or part.startswith(".") for part in rel.parts[:-1]):
            continue
        folder = str(rel.parent) if rel.parent != Path(".") else ""
        files.append({"path": str(rel), "dir": folder})
    return files


@app.get("/api/load-ini")
def api_load_ini(path: str):
    """Load an .ini file by relative path. Returns INI text + parsed pipeline info."""
    resolved = (SPIRO_DIR / path).resolve()
    if not str(resolved).startswith(str(SPIRO_DIR.resolve())):
        raise HTTPException(403, "Path outside project directory")
    if not resolved.exists() or resolved.suffix != ".ini":
        raise HTTPException(404, "INI file not found")
    ini_text = resolved.read_text()

    # Parse out pipeline info for display
    config = configparser.ConfigParser()
    config.read_string(ini_text)

    def _parse_mod_section(cfg, name):
        """Parse a single module section into {type, params}."""
        mod_type = name
        params = {}
        if cfg.has_section(name):
            if cfg.has_option(name, "type"):
                mod_type = cfg.get(name, "type").strip()
            for k, v in cfg.items(name):
                if k in ("type", "modules"):
                    continue
                if v.lower() in ("true", "false"):
                    params[k] = v.lower() == "true"
                else:
                    try:
                        params[k] = int(v)
                    except ValueError:
                        try:
                            params[k] = float(v)
                        except ValueError:
                            params[k] = v
        # Map surface module to specific UI type based on 'surface' param
        if mod_type == "surface" and "surface" in params:
            surface_to_ui = {"torus":"torus","mobius":"mobius","klein":"klein_bottle",
                             "sphere":"sphere","figure8":"figure8","ribbon":"ribbon","helix_ribbon":"helix_ribbon"}
            mod_type = surface_to_ui.get(params["surface"], "torus")
        return {"section_name": name, "type": mod_type, "params": params}

    pipeline_modules = []
    if config.has_section("pipeline"):
        mod_names = [m.strip() for m in config.get("pipeline", "modules", fallback="").split(",") if m.strip()]
        for name in mod_names:
            mod_type = name
            if config.has_section(name) and config.has_option(name, "type"):
                mod_type = config.get(name, "type").strip()

            if mod_type == "group":
                # Parse group branches: "a, b | c, d"
                modules_str = config.get(name, "modules", fallback="")
                branch_strs = modules_str.split("|")
                branches = []
                for branch_str in branch_strs:
                    branch_names = [m.strip() for m in branch_str.split(",") if m.strip()]
                    branch_mods = [_parse_mod_section(config, n) for n in branch_names]
                    branches.append(branch_mods)
                pipeline_modules.append({
                    "section_name": name, "type": "group", "branches": branches, "params": {}
                })
            else:
                pipeline_modules.append(_parse_mod_section(config, name))

    # Extract output/sampling/symmetry
    output_cfg = {}
    if config.has_section("output"):
        for k, v in config.items("output"):
            try: output_cfg[k] = float(v)
            except ValueError: output_cfg[k] = v

    sampling_cfg = {}
    if config.has_section("sampling"):
        for k, v in config.items("sampling"):
            try: sampling_cfg[k] = float(v)
            except ValueError:
                if v.lower() in ("true", "false"): sampling_cfg[k] = v.lower() == "true"
                else: sampling_cfg[k] = v

    symmetry_cfg = {}
    if config.has_section("symmetry"):
        for k, v in config.items("symmetry"):
            if v.lower() in ("true", "false"): symmetry_cfg[k] = v.lower() == "true"
            else:
                try: symmetry_cfg[k] = int(v)
                except ValueError: symmetry_cfg[k] = v

    return {
        "ini": ini_text,
        "filename": path,
        "pipeline": pipeline_modules,
        "output": output_cfg,
        "sampling": sampling_cfg,
        "symmetry": symmetry_cfg,
    }


from fastapi import Query


class SaveRequest(BaseModel):
    filename: str
    steps: list[dict[str, Any]] = []
    output: dict[str, Any] = {}
    sampling: dict[str, Any] = {}
    symmetry: dict[str, Any] = {}


@app.post("/api/save")
def api_save(req: SaveRequest):
    """Save current pipeline as an INI file."""
    # Sanitize filename
    name = req.filename.strip()
    if not name:
        raise HTTPException(400, "Filename required")
    if not name.endswith(".ini"):
        name += ".ini"
    # Allow subdirectories but prevent path traversal
    resolved = (SPIRO_DIR / name).resolve()
    if not str(resolved).startswith(str(SPIRO_DIR.resolve())):
        raise HTTPException(403, "Path outside project directory")
    # Ensure parent directory exists
    resolved.parent.mkdir(parents=True, exist_ok=True)

    # Build INI using same logic as generate
    gen_req = GenerateRequest(
        steps=req.steps, output=req.output, sampling=req.sampling,
        symmetry=req.symmetry,
    )
    ini_text = _build_ini(gen_req)
    resolved.write_text(ini_text)

    # Also generate and save SVG alongside
    try:
        svg = _run_pipeline(ini_text)
        resolved.with_suffix(".svg").write_text(svg)
    except Exception:
        pass  # SVG generation failure shouldn't block save

    return {"saved": name}


@app.get("/api/file-exists")
def api_file_exists(name: str):
    """Check if an INI file already exists."""
    if not name.endswith(".ini"):
        name += ".ini"
    resolved = (SPIRO_DIR / name).resolve()
    if not str(resolved).startswith(str(SPIRO_DIR.resolve())):
        return {"exists": False}
    return {"exists": resolved.exists()}


# --------------------------------------------------------------------------- #
# AxiDraw Plotter
# --------------------------------------------------------------------------- #

# AxiDraw model definitions: model_id -> (label, width_inches, height_inches)
AXIDRAW_MODELS = {
    1: {"label": "AxiDraw V3/SE A4", "width": 11.81, "height": 8.58},
    2: {"label": "AxiDraw V3/A3", "width": 16.93, "height": 11.69},
    3: {"label": "AxiDraw V3 XLX", "width": 23.42, "height": 8.58},
    4: {"label": "AxiDraw SE/A2", "width": 23.39, "height": 17.01},
    5: {"label": "AxiDraw SE/A1", "width": 34.02, "height": 23.39},
}

_plotter_status = {"plotting": False, "progress": 0.0, "message": "", "error": ""}


class PlotRequest(BaseModel):
    steps: list[dict[str, Any]] = []
    pipeline: list[dict[str, Any]] = []
    arms: list[list[dict[str, Any]]] = []
    global_mods: list[dict[str, Any]] = []
    output: dict[str, Any] = {}
    sampling: dict[str, Any] = {}
    symmetry: dict[str, Any] = {}
    # AxiDraw settings
    model: int = 3
    port: str = ""
    penDownSpeed: int = 25
    penUpSpeed: int = 75
    accelFactor: int = 75
    constSpeed: bool = False
    penUpPosition: int = 60
    penDownPosition: int = 30
    penLiftRate: int = 150
    penLowerRate: int = 150
    penLiftDelay: int = 0
    penLowerDelay: int = 0
    resolution: int = 1
    margin: float = 0.0
    autoRotate: bool = True
    copies: int = 1
    copyDelay: int = 15
    preview: bool = False
    # Canvas transforms
    cv_offset_x: float = 0.0
    cv_offset_y: float = 0.0
    cv_rotation: float = 0.0
    cv_scale: float = 1.0


@app.get("/api/plotter-models")
def api_plotter_models():
    return AXIDRAW_MODELS


@app.get("/api/plotter-status")
def api_plotter_status():
    return _plotter_status


@app.post("/api/plot")
def api_plot(req: PlotRequest):
    """Generate points and plot directly on AxiDraw."""
    if _plotter_status["plotting"]:
        raise HTTPException(409, "Plotter is already running")

    model_info = AXIDRAW_MODELS.get(req.model)
    if not model_info:
        raise HTTPException(400, f"Unknown model: {req.model}")

    # Compute drawable area in inches
    draw_w = model_info["width"] - 2 * req.margin
    draw_h = model_info["height"] - 2 * req.margin

    # Build INI and get normalized points in plotter coordinates (inches)
    gen_req = GenerateRequest(
        steps=req.steps, pipeline=req.pipeline, arms=req.arms,
        global_mods=req.global_mods, output=req.output, sampling=req.sampling,
        symmetry=req.symmetry,
    )
    ini_text = _build_ini(gen_req)

    try:
        normalized, cfg = _run_pipeline_points(ini_text, target_width=draw_w, target_height=draw_h)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Pipeline error: {e}")

    # Apply canvas transforms (rotation, scale, offset) then convert to inch coordinates
    import numpy as np
    cx_draw, cy_draw = draw_w / 2, draw_h / 2  # center of drawable area
    rot_rad = np.radians(req.cv_rotation)
    cos_r, sin_r = np.cos(rot_rad), np.sin(rot_rad)
    sc = req.cv_scale
    off_x = req.cv_offset_x * draw_w  # offset as inches
    off_y = req.cv_offset_y * draw_h

    segments = []
    for pts in normalized:
        # Translate to center, scale+rotate, translate back, apply offset
        centered = pts - complex(cx_draw, cy_draw)
        rotated = (centered.real * cos_r - centered.imag * sin_r) + 1j * (centered.real * sin_r + centered.imag * cos_r)
        scaled = rotated * sc
        final = scaled + complex(cx_draw + off_x, cy_draw + off_y)
        coords = [(float(p.real) + req.margin,
                    float(p.imag) + req.margin) for p in final]
        segments.append(coords)

    total_points = sum(len(s) for s in segments)
    if total_points == 0:
        raise HTTPException(400, "No points generated")

    # Plot in a background thread
    import threading

    def _plot_thread():
        _plotter_status.update(plotting=True, progress=0.0, message="Connecting...", error="")
        try:
            from pyaxidraw import axidraw
            ad = axidraw.AxiDraw()
            ad.interactive()
            ad.options.model = req.model
            ad.options.speed_pendown = req.penDownSpeed
            ad.options.speed_penup = req.penUpSpeed
            ad.options.pen_pos_up = req.penUpPosition
            ad.options.pen_pos_down = req.penDownPosition
            ad.options.accel = req.accelFactor
            ad.options.const_speed = req.constSpeed
            ad.options.auto_rotate = req.autoRotate
            if req.port:
                ad.options.port = req.port

            if not ad.connect():
                _plotter_status.update(plotting=False, error="Failed to connect to AxiDraw")
                return

            _plotter_status["message"] = f"Plotting {total_points} points in {len(segments)} segments..."
            points_done = 0

            for seg_idx, seg in enumerate(segments):
                if len(seg) < 2:
                    continue
                # Move to start of segment (pen up)
                ad.moveto(seg[0][0], seg[0][1])
                # Draw segment (pen down via lineto)
                for x, y in seg[1:]:
                    ad.lineto(x, y)
                    points_done += 1
                    if points_done % 500 == 0:
                        _plotter_status["progress"] = points_done / total_points
                        _plotter_status["message"] = f"Segment {seg_idx+1}/{len(segments)} — {int(100*points_done/total_points)}%"
                # Pen up after segment
                ad.penup()

            # Return home
            _plotter_status["message"] = "Returning home..."
            ad.moveto(0, 0)
            ad.disconnect()
            _plotter_status.update(plotting=False, progress=1.0, message="Done!", error="")

        except ImportError:
            _plotter_status.update(plotting=False, error="pyaxidraw not installed. Run: pip install https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip")
        except Exception as e:
            traceback.print_exc()
            _plotter_status.update(plotting=False, error=str(e))

    threading.Thread(target=_plot_thread, daemon=True).start()
    return {"status": "started", "total_points": total_points, "segments": len(segments)}


@app.post("/api/plot-stop")
def api_plot_stop():
    """Emergency stop."""
    _plotter_status.update(plotting=False, message="Stopped", error="Stop requested")
    return {"status": "stopped"}


class ManualCommand(BaseModel):
    command: str
    model: int = 3
    port: str = ""
    penUpPosition: int = 60
    penDownPosition: int = 30
    walkDistance: float = 1.0


@app.post("/api/plot-manual")
def api_plot_manual(cmd: ManualCommand):
    """Send a manual command to the AxiDraw."""
    if _plotter_status["plotting"]:
        raise HTTPException(409, "Plotter is busy")
    try:
        from pyaxidraw import axidraw
        ad = axidraw.AxiDraw()
        ad.interactive()
        ad.options.model = cmd.model
        ad.options.pen_pos_up = cmd.penUpPosition
        ad.options.pen_pos_down = cmd.penDownPosition
        if cmd.port:
            ad.options.port = cmd.port
        if not ad.connect():
            raise HTTPException(503, "Failed to connect to AxiDraw")
        if cmd.command == "pen_up":
            ad.penup()
        elif cmd.command == "pen_down":
            ad.pendown()
        elif cmd.command == "toggle_pen":
            # Toggle: try lowering; if already down, raise
            ad.pendown()
        elif cmd.command == "home":
            ad.penup()
            ad.moveto(0, 0)
        elif cmd.command == "enable_motors":
            ad.moveto(0, 0)  # moveto enables motors
        elif cmd.command == "disable_motors":
            pass  # disconnect below releases motors
        elif cmd.command == "walk_x":
            ad.move(cmd.walkDistance, 0)
        elif cmd.command == "walk_y":
            ad.move(0, cmd.walkDistance)
        ad.disconnect()
        return {"status": "ok", "command": cmd.command}
    except ImportError:
        raise HTTPException(500, "pyaxidraw not installed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.delete("/api/delete-ini")
def api_delete_ini(path: str = Query(...)):
    """Delete an .ini file and its associated .svg if present."""
    resolved = (SPIRO_DIR / path).resolve()
    if not str(resolved).startswith(str(SPIRO_DIR.resolve())):
        raise HTTPException(403, "Path outside project directory")
    if not resolved.exists() or resolved.suffix != ".ini":
        raise HTTPException(404, "INI file not found")
    resolved.unlink()
    # Also remove associated SVG if it exists
    svg_path = resolved.with_suffix(".svg")
    if svg_path.exists():
        svg_path.unlink()
    return {"deleted": path}


# Map UI type names to Python module names where they differ
_TYPE_TO_MODULE = {
    "torus": "surface", "mobius": "surface", "klein_bottle": "surface",
    "sphere": "surface", "figure8": "surface", "ribbon": "surface", "helix_ribbon": "surface",
}

def _emit_mod(lines, section_name, mod_params):
    """Emit a single module's INI section."""
    lines.append(f"[{section_name}]")
    for k, v in mod_params.items():
        if k == "type" and v in _TYPE_TO_MODULE:
            lines.append(f"type = {_TYPE_TO_MODULE[v]}")
        elif isinstance(v, bool):
            lines.append(f"{k} = {'true' if v else 'false'}")
        else:
            lines.append(f"{k} = {v}")
    lines.append("")


def _build_ini(req: GenerateRequest) -> str:
    """Convert JSON pipeline definition to INI text."""
    lines = []
    pipeline_names = []
    mod_counter = 0

    # New steps-based format
    if req.steps:
        for si, step in enumerate(req.steps):
            kind = step.get("kind", "single")
            if kind == "single":
                name = f"s{si}"
                _emit_mod(lines, name, step["params"])
                pipeline_names.append(name)
            elif kind == "group":
                group_name = f"grp_{si}"
                branches = step.get("branches", [])
                # Legacy flat format: step["params"] is a flat list
                if not branches and "params" in step and isinstance(step["params"], list):
                    branches = [[p] for p in step["params"]]
                branch_name_lists = []
                for bi, branch in enumerate(branches):
                    branch_names = []
                    for mi, mod_params in enumerate(branch):
                        sub_name = f"grp{si}_b{bi}_m{mi}"
                        _emit_mod(lines, sub_name, mod_params)
                        branch_names.append(sub_name)
                    branch_name_lists.append(', '.join(branch_names))
                lines.append(f"[{group_name}]")
                lines.append("type = group")
                lines.append(f"modules = {' | '.join(branch_name_lists)}")
                lines.append("")
                pipeline_names.append(group_name)

    # Legacy: arms format
    elif req.arms and len(req.arms) > 0:
        has_groups = len(req.arms) > 1
        if has_groups:
            for a, arm in enumerate(req.arms):
                group_name = f"arm_{a}"
                sub_names = []
                for i, mod in enumerate(arm):
                    sub_name = f"arm{a}_mod{i}"
                    _emit_mod(lines, sub_name, mod)
                    sub_names.append(sub_name)
                lines.append(f"[{group_name}]")
                lines.append("type = group")
                lines.append(f"modules = {', '.join(sub_names)}")
                lines.append("")
                pipeline_names.append(group_name)
        else:
            for i, mod in enumerate(req.arms[0]):
                name = f"mod_{i}"
                _emit_mod(lines, name, mod)
                pipeline_names.append(name)
        for i, mod in enumerate(req.global_mods):
            name = f"global_{i}"
            _emit_mod(lines, name, mod)
            pipeline_names.append(name)

    # Legacy: flat pipeline
    elif req.pipeline:
        for i, mod in enumerate(req.pipeline):
            name = f"mod_{i}"
            _emit_mod(lines, name, mod)
            pipeline_names.append(name)

    lines.insert(0, "")
    lines.insert(0, f"modules = {', '.join(pipeline_names)}")
    lines.insert(0, "[pipeline]")

    # Output
    out = {"width": 800, "height": 800, "stroke_width": 0.3,
           "stroke_color": "#000000", "background_color": "#ffffff",
           "margin": 0.08, "filename": "/dev/null"}
    out.update(req.output)
    lines.append("[output]")
    for k, v in out.items():
        lines.append(f"{k} = {v}")
    lines.append("")

    # Sampling
    samp = {"initial_samples": 80000, "output_samples": 12000, "use_arc_length": "true"}
    samp.update(req.sampling)
    lines.append("[sampling]")
    for k, v in samp.items():
        lines.append(f"{k} = {v}")
    lines.append("")

    # Symmetry
    if req.symmetry:
        lines.append("[symmetry]")
        for k, v in req.symmetry.items():
            lines.append(f"{k} = {v}")
        lines.append("")

    return "\n".join(lines)


def _run_pipeline_points(ini_text: str, target_width: float = None, target_height: float = None):
    """Run the spirograph pipeline from INI text and return normalized point arrays + config.

    If target_width/target_height are given, normalization uses those dimensions instead of
    the INI's output width/height (useful for plotter output in physical units).

    Returns (normalized_point_arrays, config_dict) where config_dict has output settings.
    """
    import importlib
    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    from main import (
        TransformModule, load_module, compute_pipeline_period,
        run_single_pipeline, normalize_all_for_svg, generate_svg,
        expand_moire_config
    )

    config = configparser.ConfigParser()
    config.read_string(ini_text)

    expand_moire_config(config)

    width = config.getfloat("output", "width", fallback=800)
    height = config.getfloat("output", "height", fallback=800)
    margin = config.getfloat("output", "margin", fallback=0.08)
    stroke_width = config.getfloat("output", "stroke_width", fallback=0.3)
    stroke_color = config.get("output", "stroke_color", fallback="#000000")
    bg_color = config.get("output", "background_color", fallback="#ffffff")
    close_path = config.getboolean("output", "close_path", fallback=False)

    initial_samples = config.getint("sampling", "initial_samples", fallback=80000)
    output_samples = config.getint("sampling", "output_samples", fallback=12000)
    use_arc = config.getboolean("sampling", "use_arc_length", fallback=True)
    scroll_repeats = config.getfloat("sampling", "scroll_repeats", fallback=1.0)

    start_x = config.getfloat("output", "start_x", fallback=0.0)
    start_y = config.getfloat("output", "start_y", fallback=0.0)
    start_point = start_x + 1j * start_y

    n_fold = config.getint("symmetry", "n_fold", fallback=1) if config.has_section("symmetry") else 1
    mirror = config.getboolean("symmetry", "mirror", fallback=False) if config.has_section("symmetry") else False

    # Detect layers
    layer_sections = [s for s in config.sections() if s.startswith("layer.")]
    all_path_arrays = []

    if layer_sections:
        for section in layer_sections:
            layer_name = section.split(".", 1)[1]
            module_names = [m.strip() for m in config.get(section, "modules").split(",")]
            li = config.getint(section, "initial_samples", fallback=initial_samples)
            lo = config.getint(section, "output_samples", fallback=output_samples)
            la = config.getboolean(section, "use_arc_length", fallback=use_arc)
            ls = config.getfloat(section, "scroll_repeats", fallback=scroll_repeats)
            pts = run_single_pipeline(config, module_names, li, lo, la, start_point, label=layer_name, scroll_repeats=ls)
            all_path_arrays.append(pts)
    else:
        module_names = [m.strip() for m in config.get("pipeline", "modules").split(",")]
        pts = run_single_pipeline(config, module_names, initial_samples, output_samples,
                                  use_arc, start_point, scroll_repeats=scroll_repeats)
        all_path_arrays.append(pts)

    # Pen lift
    if config.has_section("pen_lift"):
        from pen_lift import apply_pen_lift
        lifted = []
        for pts in all_path_arrays:
            lifted.extend(apply_pen_lift(pts, config))
        all_path_arrays = lifted

    # Symmetry
    if n_fold > 1 or mirror:
        from symmetry import apply_symmetry
        expanded = []
        cx = config.getfloat("symmetry", "center_x", fallback=0.0) if config.has_section("symmetry") else 0.0
        cy = config.getfloat("symmetry", "center_y", fallback=0.0) if config.has_section("symmetry") else 0.0
        for pts in all_path_arrays:
            expanded.extend(apply_symmetry(pts, n_fold, mirror, cx, cy))
        all_path_arrays = expanded

    norm_w = target_width if target_width else width
    norm_h = target_height if target_height else height
    normalized, actual_w, actual_h = normalize_all_for_svg(all_path_arrays, norm_w, norm_h, margin)

    cfg = dict(width=actual_w, height=actual_h, margin=margin, stroke_width=stroke_width,
               stroke_color=stroke_color, bg_color=bg_color, close_path=close_path)
    return normalized, cfg


def _run_pipeline(ini_text: str) -> str:
    """Run the spirograph pipeline from INI text and return SVG."""
    from main import generate_svg
    normalized, cfg = _run_pipeline_points(ini_text)

    svg = generate_svg(
        normalized[0], cfg['width'], cfg['height'], cfg['stroke_width'],
        cfg['stroke_color'], cfg['bg_color'],
        close_path=cfg['close_path'],
        extra_paths=normalized[1:] if len(normalized) > 1 else None,
        config_text=ini_text,
    )
    return svg


# --------------------------------------------------------------------------- #
# Frontend
# --------------------------------------------------------------------------- #

@app.get("/", response_class=HTMLResponse)
def index():
    return FRONTEND_HTML


FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spirograph Studio</title>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<style>
:root { --bg: #0f0f17; --sidebar: #16162a; --card: #1e1e36; --accent: #7c5cfc;
        --accent2: #e94560; --text: #e0e0e8; --muted: #888; --border: #2a2a45; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:'Inter',system-ui,sans-serif; display:flex; height:100vh; overflow:hidden; }
::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-thumb { background:#333; border-radius:3px; }

/* Sidebar */
#sidebar { width:380px; min-width:380px; background:var(--sidebar); display:flex; flex-direction:column;
           border-right:1px solid var(--border); overflow-y:auto; }
.sidebar-header { padding:16px 20px 12px; border-bottom:1px solid var(--border); }
.sidebar-header h1 { font-size:1.3rem; font-weight:700; background:linear-gradient(135deg,var(--accent),var(--accent2));
                      -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.sidebar-header p { font-size:0.75rem; color:var(--muted); margin-top:2px; }

.section { padding:12px 16px; border-bottom:1px solid var(--border); }
.section-title { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:8px; }

/* Tree: arm headers */
.arm-header { display:flex; align-items:center; gap:6px; padding:5px 8px; margin-top:4px;
              font-size:0.72rem; font-weight:700; color:var(--muted); text-transform:uppercase;
              letter-spacing:0.04em; cursor:pointer; border-radius:4px; transition:all 0.15s; }
.arm-header:hover { color:var(--text); background:rgba(255,255,255,0.03); }
.arm-header.active { color:var(--accent); }
.arm-header .arm-caret { font-size:0.55rem; transition:transform 0.15s; }
.arm-header .arm-caret.open { transform:rotate(90deg); }
.arm-header .arm-x { font-size:0.6rem; color:var(--muted); cursor:pointer; margin-left:auto; }
.arm-header .arm-x:hover { color:var(--accent2); }
.arm-body { padding-left:10px; border-left:2px solid var(--border); margin-left:10px; }
.arm-body.active-arm { border-left-color:var(--accent); }
.group-label { font-size:0.6rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--accent);
               font-weight:700; padding:3px 0; margin:2px 0; }
.group-children { padding-left:0; }
.group-add { font-size:0.65rem; color:var(--accent); cursor:pointer; padding:3px 0 3px 20px; }
.group-add:hover { text-decoration:underline; }
.drop-indicator-before { border-top:2px solid var(--accent); margin-bottom:-2px; }
.drop-indicator-after { border-bottom:2px solid var(--accent); margin-top:-2px; }
.drop-indicator-on { outline:2px solid var(--accent2); outline-offset:-2px; border-radius:4px; }
.placeholder-slot { padding:8px 12px; border:1px dashed var(--border); border-radius:6px;
                     color:var(--muted); font-size:0.72rem; text-align:center; cursor:pointer;
                     transition:all 0.15s; background:rgba(255,255,255,0.02); }
.placeholder-slot:hover { border-color:var(--accent); color:var(--accent); }
.placeholder-slot.drag-over { border-color:var(--accent); background:rgba(124,92,252,0.1); color:var(--accent); }
.global-sep { border-top:1px dashed var(--border); margin:6px 0 2px; padding-top:4px;
              font-size:0.65rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em;
              display:flex; align-items:center; gap:6px; }
.tree-add-arm { padding:3px 8px; border-radius:4px; font-size:0.68rem; font-weight:600;
                color:var(--accent); border:1px dashed var(--border); background:none;
                cursor:pointer; margin-top:4px; transition:all 0.15s; }
.tree-add-arm:hover { border-color:var(--accent); background:rgba(124,92,252,0.1); }

/* Pipeline tree */
.pipeline-area { display:flex; flex-direction:column; gap:0; min-height:36px; padding:8px 8px 8px 4px;
                 background:var(--bg); border-radius:6px; }

/* Serial steps: simple vertical chain, no tree lines */
.serial-step { margin:2px 0; }
.serial-arrow { text-align:center; color:#555; font-size:0.7rem; line-height:1; padding:1px 0; }

/* Group: tree-branching for simultaneous children */
.group-wrapper { margin:2px 0; border-left:2px solid var(--accent); padding-left:0; border-radius:0; }
.group-children { padding:2px 0; }
.tree-node { display:flex; align-items:stretch; min-height:28px; }
.tree-line { width:18px; flex-shrink:0; position:relative; }
.tree-line::before { content:''; position:absolute; left:0; top:0; bottom:50%; width:2px; background:var(--accent); }
.tree-line::after { content:''; position:absolute; left:0; top:calc(50% - 1px); width:16px; height:2px; background:var(--accent); }
.tree-node:first-child > .tree-line::before { height:0; }
.tree-node:not(:last-child) > .tree-line::before { bottom:0; }
.tree-content { flex:1; min-width:0; }

.tree-content { flex:1; min-width:0; }

/* Step row */
.pipeline-step { display:flex; align-items:center; gap:6px; padding:5px 10px; border-radius:5px;
        font-size:0.78rem; font-weight:500; cursor:grab; border:1px solid var(--border);
        background:var(--card); transition:all 0.15s; user-select:none; margin:2px 0; }
.pipeline-step:active { cursor:grabbing; }
.pipeline-step.active { border-color:var(--accent); background:rgba(124,92,252,0.15); color:#fff; }
.pipeline-step .step-label { flex:1; }
.pipeline-step .step-cat { font-size:0.6rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; }
.pipeline-step .x { font-size:0.7rem; color:var(--muted); cursor:pointer; flex-shrink:0; padding:0 2px; }
.pipeline-step .x:hover { color:var(--accent2); }
.pipeline-step .grip { color:var(--border); font-size:0.7rem; flex-shrink:0; cursor:grab; margin-right:2px; }

.pipeline-step-wrap { display:flex; align-items:center; }
.pipeline-step-wrap .pipeline-step { flex:1; }

/* Add module buttons */
.add-modules { display:flex; flex-wrap:wrap; gap:4px; }
.add-btn { padding:3px 8px; border-radius:4px; font-size:0.72rem; border:1px solid var(--border);
           background:transparent; color:var(--muted); cursor:grab; transition:all 0.15s; }
.add-btn:hover { border-color:var(--accent); color:var(--text); }
.add-btn:active { cursor:grabbing; opacity:0.6; }
.add-btn.gen { border-color:rgba(124,92,252,0.3); }
.add-btn.xfm { border-color:rgba(233,69,96,0.3); }

/* Param controls */
.param-group { margin-top:8px; }
.param-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.param-row label { font-size:0.78rem; color:var(--muted); min-width:100px; flex-shrink:0; }
.param-row input[type=range] { flex:1; accent-color:var(--accent); height:4px; min-width:60px; }
.param-row input[type=number] { width:58px; background:var(--bg); border:1px solid var(--border); color:var(--text);
                                 border-radius:4px; padding:2px 4px; font-size:0.75rem; text-align:right; flex-shrink:0; }
.param-row input[type=number]:focus { border-color:var(--accent); outline:none; }
.param-row input[type=checkbox] { accent-color:var(--accent); }
.param-row .drift-toggle { background:none; border:none; color:var(--muted); cursor:pointer; font-size:0.55rem;
                            padding:0 2px; transition:transform 0.15s, color 0.15s; flex-shrink:0; width:14px; text-align:center; }
.param-row .drift-toggle:hover { color:var(--accent); }
.param-row .drift-toggle.drift { color:var(--accent); }
.param-row .drift-toggle.osc { color:#e94560; }
.drift-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; padding-left:14px;
             border-left:2px solid var(--accent); margin-left:6px; opacity:0.85; }
.drift-row label { font-size:0.72rem; color:var(--accent); min-width:86px; flex-shrink:0; font-style:italic; cursor:pointer; }
.drift-row label:hover { color:var(--accent2); }
.drift-row input[type=range] { flex:1; accent-color:var(--accent); height:4px; min-width:40px; }
.drift-row input[type=number] { width:58px; background:var(--bg); border:1px solid var(--border); color:var(--text);
                                 border-radius:4px; padding:2px 4px; font-size:0.75rem; text-align:right; flex-shrink:0; }
.drift-row input[type=number]:focus { border-color:var(--accent); outline:none; }

/* Output settings */
.output-row { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
.output-row label { font-size:0.75rem; color:var(--muted); min-width:80px; }
.output-row input[type=color] { width:32px; height:24px; border:none; background:none; cursor:pointer; }
.output-row input[type=number] { width:54px; background:var(--bg); border:1px solid var(--border); color:var(--text);
                                  border-radius:4px; padding:2px 4px; font-size:0.75rem; }

/* Buttons */
.btn-row { display:flex; gap:6px; padding:12px 16px; border-top:1px solid var(--border); margin-top:auto; }
.btn { flex:1; padding:10px; border:none; border-radius:6px; cursor:pointer; font-size:0.85rem; font-weight:600; transition:all 0.15s; }
.btn-generate { background:var(--accent); color:#fff; }
.btn-generate:hover { background:#6a4ae0; }
.btn-generate:disabled { opacity:0.5; cursor:wait; }
.btn-secondary { background:var(--card); color:var(--text); border:1px solid var(--border); }
.btn-secondary:hover { border-color:var(--accent); }

/* Main area */
#main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
#content-area { flex:1; display:flex; overflow:hidden; position:relative; }
#right-panel-mount { display:flex; position:relative; flex-shrink:0; }
.plotter-content { flex:1; overflow-y:auto; padding:20px; font-size:0.82rem; }
.plotter-content h3 { margin:0 0 16px; font-size:1.1rem; font-weight:700; color:var(--text); }
.plotter-content .pg { margin-bottom:18px; padding-bottom:14px; border-bottom:1px solid var(--border); }
.plotter-content .pg:last-child { border-bottom:none; }
.plotter-content .pg-title { font-weight:700; color:var(--accent); margin-bottom:8px; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.8px; }
.plotter-content label { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; color:var(--muted); font-size:0.82rem; }
.plotter-content label span { font-size:0.8rem; color:var(--text); }
.plotter-content input[type=number], .plotter-content input[type=text], .plotter-content select {
  background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:5px;
  padding:6px 10px; font-size:0.85rem; width:80px; text-align:right; }
.plotter-content input[type=number]:focus, .plotter-content input[type=text]:focus, .plotter-content select:focus {
  border-color:var(--accent); outline:none; }
.plotter-content select { width:100%; text-align:left; padding:8px 10px; }
.plotter-content input[type=checkbox] { width:18px; height:18px; accent-color:var(--accent); }
.plotter-content .p-btn { padding:8px 16px; border-radius:6px; border:1px solid var(--border);
  background:var(--bg); color:var(--text); font-size:0.82rem; cursor:pointer; font-weight:600; transition:all 0.15s; }
.plotter-content .p-btn:hover { background:rgba(124,92,252,0.15); border-color:var(--accent); }
.plotter-content .p-btn.primary { background:var(--accent); color:#fff; border-color:var(--accent); padding:10px 24px; font-size:0.9rem; }
.plotter-content .p-btn.primary:hover { opacity:0.9; }
.plotter-content .p-btn.danger { background:#c0392b; color:#fff; border-color:#c0392b; padding:10px 24px; font-size:0.9rem; }
.plotter-content .device-info { color:var(--muted); font-size:0.75rem; margin-top:6px; padding:6px 10px; background:var(--bg); border-radius:4px; }
#toolbar { display:flex; gap:8px; padding:6px 16px; border-bottom:1px solid var(--border); align-items:center; }
#toolbar .spacer { flex:1; }
#toolbar .status { font-size:0.72rem; color:var(--muted); }

#canvas-area { flex:1; display:flex; align-items:center; justify-content:center; padding:20px; overflow:hidden; position:relative; min-width:0; }
/* No max-width/max-height on canvas — JS computes exact size to prevent distortion */
#canvas-area .placeholder { color:var(--muted); font-size:0.9rem; text-align:center; }
#canvas-area .spinner-overlay { position:absolute; inset:0; display:flex; flex-direction:column;
  align-items:center; justify-content:center; background:rgba(15,15,23,0.75); z-index:10; border-radius:8px; }
.spinner { width:48px; height:48px; border:3px solid var(--border); border-top-color:var(--accent);
           border-radius:50%; animation:spin 0.8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.spinner-label { margin-top:12px; font-size:0.8rem; color:var(--muted); }


/* Right panel — tabs + collapsible content */
.right-tabs { position:absolute; right:0; top:50%; transform:translateY(-50%); z-index:20;
              display:flex; flex-direction:column; gap:4px; }
.right-tab { writing-mode:vertical-rl; text-orientation:mixed;
          background:var(--card); border:1px solid var(--border); border-right:none;
          border-radius:6px 0 0 6px; padding:12px 6px; cursor:pointer;
          font-size:0.72rem; font-weight:600; color:var(--muted); letter-spacing:0.04em;
          display:flex; align-items:center; gap:6px; transition:all 0.15s; }
.right-tab:hover { color:var(--text); background:var(--sidebar); }
.right-tab.active { color:var(--text); background:var(--sidebar); border-right-color:var(--sidebar); }
.filebrowser { width:380px; min-width:380px; background:var(--sidebar);
               border-left:1px solid var(--border); display:flex; flex-direction:column;
               overflow:hidden; }
.filebrowser.collapsed { width:0; min-width:0; border-left:none; }
.fb-header { padding:14px 16px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:10px; }
.fb-header h2 { font-size:1rem; font-weight:600; flex:1; }
.fb-header .fb-close { background:none; border:none; color:var(--muted); font-size:1.3rem; cursor:pointer;
                        width:28px; height:28px; display:flex; align-items:center; justify-content:center;
                        border-radius:4px; transition:all 0.15s; }
.fb-header .fb-close:hover { color:var(--text); background:var(--card); }
.fb-search { padding:8px 16px; border-bottom:1px solid var(--border); }
.fb-search input { width:100%; background:var(--bg); border:1px solid var(--border); color:var(--text);
                    border-radius:6px; padding:8px 12px; font-size:0.82rem; outline:none; }
.fb-search input:focus { border-color:var(--accent); }
.fb-body { flex:1; overflow-y:auto; padding:4px 0; }
.fb-group-label { padding:8px 16px 4px; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.06em;
                   color:var(--muted); font-weight:600; position:sticky; top:0; background:var(--sidebar);
                   cursor:pointer; display:flex; align-items:center; gap:6px; user-select:none; }
.fb-group-label:hover { color:var(--text); }
.fb-group-label .fb-caret { font-size:0.55rem; transition:transform 0.15s; display:inline-block; }
.fb-group-label .fb-caret.open { transform:rotate(90deg); }
.fb-row { display:flex; align-items:center; gap:8px; padding:7px 16px; transition:background 0.1s; }
.fb-row:hover { background:rgba(124,92,252,0.08); }
.fb-row .fb-icon { color:var(--accent); font-size:0.75rem; flex-shrink:0; }
.fb-row .fb-name { flex:1; font-size:0.8rem; font-weight:500; cursor:pointer; }
.fb-row .fb-name:hover { color:var(--accent); }
.fb-row .fb-dir { font-size:0.6rem; color:var(--muted); }
.fb-row .fb-load { padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:600;
                    background:var(--accent); color:#fff; border:none; cursor:pointer; flex-shrink:0; }
.fb-row .fb-load:hover { background:#6a4ae0; }
.fb-row .fb-del { padding:2px 6px; border-radius:4px; font-size:0.68rem;
                   background:none; color:var(--muted); border:1px solid var(--border); cursor:pointer; flex-shrink:0; }
.fb-row .fb-del:hover { color:var(--accent2); border-color:var(--accent2); }
.fb-empty { padding:24px 16px; color:var(--muted); font-size:0.82rem; text-align:center; }
.fb-confirm { display:flex; align-items:center; gap:6px; padding:4px 8px; background:rgba(233,69,96,0.1);
              border:1px solid var(--accent2); border-radius:4px; font-size:0.7rem; }
.fb-confirm span { color:var(--accent2); }
.fb-confirm button { padding:1px 6px; border-radius:3px; font-size:0.65rem; cursor:pointer; border:none; }
.fb-confirm .fb-yes { background:var(--accent2); color:#fff; }
.fb-confirm .fb-no { background:var(--card); color:var(--text); }
/* Tab bar */
#tab-bar { display:flex; align-items:flex-end; background:var(--sidebar); border-bottom:1px solid var(--border);
  padding:0 8px; gap:2px; min-height:32px; }
.tab-item { padding:5px 12px; font-size:0.72rem; cursor:pointer; border:1px solid transparent;
  border-bottom:none; border-radius:6px 6px 0 0; color:var(--muted); user-select:none;
  display:flex; align-items:center; gap:6px; white-space:nowrap; }
.tab-item:hover { color:var(--text); background:rgba(255,255,255,0.03); }
.tab-item.active { background:var(--bg); color:var(--text); border-color:var(--border); }
.tab-item .tab-close { font-size:0.6rem; opacity:0.3; cursor:pointer; padding:0 2px; }
.tab-item .tab-close:hover { opacity:1; color:var(--accent2); }
.tab-add { padding:5px 10px; font-size:0.8rem; cursor:pointer; color:var(--muted); user-select:none; }
.tab-add:hover { color:var(--text); }
.tab-plotter { margin-left:auto; border-left:1px solid var(--border); padding-left:8px; }
.tab-plotter.active { background:var(--bg); border-color:var(--border); color:var(--accent); }
</style>
</head>
<body>
<div id="sidebar"></div>
<div id="main">
  <div id="tab-bar"></div>
  <div id="toolbar"></div>
  <div id="content-area">
    <div id="canvas-area"><div id="canvas-sizer" style="position:absolute;inset:20px;pointer-events:none;"></div></div>
    <div id="right-panel-mount"></div>
  </div>
</div>

<script type="text/babel">
const { useState, useEffect, useCallback, useRef } = React;
const h = React.createElement;

// ---- FileRow ----
function FileRow({ f, loadIniFile, confirmDelete, setConfirmDelete, deleteIniFile }) {
  const name = f.path.replace('claude_autogen/','').replace('.ini','').replace(/_/g,' ');
  const isConfirming = confirmDelete === f.path;
  return h('div', {className:'fb-row'},
    h('span', {className:'fb-icon'}, '\u2699'),
    h('span', {className:'fb-name', onClick:()=>loadIniFile(f.path)}, name),
    isConfirming
      ? h('div', {className:'fb-confirm'},
          h('span', null, 'Delete?'),
          h('button', {className:'fb-yes', onClick:()=>deleteIniFile(f.path)}, 'Yes'),
          h('button', {className:'fb-no', onClick:()=>setConfirmDelete(null)}, 'No'),
        )
      : h('button', {className:'fb-del', onClick:()=>setConfirmDelete(f.path)}, '\u2715'),
  );
}

// ---- App ----
function App() {
  const [modules, setModules] = useState(null);  // module defs from API
  // steps: [{kind:'single', mod:{id,type,params}}, {kind:'group', branches:[[{mod},...],[{mod},...]]}]
  const [steps, setStepsRaw] = useState([]);
  const [sel, setSel] = useState(null); // {step, branch?, sub?}
  const [output, setOutputRaw] = useState({ stroke_width: 0.3, stroke_color: '#000000', background_color: '#ffffff' });
  const [symmetry, setSymmetryRaw] = useState({ n_fold: 1, mirror: false });
  const [sampling, setSamplingRaw] = useState({ scroll_repeats: 1.0, initial_samples: 80000, output_samples: 12000 });

  // Undo system — snapshot all state before each change, restore with Ctrl+Z
  // Debounced: rapid changes (slider drags) coalesce into one undo entry
  const undoStack = useRef([]);
  const skipUndo = useRef(false);
  const undoTimer = useRef(null);
  const undoPending = useRef(false);
  const stateRef = useRef({steps:[], output:{stroke_width:0.3,stroke_color:'#000000',background_color:'#ffffff'}, symmetry:{n_fold:1,mirror:false}, sampling:{scroll_repeats:1,initial_samples:80000,output_samples:12000}});
  useEffect(() => { stateRef.current = {steps, output, symmetry, sampling}; });
  const redoStack = useRef([]);
  const pushUndo = () => {
    if (skipUndo.current) return;
    // Only push if no recent push (debounce 500ms)
    if (!undoPending.current) {
      undoStack.current.push(JSON.stringify(stateRef.current));
      if (undoStack.current.length > 100) undoStack.current.shift();
      undoPending.current = true;
      // New change clears redo history
      redoStack.current.length = 0;
    }
    clearTimeout(undoTimer.current);
    undoTimer.current = setTimeout(() => { undoPending.current = false; }, 500);
  };
  const setSteps = (v) => { pushUndo(); setStepsRaw(v); };
  const setOutput = (v) => { pushUndo(); setOutputRaw(v); };
  const setSymmetry = (v) => { pushUndo(); setSymmetryRaw(v); };
  const setSampling = (v) => { pushUndo(); setSamplingRaw(v); };
  const undo = useCallback(() => {
    if (undoStack.current.length === 0) { setStatus('Nothing to undo'); return; }
    // Push current state to redo before restoring
    redoStack.current.push(JSON.stringify(stateRef.current));
    skipUndo.current = true;
    const prev = JSON.parse(undoStack.current.pop());
    setStepsRaw(prev.steps); setOutputRaw(prev.output);
    setSymmetryRaw(prev.symmetry); setSamplingRaw(prev.sampling);
    skipUndo.current = false;
    setStatus('Undo');
  }, []);
  const redo = useCallback(() => {
    if (redoStack.current.length === 0) { setStatus('Nothing to redo'); return; }
    // Push current state to undo before restoring
    undoStack.current.push(JSON.stringify(stateRef.current));
    skipUndo.current = true;
    const next = JSON.parse(redoStack.current.pop());
    setStepsRaw(next.steps); setOutputRaw(next.output);
    setSymmetryRaw(next.symmetry); setSamplingRaw(next.sampling);
    skipUndo.current = false;
    setStatus('Redo');
  }, []);
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo(); }
      if ((e.metaKey || e.ctrlKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) { e.preventDefault(); redo(); }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [undo, redo]);
  const [pointData, setPointData] = useState(null); // {paths:[[x,y],...], config:{...}}
  const canvasRef = useRef(null);
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState('');
  const idCounter = useRef(0);
  const [showFileBrowser, setShowFileBrowser] = useState(false);
  const [iniFiles, setIniFiles] = useState([]);
  const [iniSearch, setIniSearch] = useState('');
  const [loadedFile, setLoadedFile] = useState('');
  const [saveName, setSaveName] = useState('');
  const [showSave, setShowSave] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [foldersOpen, setFoldersOpen] = useState({'/': true});
  const regenFlag = useRef(false);
  const [regenTrigger, setRegenTrigger] = useState(0);
  const generateRef = useRef(null);

  // Tab system — each tab stores a snapshot; switching saves/restores
  const tabIdCounter = useRef(1);
  const [tabs, setTabs] = useState([{id:1, name:'Pattern 1'}]);
  const [activeTabId, setActiveTabId] = useState(1);
  const [plotterActive, setPlotterActive] = useState(false);
  const tabSnapshots = useRef({}); // {tabId: {steps, output, symmetry, sampling, pointData, loadedFile, cvOff, cvRot, cvScale}}

  const saveCurrentTab = () => {
    tabSnapshots.current[activeTabId] = {
      steps, output, symmetry, sampling, pointData, loadedFile,
      cvOff, cvRot, cvScale, sel,
      undoStack: [...undoStack.current], redoStack: [...redoStack.current],
    };
  };
  const restoreTab = (tabId) => {
    const snap = tabSnapshots.current[tabId];
    skipUndo.current = true;
    if (snap) {
      setStepsRaw(snap.steps); setOutputRaw(snap.output);
      setSymmetryRaw(snap.symmetry); setSamplingRaw(snap.sampling);
      setPointData(snap.pointData); setLoadedFile(snap.loadedFile);
      setCvOff(snap.cvOff); setCvRot(snap.cvRot); setCvScale(snap.cvScale);
      setSel(snap.sel);
      undoStack.current = snap.undoStack || [];
      redoStack.current = snap.redoStack || [];
    } else {
      setStepsRaw([]); setOutputRaw({stroke_width:0.3,stroke_color:'#000000',background_color:'#ffffff'});
      setSymmetryRaw({n_fold:1,mirror:false}); setSamplingRaw({scroll_repeats:1,initial_samples:80000,output_samples:12000});
      setPointData(null); setLoadedFile(''); setCvOff({x:0,y:0}); setCvRot(0); setCvScale(1); setSel(null);
      undoStack.current = []; redoStack.current = [];
    }
    skipUndo.current = false;
  };
  const switchTab = (tabId) => {
    if (tabId === activeTabId && !plotterActive) return;
    saveCurrentTab();
    setActiveTabId(tabId);
    setPlotterActive(false);
    restoreTab(tabId);
  };
  const switchToPlotter = () => {
    if (plotterActive) return;
    saveCurrentTab();
    setPlotterActive(true);
  };
  const addNewTab = () => {
    saveCurrentTab();
    const id = ++tabIdCounter.current;
    setTabs(prev => [...prev, {id, name: 'Pattern ' + id}]);
    setActiveTabId(id);
    setPlotterActive(false);
    // Clear state for new tab
    skipUndo.current = true;
    setStepsRaw([]); setOutputRaw({stroke_width:0.3,stroke_color:'#000000',background_color:'#ffffff'});
    setSymmetryRaw({n_fold:1,mirror:false}); setSamplingRaw({scroll_repeats:1,initial_samples:80000,output_samples:12000});
    setPointData(null); setLoadedFile(''); setCvOff({x:0,y:0}); setCvRot(0); setCvScale(1); setSel(null);
    undoStack.current = []; redoStack.current = [];
    skipUndo.current = false;
  };
  const closeTab = (id) => {
    if (tabs.length <= 1) return;
    delete tabSnapshots.current[id];
    const remaining = tabs.filter(t => t.id !== id);
    setTabs(remaining);
    // Remove from plotter
    setPlotterPatterns(prev => prev.filter(p => p.sourceTabId !== id));
    if (activeTabId === id) {
      const next = remaining[0];
      setActiveTabId(next.id);
      restoreTab(next.id);
    }
  };

  // Plotter composition
  const [plotterPatterns, setPlotterPatterns] = useState([]);
  const [selectedPlaced, setSelectedPlaced] = useState(null);
  const placedIdCounter = useRef(0);
  const placedDrag = useRef(null);

  const addToPlotter = () => {
    if (!pointData) return;
    const tabName = tabs.find(t => t.id === activeTabId)?.name || 'pattern';
    setPlotterPatterns(prev => {
      const existing = prev.find(p => p.sourceTabId === activeTabId);
      if (existing) {
        return prev.map(p => p.sourceTabId === activeTabId
          ? {...p, paths: pointData.paths, config: pointData.config, name: tabName}
          : p);
      }
      const id = ++placedIdCounter.current;
      const n = prev.length;
      const slotW = Math.min(30, 90 / Math.max(1, n + 1));
      return [...prev, {id, sourceTabId: activeTabId, paths: pointData.paths,
        config: pointData.config, x: n * slotW, y: 0, scale: 1.0, rotation: cvRot, name: tabName}];
    });
    setStatus('Added to plotter');
  };
  const removePlotterPattern = (id) => {
    setPlotterPatterns(prev => prev.filter(p => p.id !== id));
    if (selectedPlaced === id) setSelectedPlaced(null);
  };
  const updatePlotterPattern = (id, updates) => {
    setPlotterPatterns(prev => prev.map(p => p.id === id ? {...p, ...updates} : p));
  };
  const recentRecipes = useRef([]);
  const [driftOpen, setDriftOpen] = useState({});
  const [showPlotter, setShowPlotter] = useState(false);
  const [plotterModels, setPlotterModels] = useState({});
  const [plotterStatus, setPlotterStatus] = useState(null);
  const plotPollRef = useRef(null);
  const [pOpts, setPOpts] = useState({
    model: 3, port: '',
    penDownSpeed: 25, penUpSpeed: 75, accelFactor: 75, constSpeed: false,
    penUpPosition: 60, penDownPosition: 30,
    penLiftRate: 150, penLowerRate: 150,
    penLiftDelay: 0, penLowerDelay: 0,
    resolution: 1, margin: 0,
    autoRotate: true, copies: 1, copyDelay: 15,
    reportTime: false, preview: false,
  });
  const pSet = (k, v) => setPOpts(p => ({...p, [k]: v}));
  // Canvas transform state
  const [cvOff, setCvOff] = useState({x:0, y:0}); // offset in px
  const [cvRot, setCvRot] = useState(0); // degrees
  const [cvScale, setCvScale] = useState(1);
  const cvDrag = useRef(null); // {startX, startY, origX, origY, mode:'move'|'rotate', origRot}
  const cvRef = useRef(null);

  useEffect(() => { fetch('/api/plotter-models').then(r=>r.json()).then(setPlotterModels); }, []);

  const totalModules = steps.reduce((n, s) => s.kind === 'group' ? n + (s.branches || []).reduce((m, b) => m + b.length, 0) : n + (s.mod ? 1 : 0), 0);

  useEffect(() => { fetch('/api/modules').then(r=>r.json()).then(setModules); }, []);
  useEffect(() => {
    if (regenFlag.current && totalModules > 0) { regenFlag.current = false; generateRef.current?.(); }
  }, [steps, symmetry, sampling, output, regenTrigger]);

  // Get selected module for param editing
  const getSelectedMod = () => {
    if (!sel) return null;
    const step = steps[sel.step];
    if (!step) return null;
    if (step.kind === 'single') return step.mod;
    if (step.kind === 'group' && sel.branch != null && sel.sub != null)
      return step.branches[sel.branch]?.[sel.sub] || null;
    return null;
  };
  const selectedMod = getSelectedMod();

  const makeMod = (type) => {
    const def = modules[type];
    const params = { type };
    for (const [k, v] of Object.entries(def.params)) { params[k] = v.default; }
    return { id: ++idCounter.current, type, params };
  };

  // Add a new step — with type (from drag/click) or null (placeholder)
  const addStep = (type, atIdx) => {
    const mod = type && modules ? makeMod(type) : null;
    const idx = atIdx != null ? atIdx : steps.length;
    setSteps(prev => [...prev.slice(0, idx), { kind: 'single', mod }, ...prev.slice(idx)]);
    setSel({ step: idx });
  };

  // Add a new branch to a group, or convert single to group
  const addBranch = (stepIdx) => {
    setSteps(prev => {
      const next = [...prev];
      const s = next[stepIdx];
      if (s.kind === 'single') {
        // Convert to group with two branches: original + empty
        next[stepIdx] = { kind: 'group', branches: [s.mod ? [s.mod] : [], []] };
      } else {
        next[stepIdx] = { ...s, branches: [...s.branches, []] };
      }
      return next;
    });
  };

  // Add a step within a branch
  const addToBranch = (stepIdx, branchIdx, type) => {
    const mod = type && modules ? makeMod(type) : null;
    setSteps(prev => {
      const next = [...prev];
      const s = next[stepIdx];
      const branches = [...s.branches];
      branches[branchIdx] = [...branches[branchIdx], mod];
      next[stepIdx] = { ...s, branches };
      return next;
    });
  };

  // Legacy: convert to group by adding parallel (used by drag-on-step)
  const addParallel = (stepIdx, type) => {
    const mod = type && modules ? makeMod(type) : null;
    setSteps(prev => {
      const next = [...prev];
      const s = next[stepIdx];
      if (s.kind === 'single') {
        if (!s.mod && !mod) return next;
        next[stepIdx] = { kind: 'group', branches: [
          s.mod ? [s.mod] : [],
          mod ? [mod] : [],
        ].filter(b => b.length > 0) };
        if (next[stepIdx].branches.length === 0) next[stepIdx] = { kind: 'single', mod: null };
      } else {
        next[stepIdx] = { ...s, branches: [...s.branches, mod ? [mod] : []] };
      }
      return next;
    });
  };

  // Fill a placeholder
  const fillPlaceholder = (stepIdx, branchIdx, subIdx, type) => {
    if (!modules) return;
    const mod = makeMod(type);
    setSteps(prev => {
      const next = [...prev];
      const s = next[stepIdx];
      if (s.kind === 'single') {
        next[stepIdx] = { kind: 'single', mod };
      } else if (branchIdx != null && subIdx != null) {
        const branches = s.branches.map((b, bi) => {
          if (bi !== branchIdx) return b;
          return b.map((m, mi) => mi === subIdx ? mod : m);
        });
        next[stepIdx] = { ...s, branches };
      }
      return next;
    });
    setSel({ step: stepIdx, branch: branchIdx, sub: subIdx });
  };

  // Remove: step, branch, or module within branch
  const removeAt = (stepIdx, branchIdx, subIdx) => {
    setSteps(prev => {
      const next = [...prev];
      const s = next[stepIdx];
      if (s.kind === 'single' || branchIdx == null) {
        next.splice(stepIdx, 1);
      } else if (subIdx != null) {
        // Remove module within a branch
        const branches = s.branches.map((b, bi) => bi === branchIdx ? b.filter((_, i) => i !== subIdx) : b);
        const nonEmpty = branches.filter(b => b.length > 0);
        if (nonEmpty.length <= 1) {
          next[stepIdx] = { kind: 'single', mod: nonEmpty[0]?.[0] || null };
        } else {
          next[stepIdx] = { ...s, branches: nonEmpty };
        }
      } else {
        // Remove entire branch
        const branches = s.branches.filter((_, i) => i !== branchIdx);
        if (branches.length <= 1) {
          next[stepIdx] = { kind: 'single', mod: branches[0]?.[0] || null };
        } else {
          next[stepIdx] = { ...s, branches };
        }
      }
      return next;
    });
    setSel(null);
  };

  // Update param on selected module
  const updateParam = (stepIdx, branchIdx, subIdx, key, value) => {
    setSteps(prev => {
      const next = [...prev];
      const s = next[stepIdx];
      if (s.kind === 'single') {
        next[stepIdx] = { ...s, mod: { ...s.mod, params: { ...s.mod.params, [key]: value } } };
      } else if (branchIdx != null && subIdx != null) {
        const branches = s.branches.map((b, bi) => {
          if (bi !== branchIdx) return b;
          return b.map((m, mi) => mi === subIdx ? { ...m, params: { ...m.params, [key]: value } } : m);
        });
        next[stepIdx] = { ...s, branches };
      }
      return next;
    });
  };

  // Unified drag system: reorder steps, drag new modules, or extract branches
  const [dragSrc, setDragSrc] = useState(null);  // {type:'reorder',idx} or {type:'new',modType} or {type:'branch',stepIdx,branchIdx}
  const [dropTarget, setDropTarget] = useState(null);  // {stepIdx, mode:'before'|'on'|'after'}

  const onStepDragStart = (idx) => setDragSrc({ type: 'reorder', idx });
  const onPaletteDragStart = (modType) => setDragSrc({ type: 'new', modType });
  const onBranchDragStart = (e, stepIdx, branchIdx) => { e.stopPropagation(); setDragSrc({ type: 'branch', stepIdx, branchIdx }); };

  const onStepDragOver = (e, stepIdx) => {
    e.preventDefault();
    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const h = rect.height;
    let mode;
    if (y < h * 0.25) mode = 'before';
    else if (y > h * 0.75) mode = 'after';
    else mode = 'on';
    setDropTarget({ stepIdx, mode });
  };

  const onEmptyDragOver = (e, stepIdx) => {
    e.preventDefault();
    setDropTarget({ stepIdx, mode: 'after' });
  };

  const doDrop = () => {
    if (!dragSrc || !dropTarget) return;
    const { stepIdx, mode } = dropTarget;
    if (dragSrc.type === 'new') {
      if (mode === 'on') {
        addParallel(stepIdx, dragSrc.modType);
      } else {
        const insertIdx = mode === 'before' ? stepIdx : stepIdx + 1;
        addStep(dragSrc.modType, insertIdx);
      }
    } else if (dragSrc.type === 'reorder') {
      const fromIdx = dragSrc.idx;
      if (mode === 'on' && fromIdx !== stepIdx) {
        setSteps(prev => {
          const next = [...prev];
          const src = next[fromIdx];
          const tgt = next[stepIdx];
          const srcBranches = src.kind === 'group' ? src.branches : (src.mod ? [[src.mod]] : []);
          const tgtBranches = tgt.kind === 'group' ? tgt.branches : (tgt.mod ? [[tgt.mod]] : []);
          next[stepIdx] = { kind: 'group', branches: [...tgtBranches, ...srcBranches] };
          next.splice(fromIdx, 1);
          return next;
        });
        regenFlag.current = true;
      } else if (mode !== 'on' && fromIdx !== stepIdx) {
        let toIdx = mode === 'before' ? stepIdx : stepIdx + 1;
        if (fromIdx < toIdx) toIdx--;
        if (fromIdx !== toIdx) {
          setSteps(prev => {
            const next = [...prev];
            const [moved] = next.splice(fromIdx, 1);
            next.splice(toIdx, 0, moved);
            return next;
          });
          regenFlag.current = true;
        }
      }
    } else if (dragSrc.type === 'branch') {
      // Extract a branch from a group and insert as a new serial step
      const { stepIdx: srcStep, branchIdx } = dragSrc;
      if (mode === 'on' && stepIdx === srcStep) return; // dropping back on own group
      setSteps(prev => {
        const next = [...prev];
        const group = next[srcStep];
        if (!group || group.kind !== 'group' || !group.branches) return next;
        const branch = group.branches[branchIdx];
        if (!branch || branch.length === 0) return next;

        // Remove branch from group
        const remaining = group.branches.filter((_, i) => i !== branchIdx);
        if (remaining.length <= 1) {
          // Collapse group to single step
          next[srcStep] = { kind: 'single', mod: remaining[0]?.[0] || null };
        } else {
          next[srcStep] = { ...group, branches: remaining };
        }

        // Create new single step(s) from the extracted branch
        // For simplicity, wrap the first mod as a single step (branches are typically 1 mod)
        const newStep = branch.length === 1
          ? { kind: 'single', mod: branch[0] }
          : { kind: 'group', branches: [branch] };  // keep as single-branch group if multi-mod

        // Insert at the right position
        if (mode === 'on' && stepIdx !== srcStep) {
          // Merge into target
          const tgt = next[stepIdx];
          const tgtBranches = tgt.kind === 'group' ? tgt.branches : (tgt.mod ? [[tgt.mod]] : []);
          next[stepIdx] = { kind: 'group', branches: [...tgtBranches, branch] };
        } else {
          let insertIdx = mode === 'before' ? stepIdx : stepIdx + 1;
          // Adjust if source group was before the insert point and it was removed/shrunk
          next.splice(insertIdx, 0, newStep);
        }
        return next;
      });
      regenFlag.current = true;
    }
  };

  const onDrop = (e) => { e.preventDefault(); doDrop(); setDragSrc(null); setDropTarget(null); };
  const onDragEnd = () => { setDragSrc(null); setDropTarget(null); };

  const generate = async () => {
    if (totalModules === 0) return;
    setGenerating(true);
    setStatus('Generating...');
    const t0 = Date.now();
    try {
      // Convert steps to backend format, skipping placeholders
      const stepsData = steps
        .filter(s => s.kind === 'single' ? s.mod !== null : s.branches.some(b => b.some(m => m !== null)))
        .map(s => {
          if (s.kind === 'single') return { kind: 'single', params: s.mod.params };
          return { kind: 'group', branches: s.branches.map(b => b.filter(m => m !== null).map(m => m.params)).filter(b => b.length > 0) };
        });
      const body = {
        steps: stepsData,
        output,
        sampling,
        symmetry: symmetry.n_fold > 1 || symmetry.mirror ? symmetry : {},
      };
      const res = await fetch('/api/generate-points', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Generation failed'); }
      const data = await res.json();
      setPointData(data);

      const totalPts = data.paths.reduce((n, p) => n + p.length, 0);
      setStatus(`Done in ${((Date.now()-t0)/1000).toFixed(1)}s — ${totalPts} points`);
    } catch (e) {
      setStatus('Error: ' + e.message);
    } finally {
      setGenerating(false);
    }
  };
  generateRef.current = generate;


  const plotToAxidraw = async () => {
    if (totalModules === 0) return;
    const stepsData = steps
      .filter(s => s.kind === 'single' ? s.mod !== null : s.branches.some(b => b.some(m => m !== null)))
      .map(s => {
        if (s.kind === 'single') return { kind: 'single', params: s.mod.params };
        return { kind: 'group', branches: s.branches.map(b => b.filter(m => m !== null).map(m => m.params)).filter(b => b.length > 0) };
      });
    const body = {
      steps: stepsData, output, sampling,
      symmetry: symmetry.n_fold > 1 || symmetry.mirror ? symmetry : {},
      moire: moire.enabled ? { module_idx: moire.module_idx, param: moire.param, copies: moire.copies, range: moire.range } : {},
      ...pOpts,
      cv_offset_x: canvasRef.current ? cvOff.x / canvasRef.current.clientWidth : 0,
      cv_offset_y: canvasRef.current ? cvOff.y / canvasRef.current.clientHeight : 0,
      cv_rotation: cvRot, cv_scale: cvScale,
    };
    try {
      setStatus('Sending to AxiDraw...');
      const res = await fetch('/api/plot', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Plot failed'); }
      const data = await res.json();
      setStatus(`Plotting ${data.total_points} points in ${data.segments} segments...`);
      // Poll for progress
      if (plotPollRef.current) clearInterval(plotPollRef.current);
      plotPollRef.current = setInterval(async () => {
        const sr = await fetch('/api/plotter-status');
        const st = await sr.json();
        setPlotterStatus(st);
        if (st.error) setStatus('Plotter error: ' + st.error);
        else if (st.message) setStatus(st.message);
        if (!st.plotting) { clearInterval(plotPollRef.current); plotPollRef.current = null; }
      }, 1000);
    } catch (e) {
      setStatus('Plot error: ' + e.message);
    }
  };

  const plotStop = async () => {
    await fetch('/api/plot-stop', { method: 'POST' });
    if (plotPollRef.current) { clearInterval(plotPollRef.current); plotPollRef.current = null; }
    setStatus('Plot stopped');
  };

  // Canvas interaction: drag to move, shift+drag to rotate
  // cvOff is stored in SVG viewBox units (not pixels) for stability
  const cvOffRef = useRef(cvOff);
  const cvRotRef = useRef(cvRot);
  cvOffRef.current = cvOff;
  cvRotRef.current = cvRot;

  const plotterPatternsRef = useRef(plotterPatterns);
  plotterPatternsRef.current = plotterPatterns;

  const cvMouseDown = (e) => {
    if (e.button !== 0) return;
    // Don't handle clicks on toolbar buttons/inputs inside the canvas area
    const tag = e.target.tagName;
    if (tag === 'BUTTON' || tag === 'INPUT' || tag === 'SELECT') return;
    e.preventDefault();
    e.stopPropagation();

    // In plotter mode, check if clicking on a placed pattern
    if (plotterActive && plotterPatternsRef.current.length > 0 && !e.shiftKey) {
      const cvs = canvasRef.current;
      if (cvs) {
        const rect = cvs.getBoundingClientRect();
        const mx = e.clientX - rect.left, my = e.clientY - rect.top;
        const drawW = cvs.clientWidth, drawH = cvs.clientHeight;
        // Check placed patterns in reverse (top-most first)
        for (let i = plotterPatternsRef.current.length - 1; i >= 0; i--) {
          const pp = plotterPatternsRef.current[i];
          const ppSc = drawH / pp.config.height * pp.scale;
          const px = pp.x * (drawW / 100), py = pp.y * (drawH / 100);
          const pw = pp.config.width * (drawH / pp.config.height) * pp.scale;
          const ph = drawH * pp.scale;
          if (mx >= px && mx <= px + pw && my >= py && my <= py + ph) {
            setSelectedPlaced(pp.id);
            placedDrag.current = {id: pp.id, startX: e.clientX, startY: e.clientY,
              origX: pp.x, origY: pp.y, drawW, drawH};
            document.body.style.cursor = 'grabbing';
            return;
          }
        }
        setSelectedPlaced(null);
      }
    }

    if (e.shiftKey) {
      const rect = cvRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width/2, cy = rect.top + rect.height/2;
      const startAngle = Math.atan2(e.clientY - cy, e.clientX - cx) * 180 / Math.PI;
      cvDrag.current = {mode:'rotate', startAngle, origRot: cvRotRef.current};
    } else {
      cvDrag.current = {mode:'move', startX: e.clientX, startY: e.clientY,
        origX: cvOffRef.current.x, origY: cvOffRef.current.y};
    }
    document.body.style.cursor = e.shiftKey ? 'crosshair' : 'grabbing';
  };
  const cvReset = () => { setCvOff({x:0,y:0}); setCvRot(0); setCvScale(1); };

  useEffect(() => {
    const onMove = (e) => {
      // Handle placed pattern dragging
      if (placedDrag.current) {
        e.preventDefault();
        const dx = e.clientX - placedDrag.current.startX;
        const dy = e.clientY - placedDrag.current.startY;
        const newX = placedDrag.current.origX + (dx / placedDrag.current.drawW) * 100;
        const newY = placedDrag.current.origY + (dy / placedDrag.current.drawH) * 100;
        updatePlotterPattern(placedDrag.current.id, { x: newX, y: newY });
        return;
      }
      if (!cvDrag.current) return;
      e.preventDefault();
      if (cvDrag.current.mode === 'move') {
        setCvOff({x: cvDrag.current.origX + e.clientX - cvDrag.current.startX,
                  y: cvDrag.current.origY + e.clientY - cvDrag.current.startY});
      } else if (cvDrag.current.mode === 'rotate' && cvRef.current) {
        const rect = cvRef.current.getBoundingClientRect();
        const cx = rect.left + rect.width/2, cy = rect.top + rect.height/2;
        const angle = Math.atan2(e.clientY - cy, e.clientX - cx) * 180 / Math.PI;
        setCvRot(cvDrag.current.origRot + angle - cvDrag.current.startAngle);
      }
    };
    const onUp = () => { cvDrag.current = null; placedDrag.current = null; document.body.style.cursor = ''; };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
  }, []);

  // Multi-pattern composition
  // (addToPlotter, removePlotterPattern, updatePlotterPattern defined above with tab system)

  // Canvas rendering
  const drawCanvas = useCallback(() => {
    const cvs = canvasRef.current;
    if (!cvs) return;
    if (!pointData && !plotterActive) return;
    const ctx = cvs.getContext('2d');
    const cfg = pointData ? pointData.config : {width:800,height:800,bg_color:'#ffffff',stroke_color:'#000000',stroke_width:0.3};
    const dpr = window.devicePixelRatio || 1;

    // Measure available space from the sizer div (position:absolute, always in DOM).
    const sizer = document.getElementById('canvas-sizer');
    if (!sizer) return;
    const cw = sizer.clientWidth, ch = sizer.clientHeight;
    if (cw === 0 || ch === 0) return;

    const pm = plotterActive && plotterModels[pOpts.model];
    const canvasAR = pm ? pm.width / pm.height : cfg.width / cfg.height;

    let drawW, drawH;
    if (cw / ch > canvasAR) { drawH = ch; drawW = ch * canvasAR; }
    else { drawW = cw; drawH = cw / canvasAR; }

    cvs.style.width = drawW + 'px';
    cvs.style.height = drawH + 'px';
    cvs.width = Math.round(drawW * dpr);
    cvs.height = Math.round(drawH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Background
    ctx.fillStyle = cfg.bg_color || '#ffffff';
    ctx.fillRect(0, 0, drawW, drawH);

    // Scale drawing to fit within canvas, preserving the pattern's own aspect ratio
    const svgW = cfg.width, svgH = cfg.height;
    const patternAR = svgW / svgH;
    // Fit pattern inside canvas without distortion
    // In plotter mode, scale to fit paper height (Y preserved), allow horizontal overflow
    let pxW, pxH;
    if (pm && patternAR > canvasAR) {
      // Pattern wider than paper: fit to height, let width overflow (user can zoom/pan)
      pxH = drawH; pxW = drawH * patternAR;
    } else if (drawW / drawH > patternAR) {
      pxH = drawH; pxW = drawH * patternAR;
    } else {
      pxW = drawW; pxH = drawW / patternAR;
    }
    const sc = pxW / svgW; // uniform scale from SVG coords to canvas pixels
    const offX = (drawW - pxW) / 2;
    const offY = (drawH - pxH) / 2;

    // Drawing center in canvas pixel coords
    const cxC = offX + pxW / 2;
    const cyC = offY + pxH / 2;

    // Helper: draw a set of paths with given transforms
    const drawPaths = (paths, pcfg, psc, ox, oy, pOff, pRot, pScale, isSelected) => {
      const pcxC = ox + (pcfg.width * psc) / 2;
      const pcyC = oy + (pcfg.height * psc) / 2;
      ctx.save();
      ctx.translate(pcxC + pOff.x, pcyC + pOff.y);
      ctx.rotate(pRot * Math.PI / 180);
      ctx.scale(pScale, pScale);
      ctx.translate(-pcxC, -pcyC);
      ctx.translate(ox, oy);
      ctx.strokeStyle = pcfg.stroke_color || '#000000';
      ctx.lineWidth = Math.max(0.4, (pcfg.stroke_width || 0.3) * psc);
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      for (const path of paths) {
        if (path.length < 2) continue;
        ctx.beginPath();
        ctx.moveTo(path[0][0] * psc, path[0][1] * psc);
        for (let i = 1; i < path.length; i++) ctx.lineTo(path[i][0] * psc, path[i][1] * psc);
        ctx.stroke();
      }
      if (isSelected) {
        ctx.strokeStyle = 'rgba(124,92,252,0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(0, 0, pcfg.width * psc, pcfg.height * psc);
        ctx.setLineDash([]);
      }
      ctx.restore();
    };

    // Draw placed patterns (plotter composition)
    if (plotterActive && plotterPatterns.length > 0) {
      for (const pp of plotterPatterns) {
        const ppAR = pp.config.width / pp.config.height;
        // Scale placed pattern to fit paper height
        const ppSc = drawH / pp.config.height;
        const ppOffX = pp.x * (drawW / 100); // x,y are in % of paper
        const ppOffY = pp.y * (drawH / 100);
        drawPaths(pp.paths, pp.config, ppSc,
          ppOffX, ppOffY, {x:0, y:0}, pp.rotation, pp.scale,
          pp.id === selectedPlaced);
      }
    }

    // Draw current live pattern (only on pattern tabs, not plotter tab)
    if (pointData && !plotterActive) {
      drawPaths(pointData.paths, cfg, sc, offX, offY, cvOff, cvRot, cvScale, false);
    }

    // Paper border in plotter mode
    if (pm) {
      ctx.strokeStyle = 'rgba(0,0,0,0.15)';
      ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, drawW, drawH);
    }
  }, [pointData, cvOff, cvRot, cvScale, plotterActive, pOpts.model, plotterModels, plotterPatterns, selectedPlaced]);

  useEffect(() => { drawCanvas(); }, [drawCanvas]);
  useEffect(() => {
    const onResize = () => drawCanvas();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [drawCanvas]);

  const saveConfig = async (skipConfirm) => {
    if (!saveName.trim()) return;
    try {
      // Check for overwrite
      if (!skipConfirm) {
        const chk = await fetch('/api/file-exists?name=' + encodeURIComponent(saveName));
        const { exists } = await chk.json();
        if (exists && !confirm('Overwrite "' + saveName + '.ini"?')) return;
      }
      setSaving(true);
      const stepsData = steps
        .filter(s => s.kind === 'single' ? s.mod !== null : (s.branches || []).some(b => b.some(m => m !== null)))
        .map(s => {
          if (s.kind === 'single') return { kind: 'single', params: s.mod.params };
          return { kind: 'group', branches: s.branches.map(b => b.filter(m => m !== null).map(m => m.params)).filter(b => b.length > 0) };
        });
      const res = await fetch('/api/save', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: saveName, steps: stepsData, output, sampling,
          symmetry: symmetry.n_fold > 1 || symmetry.mirror ? symmetry : {},
          }),
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Save failed'); }
      const data = await res.json();
      setStatus('Saved: ' + data.saved);
      setShowSave(false);
      setLoadedFile(data.saved);
      refreshIniFiles();
    } catch (e) {
      setStatus('Error: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const randomize = () => {
    if (!modules) return;
    const R = Math.random;
    const pick = arr => arr[Math.floor(R() * arr.length)];
    const rf = (lo, hi) => Math.round((lo + R() * (hi - lo)) * 100) / 100;
    const rint = (lo, hi) => Math.round(lo + R() * (hi - lo));
    const gcd = (a, b) => { while (b) { [a, b] = [b, a % b]; } return a; };
    const mm = (type, params) => ({ id: ++idCounter.current, type, params: { type, ...params } });
    const hz = {freq3:0,amp3:0,phase3:0,decay3:0,freq4:0,amp4:0,phase4:0,decay4:0};
    const rot = d => ({ kind:'single', mod: mm('rotation', { total_degrees:d, origin_x:0, origin_y:0, normalize:true }) });
    const arc = (r,sw) => ({ kind:'single', mod: mm('arc', { arc_radius:r, sweep_angle:sw, start_angle:0, cycles:1 }) });
    const sparc = (ir,or,sw) => ({ kind:'single', mod: mm('spiral_arc', { inner_radius:ir, outer_radius:or, sweep_angle:sw, start_angle:0 }) });
    const noise = (a,f) => ({ kind:'single', mod: mm('noise', { amplitude:a, frequency:f }) });
    const bend = (r,sw) => ({ kind:'single', mod: mm('bend', { radius:r, sweep_angle:sw }) });
    const damp = (rate,dur) => ({ kind:'single', mod: mm('damping', { decay_rate:rate, duration:dur }) });

    const recipes = [

      // ── HARMONOGRAPH: Slow Decay 4-Frequency (top experiment result, path 575K) ──
      () => {
        const [a,b] = pick([[3,2],[2,3],[5,4],[4,3]]);
        const [c,d] = pick([[5,4],[4,3],[7,5],[3,2]]);
        return { steps: [{ kind:'single', mod: mm('harmonograph', {
          freq1:a, freq2:b+(R()-0.5)*0.006, freq3:c, freq4:d+(R()-0.5)*0.004,
          amp1:100, amp2:rf(70,90), amp3:rf(40,60), amp4:rf(30,50),
          phase1:0, phase2:rf(0.5,1.57), phase3:rf(1.0,2.0), phase4:rf(1.5,2.5),
          decay1:rf(0.001,0.004), decay2:rf(0.001,0.004), decay3:rf(0.001,0.004), decay4:rf(0.001,0.004),
          duration:rf(100,150), cycles:1,
        })}], sw: 0.1 };
      },

      // ── HARMONOGRAPH: 7:5 Complex (experiment path 397K) ──
      () => {
        const [a,b] = pick([[7,5],[5,7],[7,4],[4,7]]);
        return { steps: [{ kind:'single', mod: mm('harmonograph', {
          freq1:a, freq2:b+(R()-0.5)*0.006, freq3:pick([3,2]), freq4:pick([4,5])+(R()-0.5)*0.01,
          amp1:100, amp2:80, amp3:60, amp4:50,
          phase1:0, phase2:1.5708, phase3:rf(0.3,0.7), phase4:rf(1.5,2.5),
          decay1:rf(0.003,0.005), decay2:rf(0.002,0.004), decay3:rf(0.004,0.006), decay4:rf(0.003,0.005),
          duration:rf(50,80), cycles:1,
        })}], sw: 0.1 };
      },

      // ── HARMONOGRAPH: Prime Harmonics 2:3:5:7 (experiment path 258K) ──
      () => ({
        steps: [{ kind:'single', mod: mm('harmonograph', {
          freq1:2, freq2:3+(R()-0.5)*0.01, freq3:5, freq4:7+(R()-0.5)*0.006,
          amp1:100, amp2:80, amp3:60, amp4:50,
          phase1:0, phase2:1.5708, phase3:rf(0.3,0.7), phase4:rf(1.5,2.5),
          decay1:rf(0.003,0.005), decay2:rf(0.002,0.004), decay3:rf(0.004,0.006), decay4:rf(0.003,0.005),
          duration:60, cycles:1,
        })}], sw: 0.1,
      }),

      // ── HARMONOGRAPH: Beat Pattern — extreme detuning (experiment path 273K) ──
      () => {
        const base = pick([2,3]);
        return { steps: [{ kind:'single', mod: mm('harmonograph', {
          freq1:base, freq2:base+rf(0.03,0.07), freq3:base+1, freq4:base+1+rf(0.04,0.08),
          amp1:100, amp2:80, amp3:60, amp4:40,
          phase1:0, phase2:1.5708, phase3:rf(0.5,1.5), phase4:rf(2.0,3.0),
          decay1:rf(0.001,0.003), decay2:rf(0.002,0.004), decay3:rf(0.001,0.002), decay4:rf(0.001,0.003),
          duration:rf(80,120), cycles:1,
        })}], sw: 0.1 };
      },

      // ── HARMONOGRAPH: Fast Decay spiral-in (experiment path 86K) ──
      () => {
        const [a,b] = pick([[3,2],[5,4],[7,5]]);
        return { steps: [{ kind:'single', mod: mm('harmonograph', {
          freq1:a, freq2:b+0.005, freq3:pick([5,3]), freq4:pick([7,4])+0.003,
          amp1:120, amp2:100, amp3:80, amp4:60,
          phase1:0, phase2:1.5708, phase3:0.5, phase4:2.0,
          decay1:rf(0.015,0.025), decay2:rf(0.012,0.02), decay3:rf(0.02,0.03), decay4:rf(0.015,0.025),
          duration:rf(15,30), cycles:1,
        })}], sw: 0.15 };
      },

      // ── HARMONOGRAPH: Amplitude Drift "Butterfly" ──
      () => {
        const [a,b] = pick([[2,3],[3,4],[5,4]]);
        const d = rf(0.002,0.005);
        return { steps: [{ kind:'single', mod: mm('harmonograph', {
          freq1:a, amp1:rf(100,130), end_amp1:rf(20,40), phase1:0, decay1:d,
          freq2:b+(R()-0.5)*0.008, amp2:rf(100,130), end_amp2:rf(40,70), phase2:90, decay2:d,
          freq3:1+(R()-0.5)*0.005, amp3:rf(30,55), end_amp3:rf(5,15), phase3:rf(20,60), decay3:d,
          freq4:0, amp4:0, phase4:0, decay4:0,
          duration:rf(80,110), cycles:rint(3,5),
        })}], sw: 0.12 };
      },

      // ── HARMONOGRAPH + ROTATION ──
      () => {
        const [a,b] = pick([[2,3],[3,4],[5,4],[5,3]]);
        const d = rf(0.004,0.01);
        return { steps: [
          { kind:'single', mod: mm('harmonograph', {
            freq1:a, amp1:100, phase1:0, decay1:d,
            freq2:b+(R()-0.5)*0.01, amp2:100, phase2:90, decay2:d, ...hz,
            duration:rf(60,90), cycles:rint(3,5),
          })},
          { kind:'single', mod: mm('rotation', { total_degrees:pick([90,120,180]), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.15 };
      },

      // ── HARMONOGRAPH + CIRCLE GROUP (experiment: fuzzy orbits) ──
      () => {
        const [a,b] = pick([[2,3],[3,4],[5,4]]);
        const cRad = pick([15, 20, 25, 30]);
        const cCycles = cRad < 20 ? rint(15,25) : rint(4,8);
        return { steps: [
          { kind:'group', branches: [
            [mm('harmonograph', {
              freq1:a, amp1:100, phase1:0, decay1:rf(0.004,0.008),
              freq2:b+0.005, amp2:80, phase2:1.5708, decay2:rf(0.003,0.006), ...hz,
              duration:rf(35,50), cycles:1,
            })],
            [mm('circle', { radius:cRad, cycles:cCycles })],
          ]},
        ], sw: 0.12 };
      },

      // ── DUAL HARMONOGRAPH GROUP (experiment: path 186K) ──
      () => {
        const [a1,b1] = pick([[2,3],[3,4]]);
        const [a2,b2] = pick([[5,4],[7,5],[3,2]]);
        const d = rf(0.003,0.007);
        return { steps: [
          { kind:'group', branches: [
            [mm('harmonograph', {
              freq1:a1, amp1:100, phase1:0, decay1:d,
              freq2:b1+0.003, amp2:100, phase2:90, decay2:d, ...hz,
              duration:80, cycles:rint(3,5),
            })],
            [mm('harmonograph', {
              freq1:a2, amp1:rf(50,75), phase1:0, decay1:d,
              freq2:b2+0.004, amp2:rf(50,75), phase2:90, decay2:d, ...hz,
              duration:80, cycles:rint(3,5),
            })],
          ]},
          { kind:'single', mod: mm('damping', { decay_rate:rf(0.008,0.015), duration:rf(40,60) }) },
        ], sw: 0.12 };
      },

      // ── HARMONOGRAPH + CIRCLE + TRANSLATION (decay_shell_joe archetype) ──
      () => {
        const [a,b] = pick([[2,3],[3,2],[3,4]]);
        return { steps: [
          { kind:'group', branches: [
            [mm('harmonograph', {
              freq1:a, amp1:100, phase1:0, decay1:0,
              freq2:b, amp2:100, end_amp2:rf(50,80), phase2:90, decay2:0, ...hz,
              duration:60, cycles:3,
            })],
            [mm('circle', { radius:rf(30,55), cycles:1 })],
            [mm('translation', { start_x:0, end_x:rf(60,120), start_y:0, end_y:0, normalize:true })],
          ]},
          { kind:'single', mod: mm('rotation', { total_degrees:rf(50,120), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.12 };
      },

      // ── GEAR: Fibonacci ratios (experiment: dense fill, path 155K) ──
      () => {
        const [f,r] = pick([[233,144],[144,89],[89,55]]);
        return { steps: [{ kind:'single', mod: mm('spirograph_gear', {
          fixed_teeth:f, rolling_teeth:r, tooth_pitch:rf(0.8,1.5),
          hole_position:rf(0.7,0.9), inside:true, cycles:1,
        })}], sw: 0.12 };
      },

      // ── GEAR: Classic with good GCD ──
      () => {
        const fixed = pick([96, 105, 120, 144]);
        const candidates = [24,30,32,36,40,45,48,52,56,60,63,72].filter(r => r < fixed && gcd(fixed,r) >= 3 && gcd(fixed,r) <= 12);
        const rolling = candidates.length ? pick(candidates) : 36;
        return { steps: [{ kind:'single', mod: mm('spirograph_gear', {
          fixed_teeth:fixed, rolling_teeth:rolling,
          tooth_pitch:rf(4,9), hole_position:rf(0.55,0.75), inside:true, cycles:1,
        })}], sw: 0.12 };
      },

      // ── GEAR + ROTATION + SCALE (experiment: concentric rings) ──
      () => {
        const fixed = pick([100,96,120]);
        const rolling = pick([37,41,43,47].filter(r => r < fixed));
        return { steps: [
          { kind:'single', mod: mm('spirograph_gear', {
            fixed_teeth:fixed, rolling_teeth:rolling, tooth_pitch:rf(1.5,3),
            hole_position:rf(0.7,0.9), inside:true, cycles:1,
          })},
          { kind:'single', mod: mm('scale', { start_scale:1.0, end_scale:rf(0.4,0.6) }) },
          { kind:'single', mod: mm('rotation', { total_degrees:pick([90,120,180]), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.12 };
      },

      // ── GEAR DRIFT + BEND "Wreath" ──
      () => {
        const fixed = pick([96,105,120]);
        const rolling = pick([36,40,45,52].filter(r => r < fixed));
        return { steps: [
          { kind:'single', mod: mm('spirograph_gear', { fixed_teeth:fixed, rolling_teeth:rolling, tooth_pitch:rf(4,7), hole_position:rf(0.4,0.55), end_hole_position:rf(0.75,0.9), inside:true, cycles:rint(10,20) }) },
          { kind:'single', mod: mm('translation', { start_x:0, end_x:rf(150,250), start_y:0, end_y:0, normalize:true }) },
          { kind:'single', mod: mm('bend', { radius:rf(170,260), sweep_angle:pick([180,200,240]) }) },
          { kind:'single', mod: mm('rotation', { total_degrees:pick([180,270,360]), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.1 };
      },

      // ── GEAR SCROLL archetype ──
      () => ({
        steps: [
          { kind:'single', mod: mm('spirograph_gear', { fixed_teeth:105, rolling_teeth:52, tooth_pitch:rf(5,8), hole_position:0.65, inside:true, cycles:rint(10,20) }) },
          { kind:'single', mod: mm('translation', { start_x:0, end_x:rf(150,250), start_y:0, end_y:0, normalize:true }) },
          { kind:'single', mod: mm('rotation', { total_degrees:pick([90,180,360,540]), origin_x:0, origin_y:0, normalize:true }) },
          { kind:'single', mod: mm('spiral_shape', { start_radius:5, end_radius:rf(120,170), turns:rf(4,6), cycles:1 }) },
        ], sw: 0.12,
      }),

      // ── LISSAJOUS + SCALE "Nautilus Mesh" ──
      () => {
        const [a,b] = pick([[5,6],[7,8],[9,8],[7,6],[5,4]]);
        return { steps: [
          { kind:'single', mod: mm('lissajous', { freq_x:a, freq_y:b, amp_x:rf(100,140), amp_y:rf(100,140), phase:rf(40,80), cycles:rint(2,4) }) },
          { kind:'single', mod: mm('scale', { start_scale:1.0, end_scale:rf(0.2,0.4) }) },
          { kind:'single', mod: mm('rotation', { total_degrees:pick([120,180,270]), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.1 };
      },

      // ── ELLIPSE AXIS SWAP "Lens" ──
      () => {
        const rx = rf(140,200), ry = rf(20,40);
        return { steps: [
          { kind:'single', mod: mm('ellipse', { radius_x:rx, radius_y:ry, end_radius_x:ry, end_radius_y:rx, cycles:rint(100,180), rotation:rf(0,90) }) },
          { kind:'single', mod: mm('damping', { decay_rate:rf(0.01,0.02), duration:rf(40,70) }) },
          { kind:'single', mod: mm('rotation', { total_degrees:pick([120,180,270]), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.12 };
      },

      // ── SURFACE + ROTATION "Trefoil" ──
      () => {
        const stype = pick(['torus','figure8','mobius','klein']);
        return { steps: [
          { kind:'single', mod: mm(stype === 'klein' ? 'klein_bottle' : stype, { surface:stype, major_radius:rf(100,150), minor_radius:rf(35,65), width:rf(40,80), v_lines:rint(30,60), view_angle_x:rf(20,50), view_angle_y:rf(10,40), view_angle_z:rf(-15,15) }) },
          { kind:'single', mod: mm('rotation', { total_degrees:360, origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.12 };
      },

      // ── ROSE with interesting ratios ──
      () => {
        const [p,d] = pick([[5,3],[7,3],[7,4],[8,3],[5,2]]);
        return { steps: [
          { kind:'single', mod: mm('rose', { petals:p, denom:d, radius:rf(100,140), cycles:1 }) },
          { kind:'single', mod: mm('rotation', { total_degrees:pick([36,45,60,72]), origin_x:0, origin_y:0, normalize:true }) },
        ], sw: 0.15, sym: pick([0,0,3,5]) || undefined };
      },

      // ── KLEIN BOTTLE + rotation (dense intricate mesh) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('klein_bottle', { surface:'klein', major_radius:rf(80,120), minor_radius:rf(30,50), v_lines:rint(40,60), view_angle_x:rf(25,45), view_angle_y:rf(15,35) }) },
          rot(360),
        ], sw: 0.1,
      }),

      // ── FIGURE-8 TORUS + rotation (spirograph-like mesh) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('figure8', { surface:'figure8', major_radius:rf(90,130), minor_radius:rf(30,50), v_lines:rint(35,55), view_angle_x:rf(15,40), view_angle_y:rf(5,25) }) },
          rot(360),
        ], sw: 0.1,
      }),

      // ── HELIX RIBBON + rotation (circle chain spiral) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('helix_ribbon', { surface:'helix_ribbon', major_radius:rf(80,120), width:rf(30,50), twists:pick([1,2,3]), v_lines:rint(30,50), view_angle_x:rf(25,40), view_angle_y:rf(15,30) }) },
          rot(360),
        ], sw: 0.12,
      }),

      // ── HARMONOGRAPH + ARC (3D knot form) ──
      () => {
        const [a,b] = pick([[3,2],[2,3],[5,4],[4,3]]);
        return { steps: [
          { kind:'single', mod: mm('harmonograph', {
            freq1:a, amp1:rf(60,80), phase1:0, decay1:rf(0.006,0.01),
            freq2:b+0.004, amp2:rf(60,80), phase2:90, decay2:rf(0.006,0.01), ...hz,
            duration:rf(35,50), cycles:rint(2,3),
          })},
          arc(rf(160,220), pick([180,270])), rot(pick([180,270,360])),
        ], sw: 0.1 };
      },

      // ── HARMONOGRAPH + SPIRAL ARC (spiral galaxy) ──
      () => {
        const [a,b] = pick([[2,3],[3,2],[3,4]]);
        return { steps: [
          { kind:'single', mod: mm('harmonograph', {
            freq1:a, amp1:rf(40,60), phase1:0, decay1:rf(0.008,0.015),
            freq2:b+0.005, amp2:rf(40,60), phase2:90, decay2:rf(0.008,0.015), ...hz,
            duration:rf(25,40), cycles:2,
          })},
          sparc(rf(15,25), rf(150,200), pick([720,1080,1440])),
        ], sw: 0.1 };
      },

      // ── GEAR EPITROCHOID + NOISE (hand-drawn ring) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('spirograph_gear', { fixed_teeth:144, rolling_teeth:pick([55,89,73]), tooth_pitch:rf(1.0,1.8), hole_position:rf(0.55,0.75), inside:false, cycles:1 }) },
          noise(rf(1.5,3.5), rf(6,14)),
        ], sw: 0.1,
      }),

      // ── STAR + HARMONOGRAPH GROUP (angular organic) ──
      () => {
        const [a,b] = pick([[3,2],[2,3],[5,4]]);
        return { steps: [
          { kind:'group', branches: [
            [mm('star_shape', { points:pick([5,6,7]), outer_radius:rf(50,70), inner_radius:rf(15,30), rotation:0, cycles:2 })],
            [mm('harmonograph', {
              freq1:a, amp1:rf(80,100), phase1:0, decay1:rf(0.005,0.008),
              freq2:b+0.005, amp2:rf(80,100), phase2:90, decay2:rf(0.005,0.008), ...hz,
              duration:60, cycles:3,
            })],
          ]},
          rot(pick([90,120])),
        ], sw: 0.12 };
      },

      // ── RACK + BEND (cloud lobes) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('rack', { teeth:rint(25,40), tooth_pitch:rf(4,7), hole_position:rf(0.6,0.8), straight_length:rf(150,250), cycles:rint(2,4) }) },
          bend(rf(170,230), pick([180,200,240])), rot(pick([180,270])),
        ], sw: 0.15,
      }),

      // ── POLYGON + SPIRAL ARC (rounded spiral) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('polygon', { sides:pick([5,6,7,8]), radius:rf(30,50), rotation:0, cycles:rint(3,5) }) },
          sparc(rf(15,25), rf(140,180), pick([720,1080])),
        ], sw: 0.12,
      }),

      // ── GUILLOCHE (banknote/certificate patterns) ──
      () => {
        const primes = [11,13,17,19,23,29,31,37,41,43,47,53,59,67,71,79,83,89];
        const div = pick(primes);
        return { steps: [
          { kind:'single', mod: mm('guilloche', {
            inner:rf(50,100), outer:rf(160,250),
            nodes:rint(80,170), div,
            n0:rint(4,12), h0:rf(5,25),
            n1:rint(8,20), h1:rf(8,30),
          })},
        ], sw: 0.08 };
      },

      // ── GUILLOCHE with envelope drift ──
      () => {
        const primes = [11,13,17,19,23,29,31,37,41,43,47,53];
        return { steps: [
          { kind:'single', mod: mm('guilloche', {
            inner:rf(40,80), end_inner:rf(90,130),
            outer:rf(200,260), end_outer:rf(150,200),
            nodes:rint(100,160), div:pick(primes),
            n0:rint(5,10), h0:rf(8,18),
            n1:rint(10,18), h1:rf(10,22),
          })},
        ], sw: 0.08 };
      },

      // ── GUILLOCHE deep chain: damping + scale + noise ──
      () => {
        const primes = [13,17,23,29,37,41,47,53,59,67,71];
        return { steps: [
          { kind:'single', mod: mm('guilloche', {
            inner:rf(50,90), outer:rf(170,240), nodes:rint(90,160), div:pick(primes),
            n0:rint(4,10), h0:rf(6,20), n1:rint(8,18), h1:rf(8,25),
          })},
          damp(rf(0.008,0.02), rf(30,60)),
          { kind:'single', mod: mm('scale', { start_scale:1.0, end_scale:rf(0.4,0.7) }) },
          noise(rf(1,3), rf(6,12)),
        ], sw: 0.1 };
      },

      // ── GUILLOCHE + stretch + rotation ──
      () => {
        const primes = [17,23,31,37,41,53,71];
        return { steps: [
          { kind:'single', mod: mm('guilloche', {
            inner:rf(60,100), outer:rf(160,220), nodes:rint(100,150), div:pick(primes),
            n0:rint(5,8), h0:rf(8,15), n1:rint(10,16), h1:rf(10,20),
          })},
          { kind:'single', mod: mm('stretch', { scale_x:rf(1.5,2.5), scale_y:1.0 }) },
          rot(pick([90,180,270,360])),
        ], sw: 0.08 };
      },

      // ── GEAR EPITROCHOID (outside rolling) + noise ──
      () => {
        const fixed = pick([96,105,120,144]);
        const rolling = pick([36,40,45,52,55].filter(r => r < fixed));
        return { steps: [
          { kind:'single', mod: mm('spirograph_gear', { fixed_teeth:fixed, rolling_teeth:rolling, tooth_pitch:rf(1.0,2.5), hole_position:rf(0.55,0.75), inside:false, cycles:1 }) },
          noise(rf(1.5,3), rf(6,12)),
          rot(pick([90,180,360])),
        ], sw: 0.1 };
      },

      // ── GEAR deep chain: noise + rotation + damping ──
      () => {
        const fixed = pick([96,100,120]);
        const rolling = pick([37,41,43,47].filter(r => r < fixed));
        return { steps: [
          { kind:'single', mod: mm('spirograph_gear', { fixed_teeth:fixed, rolling_teeth:rolling, tooth_pitch:rf(1.5,4), hole_position:rf(0.65,0.85), inside:true, cycles:1 }) },
          noise(rf(1,2.5), rf(8,15)),
          rot(pick([120,180,270])),
          damp(rf(0.008,0.015), rf(40,60)),
        ], sw: 0.1 };
      },

      // ── TORUS + stretch (wide paper fill) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('torus', { surface:'torus', major_radius:rf(90,130), minor_radius:rf(30,55), v_lines:rint(35,55), view_angle_x:rf(20,45), view_angle_y:rf(10,35) }) },
          { kind:'single', mod: mm('stretch', { scale_x:rf(1.8,3.0), scale_y:1.0 }) },
        ], sw: 0.1,
      }),

      // ── KLEIN + rotation (dense mesh, top experiment result) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('klein_bottle', { surface:'klein', major_radius:rf(80,120), minor_radius:rf(30,50), v_lines:rint(40,60), view_angle_x:rf(25,45), view_angle_y:rf(15,35) }) },
          rot(360),
        ], sw: 0.1,
      }),

      // ── FIGURE8 + stretch ──
      () => ({
        steps: [
          { kind:'single', mod: mm('figure8', { surface:'figure8', major_radius:rf(90,130), minor_radius:rf(30,50), v_lines:rint(35,55), view_angle_x:rf(15,40), view_angle_y:rf(5,25) }) },
          { kind:'single', mod: mm('stretch', { scale_x:rf(1.5,2.5), scale_y:rf(0.8,1.0) }) },
        ], sw: 0.1,
      }),

      // ── MOBIUS + rotation + scale ──
      () => ({
        steps: [
          { kind:'single', mod: mm('mobius', { surface:'mobius', major_radius:rf(100,140), width:rf(40,70), v_lines:rint(35,55), view_angle_x:rf(30,50), view_angle_y:rf(15,30) }) },
          { kind:'single', mod: mm('scale', { start_scale:1.0, end_scale:rf(0.3,0.5) }) },
          rot(pick([180,270,360])),
        ], sw: 0.1,
      }),

      // ── LISSAJOUS high ratio (6:5, 7:8, 9:8) ──
      () => {
        const [a,b] = pick([[6,5],[7,8],[9,8],[8,7],[7,6]]);
        return { steps: [
          { kind:'single', mod: mm('lissajous', { freq_x:a, freq_y:b, amp_x:rf(100,140), amp_y:rf(100,140), phase:rf(30,80), cycles:rint(2,4) }) },
          noise(rf(1,2.5), rf(8,14)),
        ], sw: 0.1 };
      },

      // ── LISSAJOUS + damping + stretch ──
      () => {
        const [a,b] = pick([[5,4],[7,6],[4,3],[9,8]]);
        return { steps: [
          { kind:'single', mod: mm('lissajous', { freq_x:a, freq_y:b, amp_x:rf(90,130), amp_y:rf(90,130), phase:rf(40,75), cycles:rint(2,4) }) },
          damp(rf(0.008,0.015), rf(40,60)),
          { kind:'single', mod: mm('stretch', { scale_x:rf(1.3,2.0), scale_y:1.0 }) },
        ], sw: 0.12 };
      },

      // ── ELLIPSE + spiral_arc ──
      () => ({
        steps: [
          { kind:'single', mod: mm('ellipse', { radius_x:rf(40,70), radius_y:rf(25,45), end_radius_x:rf(15,30), end_radius_y:rf(10,20), cycles:rint(60,120), rotation:rf(0,45) }) },
          sparc(rf(15,25), rf(140,200), pick([720,1080,1440])),
        ], sw: 0.1,
      }),

      // ── ELLIPSE deep: bend + rotation + noise ──
      () => ({
        steps: [
          { kind:'single', mod: mm('ellipse', { radius_x:rf(100,160), radius_y:rf(60,100), end_radius_x:rf(30,60), end_radius_y:rf(20,40), cycles:rint(80,150), rotation:rf(0,60) }) },
          bend(rf(180,260), pick([120,180,200])),
          rot(pick([120,180,270])),
          noise(rf(1,3), rf(6,12)),
        ], sw: 0.08,
      }),

      // ── RACK + bend + rotation (cloud lobes) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('rack', { teeth:rint(20,40), tooth_pitch:rf(4,8), hole_position:rf(0.6,0.8), straight_length:rf(150,250), cycles:rint(2,5) }) },
          bend(rf(150,250), pick([180,200,240])),
          rot(pick([180,270,360])),
        ], sw: 0.12,
      }),

      // ── RACK + spiral_arc ──
      () => ({
        steps: [
          { kind:'single', mod: mm('rack', { teeth:rint(25,40), tooth_pitch:rf(3,6), hole_position:rf(0.55,0.75), straight_length:rf(120,200), cycles:rint(3,5) }) },
          sparc(rf(20,35), rf(150,200), pick([720,1080])),
        ], sw: 0.1,
      }),

      // ── RAIL + arc + rotation ──
      () => ({
        steps: [
          { kind:'single', mod: mm('spirograph_rail', { rolling_teeth:rint(25,45), tooth_pitch:rf(3,6), hole_position:rf(0.55,0.8), rail_length:rf(200,400), cycles:rint(1,3) }) },
          arc(rf(150,250), pick([180,270])),
          rot(pick([180,270,360])),
        ], sw: 0.12,
      }),

      // ── RAIL + stretch (fill wide paper) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('spirograph_rail', { rolling_teeth:rint(30,50), tooth_pitch:rf(3,5), hole_position:rf(0.6,0.8), rail_length:rf(250,400), cycles:rint(1,3) }) },
          { kind:'single', mod: mm('stretch', { scale_x:rf(1.5,2.5), scale_y:rf(0.8,1.2) }) },
          rot(pick([90,180])),
        ], sw: 0.1,
      }),

      // ── POLYGON + spiral_arc + noise ──
      () => ({
        steps: [
          { kind:'single', mod: mm('polygon', { sides:pick([5,6,7,8]), radius:rf(25,45), rotation:0, cycles:rint(3,6) }) },
          sparc(rf(15,25), rf(140,180), pick([720,1080,1440])),
          noise(rf(1,2), rf(8,14)),
        ], sw: 0.1,
      }),

      // ── STAR + scale + rotation (shrinking star spiral) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('star_shape', { points:pick([5,6,7,8,9]), outer_radius:rf(100,150), inner_radius:rf(25,55), rotation:0, cycles:rint(3,5) }) },
          { kind:'single', mod: mm('scale', { start_scale:1.3, end_scale:rf(0.2,0.4) }) },
          rot(pick([270,360,540])),
        ], sw: 0.12,
      }),

      // ── STAR deep: arc + noise + damping ──
      () => ({
        steps: [
          { kind:'single', mod: mm('star_shape', { points:pick([5,7,8]), outer_radius:rf(50,80), inner_radius:rf(15,30), rotation:0, cycles:rint(2,4) }) },
          arc(rf(150,220), pick([180,270])),
          noise(rf(1.5,3), rf(6,10)),
          damp(rf(0.01,0.02), rf(30,50)),
        ], sw: 0.1,
      }),

      // ── LINE + spiral_arc + noise (textured spiral) ──
      () => ({
        steps: [
          { kind:'single', mod: mm('line', { length:rf(80,180), angle:0, cycles:rint(2,4) }) },
          sparc(rf(15,25), rf(140,180), pick([720,1080,1440])),
          noise(rf(2,5), rf(4,8)),
        ], sw: 0.12,
      }),

      // ── ROSE + noise + damping ──
      () => {
        const [p,d] = pick([[5,2],[7,3],[8,3],[5,3],[7,4]]);
        return { steps: [
          { kind:'single', mod: mm('rose', { petals:p, denom:d, radius:rf(100,140), cycles:rint(2,4) }) },
          noise(rf(2,4), rf(6,12)),
          damp(rf(0.01,0.02), rf(40,60)),
        ], sw: 0.12 };
      },

      // ── SPHERE + arc + rotation ──
      () => ({
        steps: [
          { kind:'single', mod: mm('sphere', { surface:'sphere', major_radius:rf(50,80), v_lines:rint(25,40) }) },
          arc(rf(150,220), pick([180,270])),
          rot(pick([180,270,360])),
        ], sw: 0.12,
      }),

      // ── RIBBON + rotation ──
      () => ({
        steps: [
          { kind:'single', mod: mm('ribbon', { surface:'ribbon', major_radius:rf(90,130), width:rf(40,60), twists:pick([2,3,4]), v_lines:rint(35,50), view_angle_x:rf(25,40), view_angle_y:rf(10,25) }) },
          rot(360),
        ], sw: 0.1,
      }),

      // ── SPIRAL_SHAPE + noise + rotation ──
      () => ({
        steps: [
          { kind:'single', mod: mm('spiral_shape', { start_radius:rf(3,8), end_radius:rf(120,180), turns:rf(4,8), cycles:1 }) },
          noise(rf(3,8), rf(4,10)),
          rot(pick([180,360,540])),
        ], sw: 0.12,
      }),

      // ── 1K EXPERIMENT TOP SCORERS ──

      // Ellipse + rotation (score 1344)
      () => ({
        steps: [
          { kind:'single', mod: mm('ellipse', { radius_x:rf(100,170), radius_y:rf(60,120), end_radius_x:rf(25,55), end_radius_y:rf(15,40), cycles:rint(80,180), rotation:rf(0,60) }) },
          rot(pick([90,120,180,270,360])),
        ], sw: 0.1,
      }),

      // Line + bend + rotation (score 1344, perfect)
      () => ({
        steps: [
          { kind:'single', mod: mm('line', { length:rf(100,250), angle:rf(0,30), cycles:rint(2,5) }) },
          bend(rf(120,250), pick([120,180,240,270])),
          rot(pick([180,270,360])),
        ], sw: 0.12,
      }),

      // Line deep: damping + stretch + spiral_arc + noise (score 1341)
      () => ({
        steps: [
          { kind:'single', mod: mm('line', { length:rf(80,180), angle:0, cycles:rint(2,4) }) },
          damp(rf(0.008,0.018), rf(30,55)),
          { kind:'single', mod: mm('stretch', { scale_x:rf(1.2,2.0), scale_y:rf(0.8,1.2) }) },
          sparc(rf(15,25), rf(140,190), pick([720,1080])),
          noise(rf(1,3), rf(6,10)),
        ], sw: 0.1,
      }),

      // Klein + damping + spiral_arc (score 1303)
      () => ({
        steps: [
          { kind:'single', mod: mm('klein_bottle', { surface:'klein', major_radius:rf(80,120), minor_radius:rf(30,50), v_lines:rint(35,55), view_angle_x:rf(25,45), view_angle_y:rf(15,35) }) },
          damp(rf(0.008,0.015), rf(35,55)),
          sparc(rf(20,35), rf(150,200), pick([360,720])),
        ], sw: 0.1,
      }),

      // Guilloche + scale + rotation (score 1319)
      () => {
        const primes = [17,23,31,37,41,53,59,67,71];
        return { steps: [
          { kind:'single', mod: mm('guilloche', {
            inner:rf(50,90), outer:rf(170,240), nodes:rint(80,150), div:pick(primes),
            n0:rint(4,10), h0:rf(6,18), n1:rint(8,16), h1:rf(8,22),
          })},
          { kind:'single', mod: mm('scale', { start_scale:1.0, end_scale:rf(0.4,0.7) }) },
          rot(pick([120,180,270,360])),
        ], sw: 0.08 };
      },

      // GROUP: star_shape + ellipse (score 1338)
      () => ({
        steps: [
          { kind:'group', branches: [
            [mm('star_shape', { points:pick([5,6,7,8]), outer_radius:rf(60,100), inner_radius:rf(20,40), rotation:0, cycles:rint(2,4) })],
            [mm('ellipse', { radius_x:rf(80,130), radius_y:rf(50,90), end_radius_x:rf(20,45), end_radius_y:rf(15,35), cycles:rint(60,120), rotation:rf(0,45) })],
          ]},
          rot(pick([90,120,180])),
        ], sw: 0.1,
      }),

      // GROUP: guilloche + ellipse + polygon (score 1324)
      () => {
        const primes = [17,23,31,37,41,53];
        return { steps: [
          { kind:'group', branches: [
            [mm('guilloche', { inner:rf(40,70), outer:rf(130,180), nodes:rint(60,100), div:pick(primes), n0:rint(3,7), h0:rf(5,12), n1:rint(6,12), h1:rf(6,15) })],
            [mm('ellipse', { radius_x:rf(50,80), radius_y:rf(30,55), end_radius_x:rf(15,30), end_radius_y:rf(10,25), cycles:rint(40,80), rotation:0 })],
            [mm('polygon', { sides:pick([5,6,7,8]), radius:rf(30,50), rotation:0, cycles:rint(2,4) })],
          ]},
        ], sw: 0.1 };
      },

      // GROUP: gear + polygon (score 1322)
      () => {
        const fixed = pick([96,105,120]);
        const rolling = pick([36,40,45,52].filter(r => r < fixed));
        return { steps: [
          { kind:'group', branches: [
            [mm('spirograph_gear', { fixed_teeth:fixed, rolling_teeth:rolling, tooth_pitch:rf(3,6), hole_position:rf(0.55,0.75), inside:true, cycles:1 })],
            [mm('polygon', { sides:pick([5,6,7,8]), radius:rf(30,55), rotation:0, cycles:rint(2,4) })],
          ]},
          rot(pick([90,180,270])),
        ], sw: 0.1 };
      },
    ];

    // Avoid repeating recent recipes — exclude last 40 picks
    const recent = recentRecipes.current;
    let idx;
    const available = recipes.map((_,i) => i).filter(i => !recent.includes(i));
    idx = available.length > 0 ? pick(available) : Math.floor(R() * recipes.length);
    recent.push(idx);
    if (recent.length > 40) recent.splice(0, recent.length - 40);
    const recipe = recipes[idx]();
    setSteps(recipe.steps);
    setSel({ step: 0 });
    const sym = recipe.sym || (R() > 0.55 ? pick([3,4,5,6,8]) : 1);
    setSymmetry({ n_fold: sym, mirror: sym > 1 && R() > 0.6 });
    setSampling({ initial_samples: 80000, output_samples: 12000, scroll_repeats: 1 });
    setOutput(prev => ({ ...prev, stroke_width: recipe.sw || 0.12 }));
    regenFlag.current = true;
  };

  const refreshIniFiles = async () => {
    try { const res = await fetch('/api/ini-files'); setIniFiles(await res.json()); } catch {}
  };

  const openFileBrowser = () => {
    setIniSearch('');
    setConfirmDelete(null);
    setShowFileBrowser(true);
    refreshIniFiles();
  };

  const deleteIniFile = async (filePath) => {
    try {
      const res = await fetch('/api/delete-ini?path=' + encodeURIComponent(filePath), { method: 'DELETE' });
      if (res.ok) {
        setConfirmDelete(null);
        refreshIniFiles();
        if (loadedFile === filePath) setLoadedFile('');
      }
    } catch {}
  };

  const loadIniFile = async (filePath) => {
    setGenerating(true);
    setStatus('Loading ' + filePath + '...');
    const t0 = Date.now();
    try {
      const res = await fetch('/api/load-ini?path=' + encodeURIComponent(filePath));
      if (!res.ok) throw new Error('Failed to load');
      const data = await res.json();

      // Try to populate the pipeline UI from parsed data
      const newSteps = [];
      for (const entry of data.pipeline) {
        if (entry.type === 'group' && entry.branches) {
          // Reconstruct group with branches
          const branches = entry.branches.map(branch =>
            branch.map(mod => {
              const id = ++idCounter.current;
              const def = modules[mod.type];
              const params = { type: mod.type };
              if (def) { for (const [k, v] of Object.entries(def.params)) { params[k] = v.default; } }
              for (const [k, v] of Object.entries(mod.params)) { params[k] = v; }
              return { id, type: mod.type, params };
            })
          );
          newSteps.push({ kind: 'group', branches });
        } else {
          const id = ++idCounter.current;
          const def = modules[entry.type];
          const params = { type: entry.type };
          if (def) { for (const [k, v] of Object.entries(def.params)) { params[k] = v.default; } }
          for (const [k, v] of Object.entries(entry.params)) { params[k] = v; }
          newSteps.push({ kind: 'single', mod: { id, type: entry.type, params } });
        }
      }
      if (newSteps.length > 0) {
        setSteps(newSteps);
        setSel({ step: 0 });
      }

      // Reset all settings to defaults, then apply file's values
      const defOutput = { stroke_width: 0.3, stroke_color: '#000000', background_color: '#ffffff' };
      setOutput({ ...defOutput, ...data.output.stroke_color && { stroke_color: data.output.stroke_color },
        ...data.output.stroke_width && { stroke_width: data.output.stroke_width },
        ...data.output.background_color && { background_color: data.output.background_color } });
      setSymmetry({ n_fold: data.symmetry.n_fold || 1, mirror: data.symmetry.mirror || false });
      setSampling({ scroll_repeats: data.sampling.scroll_repeats || 1, initial_samples: 80000, output_samples: 12000 });
      setLoadedFile(filePath);
      // Update tab name to match loaded file
      const tabName = filePath.replace('.ini','').replace(/.*\//,'').replace(/_/g,' ');
      setTabs(prev => prev.map(t => t.id === activeTabId ? {...t, name: tabName} : t));
      setStatus(`Loaded ${filePath}`);
      regenFlag.current = true;
      setRegenTrigger(c => c + 1);
    } catch (e) {
      setStatus('Error: ' + e.message);
      setGenerating(false);
    }
  };

  if (!modules) return h('div', {id:'sidebar'}, h('div', {className:'sidebar-header'}, h('h1',null,'Loading...')));

  const generators = Object.entries(modules).filter(([_,v]) => v.category === 'generator');
  const transforms = Object.entries(modules).filter(([_,v]) => v.category === 'transform');
  const activeMod = selectedMod;
  const activeModDef = activeMod ? modules[activeMod.type] : null;

  return [
    // ---- Sidebar (portaled) ----
    ReactDOM.createPortal(h('div', { key:'sb', style:{display:'flex',flexDirection:'column',height:'100%'} },
      h('div', {className:'sidebar-header'},
        h('h1', null, 'Spirograph Studio'),
        h('p', null, plotterActive ? 'Plotter composition' : 'Modular pattern generator'),
      ),

      // ---- Plotter sidebar (when plotter tab is active) ----
      plotterActive ? h(React.Fragment, null,
        // Composition list
        h('div', {className:'section', style:{flex:1,overflowY:'auto'}},
          h('div', {className:'section-title'}, `Patterns on page (${plotterPatterns.length})`),
          plotterPatterns.length === 0 ? h('div', {style:{padding:'16px',color:'var(--muted)',fontSize:'0.78rem',textAlign:'center'}},
            'No patterns added yet.', h('br'), 'Switch to a pattern tab and click "+ Plotter"') : null,
          plotterPatterns.map(pp => {
            const isSel = pp.id === selectedPlaced;
            return h('div', {key:pp.id, style:{padding:'8px 12px',margin:'4px 8px',borderRadius:'6px',cursor:'pointer',
              background: isSel ? 'rgba(124,92,252,0.12)' : 'var(--card)',
              border: isSel ? '1px solid var(--accent)' : '1px solid var(--border)'},
              onClick:()=>setSelectedPlaced(isSel ? null : pp.id)},
              h('div', {style:{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'4px'}},
                h('span', {style:{fontWeight:600,fontSize:'0.78rem'}}, pp.name),
                h('span', {style:{cursor:'pointer',color:'var(--muted)',fontSize:'0.8rem',padding:'0 4px'},
                  title:'Remove from plotter',
                  onClick:e=>{e.stopPropagation(); removePlotterPattern(pp.id);}}, '\u00d7'),
              ),
              h('div', {style:{display:'flex',gap:'8px',alignItems:'center',fontSize:'0.68rem',color:'var(--muted)'},
                onClick:e=>e.stopPropagation(), onMouseDown:e=>e.stopPropagation()},
                h('label', {onClick:e=>e.stopPropagation()}, 'Scale ',
                  h('input', {type:'number', value:pp.scale.toFixed(2), step:0.1, min:0.1, max:10,
                    style:{width:'50px',background:'var(--bg)',border:'1px solid var(--border)',color:'var(--text)',
                      borderRadius:'3px',padding:'2px 4px',fontSize:'0.68rem'},
                    onClick:e=>e.stopPropagation(), onMouseDown:e=>e.stopPropagation(),
                    onChange:e=>{const v=parseFloat(e.target.value); if(!isNaN(v)&&v>0) updatePlotterPattern(pp.id,{scale:v});}})),
                h('label', {onClick:e=>e.stopPropagation()}, 'Rot ',
                  h('input', {type:'number', value:Math.round(pp.rotation), step:15,
                    style:{width:'45px',background:'var(--bg)',border:'1px solid var(--border)',color:'var(--text)',
                      borderRadius:'3px',padding:'2px 4px',fontSize:'0.68rem'},
                    onClick:e=>e.stopPropagation(), onMouseDown:e=>e.stopPropagation(),
                    onChange:e=>{const v=parseFloat(e.target.value); if(!isNaN(v)) updatePlotterPattern(pp.id,{rotation:v});}}),
                  '\u00b0'),
              ),
            );
          }),
        ),
      ) : null,

      // ---- Pattern editor sidebar (when pattern tab is active) ----
      !plotterActive ? h(React.Fragment, null,

      // Pipeline tree
      h('div', {className:'section'},
        h('div', {className:'section-title'}, 'Pipeline'),
        h('div', {className:'pipeline-area'},
          (() => {
            const isDragging = !!dragSrc;

            if (steps.length === 0) {
              return h('div', {className:'placeholder-slot' + (isDragging ? ' drag-over' : ''),
                onDragOver:(e) => { e.preventDefault(); e.stopPropagation(); },
                onDrop:(e) => { e.preventDefault(); e.stopPropagation(); if (dragSrc?.type==='new') addStep(dragSrc.modType); setDragSrc(null); setDropTarget(null); },
                onClick:() => addStep(null)},
                isDragging ? 'drop here' : 'click + or drag a module here');
            }

            // Render a module row or placeholder
            const renderMod = (mod, stepIdx, branchIdx, subIdx) => {
              if (!mod) {
                const isOver = isDragging && dropTarget?.stepIdx === stepIdx && dropTarget?.mode === 'on';
                return h('div', {className:'placeholder-slot' + (isOver ? ' drag-over' : ''),
                  onDragOver:(e) => { e.preventDefault(); e.stopPropagation(); setDropTarget({stepIdx, mode:'on'}); },
                  onDrop:(e) => { e.preventDefault(); e.stopPropagation(); if (dragSrc?.type==='new') fillPlaceholder(stepIdx, branchIdx, subIdx, dragSrc.modType); setDragSrc(null); setDropTarget(null); },
                  }, 'drop module here');
              }
              const def = modules[mod.type];
              const cat = def?.category || '?';
              const isActive = sel && sel.step === stepIdx && sel.branch === branchIdx && sel.sub === subIdx;
              return h('div', {className:'pipeline-step' + (isActive ? ' active' : ''),
                onClick:() => setSel({ step: stepIdx, branch: branchIdx, sub: subIdx })},
                h('span', {className:'step-label'}, def?.label || mod.type),
                h('span', {className:'step-cat'}, cat === 'generator' ? 'gen' : 'xfm'),
                h('span', {className:'x', onClick:(e)=>{e.stopPropagation();removeAt(stepIdx,branchIdx,subIdx);}}, '\u00d7'),
              );
            };

            const nodes = [];
            steps.forEach((step, si) => {
              const dt = dropTarget;
              const dropClass = (dt && dt.stepIdx === si ? (dt.mode === 'on' ? ' drop-indicator-on' : dt.mode === 'before' ? ' drop-indicator-before' : ' drop-indicator-after') : '');

              if (step.kind === 'single') {
                nodes.push(h('div', {key:`step-${si}`, className:'serial-step pipeline-step-wrap' + dropClass,
                  draggable:!!step.mod,
                  onDragStart: step.mod ? () => onStepDragStart(si) : undefined,
                  onDragOver:(e) => onStepDragOver(e, si), onDrop:onDrop, onDragEnd:onDragEnd},
                  step.mod ? h('span', {className:'grip'}, '\u2261') : null,
                  renderMod(step.mod, si, undefined, undefined),
                ));
              } else {
                // Group — branches with tree lines
                nodes.push(h('div', {key:`grp-${si}`, className:'serial-step group-wrapper' + dropClass,
                  draggable:true,
                  onDragStart:() => onStepDragStart(si),
                  onDragOver:(e) => onStepDragOver(e, si), onDrop:onDrop, onDragEnd:onDragEnd},
                  h('div', {className:'group-label'}, 'simultaneous'),
                  h('div', {className:'group-children'},
                    step.branches.map((branch, bi) =>
                      h('div', {key:`b-${bi}`, className:'tree-node', draggable:true,
                        onDragStart:(e) => onBranchDragStart(e, si, bi), onDragEnd:onDragEnd},
                        h('div', {className:'tree-line'}),
                        h('div', {className:'tree-content'},
                          // Each branch is its own serial chain
                          branch.map((mod, mi) => h(React.Fragment, {key: mod ? mod.id : `ph-${bi}-${mi}`},
                            renderMod(mod, si, bi, mi),
                            mi < branch.length - 1 ? h('div', {className:'serial-arrow', style:{fontSize:'0.55rem'}}, '\u25bc') : null,
                          )),
                          h('div', {className:'group-add', style:{fontSize:'0.6rem'},
                            onClick:() => addToBranch(si, bi, null)}, '+ step'),
                        ),
                      ),
                    ),
                  ),
                  h('div', {className:'group-add', onClick:() => addBranch(si)}, '+ branch'),
                ));
              }
              // Arrow between serial steps
              if (si < steps.length - 1) {
                nodes.push(h('div', {key:`arr-${si}`, className:'serial-arrow'}, '\u25bc'));
              }
            });

            // Bottom +
            nodes.push(h('div', {key:'add', className:'serial-step'},
              h('div', {className:'placeholder-slot', style:{padding:'4px 8px',fontSize:'0.7rem'},
                onDragOver:(e) => { e.preventDefault(); setDropTarget({stepIdx: steps.length - 1, mode:'after'}); },
                onDrop:onDrop, onDragEnd:onDragEnd,
                onClick:() => addStep(null)}, '+'),
            ));

            return nodes;
          })(),
        ),
      ),

      // Module palette — drag from here
      h('div', {className:'section'},
        h('div', {className:'section-title'}, 'Generators \u2014 drag onto pipeline'),
        h('div', {className:'add-modules'},
          generators.map(([type, def]) => h('button', {key:type, className:'add-btn gen',
            draggable:true,
            onDragStart:() => onPaletteDragStart(type),
            onDragEnd:onDragEnd,
            title:def.desc}, def.label)),
        ),
        h('div', {className:'section-title', style:{marginTop:8}}, 'Transforms \u2014 drag onto pipeline'),
        h('div', {className:'add-modules'},
          transforms.map(([type, def]) => h('button', {key:type, className:'add-btn xfm',
            draggable:true,
            onDragStart:() => onPaletteDragStart(type),
            onDragEnd:onDragEnd,
            title:def.desc}, def.label)),
        ),
      ),

      // Active module params
      activeMod && activeModDef ? h('div', {className:'section'},
        h('div', {className:'section-title'}, activeModDef.label + ' Parameters'),
        h('div', {className:'param-group'},
          (() => {
            const params = activeModDef.params;
            // Build set of drift keys so we skip them in main loop
            const driftKeys = new Set();
            const driftMap = {};  // baseKey -> driftKey
            for (const [k, s] of Object.entries(params)) {
              if (s.drift_for) { driftKeys.add(k); driftMap[s.drift_for] = k; }
            }
            const rows = [];
            for (const [key, spec] of Object.entries(params)) {
              if (driftKeys.has(key)) continue;  // rendered as child of base param
              if (spec.hidden) continue;  // hidden params (e.g. surface type selector)
              const val = activeMod.params[key];
              const hasDrift = !!driftMap[key];
              if (spec.type === 'bool') {
                rows.push(h('div', {key, className:'param-row'},
                  h('label', null, spec.desc),
                  h('input', {type:'checkbox', checked:!!val, onChange:e=>updateParam(sel.step,sel.branch,sel.sub,key,e.target.checked)}),
                ));
                continue;
              }
              if (spec.type === 'str') {
                rows.push(h('div', {key, className:'param-row'},
                  h('label', null, spec.desc),
                  h('input', {type:'text', value:val||'', style:{flex:1,background:'var(--bg)',border:'1px solid var(--border)',color:'var(--text)',borderRadius:'4px',padding:'3px 6px',fontSize:'0.78rem'},
                    onChange:e=>updateParam(sel.step,sel.branch,sel.sub,key,e.target.value)}),
                ));
                continue;
              }
              const step = spec.step || (spec.type==='int' ? 1 : 0.1);
              const parse = v => spec.type==='int' ? parseInt(v) : parseFloat(v);
              // Base param row — with optional drift/oscillation toggle
              // Determine mode: stored state, or auto-detect from params
              let driftMode;
              const storedMode = driftOpen[key];
              if (storedMode !== undefined) {
                driftMode = storedMode; // User has explicitly set this
              } else if (hasDrift) {
                // Auto-detect from params
                if (activeMod.params['osc_'+key]) driftMode = 'osc';
                else if (activeMod.params[driftMap[key]] !== undefined && activeMod.params[driftMap[key]] !== val) driftMode = 'drift';
                else driftMode = '';
              } else {
                driftMode = '';
              }
              const cycleDrift = () => setDriftOpen(prev => {
                // Use whatever is currently displayed
                const cur = prev[key] !== undefined ? prev[key] : driftMode;
                const next = cur === '' ? 'drift' : cur === 'drift' ? 'osc' : '';
                // Reset osc params when turning off
                if (next === '' && activeMod.params['osc_'+key]) {
                  updateParam(sel.step, sel.branch, sel.sub, 'osc_'+key, '');
                }
                return {...prev, [key]: next};
              });
              const driftLabel = driftMode === 'osc' ? '\u25ce' : driftMode === 'drift' ? '\u25be' : '\u25b8';
              rows.push(h('div', {key, className:'param-row'},
                hasDrift ? h('button', {className:'drift-toggle ' + driftMode,
                  title: driftMode === '' ? 'Click for drift' : driftMode === 'drift' ? 'Click for oscillate' : 'Click to disable',
                  onClick:cycleDrift}, driftLabel) : null,
                h('label', null, driftMode === 'osc' ? spec.desc + ' min' : spec.desc),
                h('input', {type:'range', min:spec.min, max:Math.max(spec.max, val), step, value:val,
                  onChange:e=>updateParam(sel.step, sel.branch, sel.sub, key, parse(e.target.value))}),
                h('input', {type:'number', step, value:val,
                  onChange:e=>{ const v = parse(e.target.value); if (!isNaN(v)) updateParam(sel.step, sel.branch, sel.sub, key, v); }}),
              ));
              // Drift row (linear end value)
              if (hasDrift && driftMode === 'drift') {
                const dk = driftMap[key];
                const ds = params[dk];
                const dv = activeMod.params[dk];
                const dstep = ds.step || (ds.type==='int' ? 1 : 0.1);
                const dparse = v => ds.type==='int' ? parseInt(v) : parseFloat(v);
                rows.push(h('div', {key:dk, className:'drift-row'},
                  h('label', null, '\u2192 end'),
                  h('input', {type:'range', min:ds.min, max:Math.max(ds.max, dv), step:dstep, value:dv,
                    onChange:e=>updateParam(sel.step, sel.branch, sel.sub, dk, dparse(e.target.value))}),
                  h('input', {type:'number', step:dstep, value:dv,
                    onChange:e=>{ const v = dparse(e.target.value); if (!isNaN(v)) updateParam(sel.step, sel.branch, sel.sub, dk, v); }}),
                ));
              }
              // Oscillation row (speed + irregularity)
              if (hasDrift && driftMode === 'osc') {
                const dk = driftMap[key];
                const ds = params[dk];
                const dv = activeMod.params[dk];
                const dstep = ds.step || (ds.type==='int' ? 1 : 0.1);
                const dparse = v => ds.type==='int' ? parseInt(v) : parseFloat(v);
                const oscKey = 'osc_' + key;
                const oscVal = activeMod.params[oscKey] || '';
                const oscParts = oscVal ? String(oscVal).split(',').map(Number) : [3, 0.3];
                const oscSpeed = oscParts[0] || 3;
                const oscIrreg = oscParts[1] != null ? oscParts[1] : 0.3;
                const setOsc = (s, ir) => updateParam(sel.step, sel.branch, sel.sub, oscKey, s+','+ir);
                // End value (max of oscillation)
                rows.push(h('div', {key:dk, className:'drift-row'},
                  h('label', null, '\u2194 max'),
                  h('input', {type:'range', min:ds.min, max:Math.max(ds.max, dv), step:dstep, value:dv,
                    onChange:e=>updateParam(sel.step, sel.branch, sel.sub, dk, dparse(e.target.value))}),
                  h('input', {type:'number', step:dstep, value:dv,
                    onChange:e=>{ const v = dparse(e.target.value); if (!isNaN(v)) updateParam(sel.step, sel.branch, sel.sub, dk, v); }}),
                ));
                rows.push(h('div', {key:oscKey+'_spd', className:'drift-row'},
                  h('label', null, 'cycles'),
                  h('input', {type:'range', min:0.5, max:20, step:0.5, value:oscSpeed,
                    onChange:e=>setOsc(parseFloat(e.target.value), oscIrreg)}),
                  h('input', {type:'number', step:0.5, value:oscSpeed, style:{width:'45px'},
                    onChange:e=>{ const v=parseFloat(e.target.value); if(!isNaN(v)&&v>0) setOsc(v, oscIrreg); }}),
                ));
                rows.push(h('div', {key:oscKey+'_irr', className:'drift-row'},
                  h('label', null, 'wobble'),
                  h('input', {type:'range', min:0, max:5, step:0.1, value:oscIrreg,
                    onChange:e=>setOsc(oscSpeed, parseFloat(e.target.value))}),
                  h('input', {type:'number', step:0.1, value:oscIrreg, style:{width:'45px'},
                    onChange:e=>{ const v=parseFloat(e.target.value); if(!isNaN(v)&&v>=0) setOsc(oscSpeed, v); }}),
                ));
              }
            }
            return rows;
          })(),
        ),
      ) : null,

      // Output / Symmetry / Sampling
      h('div', {className:'section'},
        h('div', {className:'section-title'}, 'Output'),
        h('div', {className:'output-row'},
          h('label', null, 'Stroke'),
          h('input', {type:'color', value:output.stroke_color, onChange:e=>setOutput({...output,stroke_color:e.target.value})}),
          h('label', null, 'Width'),
          h('input', {type:'number', value:output.stroke_width, min:0.05, max:3, step:0.05,
            onChange:e=>setOutput({...output,stroke_width:parseFloat(e.target.value)})}),
        ),
        h('div', {className:'output-row'},
          h('label', null, 'Background'),
          h('input', {type:'color', value:output.background_color, onChange:e=>setOutput({...output,background_color:e.target.value})}),
        ),
        h('div', {className:'output-row'},
          h('label', null, 'Symmetry'),
          h('input', {type:'number', value:symmetry.n_fold, min:1, max:12, step:1,
            onChange:e=>setSymmetry({...symmetry,n_fold:parseInt(e.target.value)})}),
          h('label', null, 'Mirror'),
          h('input', {type:'checkbox', checked:symmetry.mirror, onChange:e=>setSymmetry({...symmetry,mirror:e.target.checked})}),
        ),
        h('div', {className:'output-row'},
          h('label', null, 'Scroll'),
          h('input', {type:'number', value:sampling.scroll_repeats, min:1, max:20, step:1,
            onChange:e=>setSampling({...sampling,scroll_repeats:parseFloat(e.target.value)})}),
          h('span', {style:{fontSize:'0.7rem',color:'var(--muted)'}}, 'repeats'),
        ),
        h('div', {className:'output-row'},
          h('label', null, 'Quality'),
          ...[
            {label:'Draft', i:80000, o:12000},
            {label:'Fine', i:300000, o:40000},
            {label:'Ultra', i:1000000, o:100000},
          ].map(q => h('button', {key:q.label,
            style:{padding:'2px 8px',borderRadius:'4px',fontSize:'0.68rem',fontWeight:600,cursor:'pointer',
              border: sampling.initial_samples===q.i ? '1px solid var(--accent)' : '1px solid var(--border)',
              background: sampling.initial_samples===q.i ? 'rgba(124,92,252,0.15)' : 'var(--bg)',
              color: sampling.initial_samples===q.i ? 'var(--text)' : 'var(--muted)'},
            onClick:()=>setSampling({...sampling, initial_samples:q.i, output_samples:q.o})},
            q.label)),
        ),
      ),

      // Action buttons
      h('div', {className:'btn-row'},
        h('button', {className:'btn btn-generate', onClick:generate, disabled:generating || totalModules===0},
          generating ? 'Generating...' : 'Generate'),
        h('button', {className:'btn btn-secondary', onClick:() => { setShowSave(!showSave); setSaveName(loadedFile.replace('.ini','') || ''); }}, 'Save'),
        h('button', {className:'btn btn-secondary', disabled:!pointData, onClick: async () => {
          // Generate SVG on demand from current pipeline
          const stepsData = steps
            .filter(s => s.kind === 'single' ? s.mod !== null : s.branches.some(b => b.some(m => m !== null)))
            .map(s => {
              if (s.kind === 'single') return { kind: 'single', params: s.mod.params };
              return { kind: 'group', branches: s.branches.map(b => b.filter(m => m !== null).map(m => m.params)).filter(b => b.length > 0) };
            });
          try {
            const res = await fetch('/api/generate', {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ steps: stepsData, output, sampling,
                symmetry: symmetry.n_fold > 1 || symmetry.mirror ? symmetry : {},
              }),
            });
            const svg = await res.text();
            const blob = new Blob([svg], {type:'image/svg+xml'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = (loadedFile || 'spirograph').replace('.ini','') + '.svg';
            a.click(); URL.revokeObjectURL(url);
          } catch(e) { setStatus('Export error: ' + e.message); }
        }}, 'Export SVG'),
        h('button', {className:'btn btn-secondary', onClick:randomize}, 'Random'),
        !plotterActive ? h('button', {className:'btn btn-secondary', disabled:!pointData,
          style:{background:'rgba(124,92,252,0.15)', borderColor:'var(--accent)'},
          onClick:addToPlotter}, '+ Plotter') : null,
      ),
      // Plotter panel is a right flyout (rendered below in portal)
      showSave ? h('div', {style:{padding:'4px 16px 8px',display:'flex',gap:'6px',alignItems:'center'}},
        h('input', {type:'text', value:saveName, placeholder:'filename', disabled:saving,
          style:{flex:1,background:'var(--bg)',border:'1px solid var(--border)',color:'var(--text)',
                 borderRadius:'4px',padding:'5px 8px',fontSize:'0.78rem',outline:'none'},
          onChange:e=>setSaveName(e.target.value),
          onKeyDown:e=>{ if (e.key==='Enter' && !saving) saveConfig(); if (e.key==='Escape') setShowSave(false); },
          autoFocus:true}),
        h('span', {style:{color:'var(--muted)',fontSize:'0.72rem'}}, '.ini'),
        h('button', {style:{background:'var(--accent)',color:'#fff',border:'none',borderRadius:'4px',
                            padding:'5px 10px',fontSize:'0.75rem',fontWeight:600,cursor:'pointer',
                            opacity: saving ? 0.6 : 1},
          disabled:saving, onClick:saveConfig}, saving ? 'Saving...' : 'Save'),
      ) : null,
      loadedFile ? h('div', {style:{padding:'0 16px 8px',fontSize:'0.7rem',color:'var(--muted)'}},
        'Loaded: ', loadedFile) : null,
      ) : null, // end !plotterActive conditional
    ), document.getElementById('sidebar')),

    // ---- Right panel: tabs (Files / Plotter) + content ----
    ReactDOM.createPortal(h(React.Fragment, null,
      // Vertical tabs on the edge
      h('div', {className:'right-tabs'},
        h('div', {className:'right-tab' + (showFileBrowser ? ' active' : ''),
          onClick:() => {
            if (showFileBrowser) { setShowFileBrowser(false); }
            else { setShowFileBrowser(true); refreshIniFiles(); }
          }}, 'Files'),
      ),
      // Panel content
      h('div', {className:'filebrowser' + (showFileBrowser ? '' : ' collapsed')},
        // Files content
        showFileBrowser ? h(React.Fragment, null,
          h('div', {className:'fb-header'},
            h('h2', null, 'Configurations'),
            h('button', {className:'fb-close', onClick:()=>setShowFileBrowser(false)}, '\u00d7'),
          ),
          h('div', {className:'fb-search'},
            h('input', {placeholder:'Search...', value:iniSearch,
              onChange:e=>{setIniSearch(e.target.value); setConfirmDelete(null);}}),
          ),
          h('div', {className:'fb-body'}, (() => {
            const filtered = iniFiles.filter(f => !iniSearch || f.path.toLowerCase().includes(iniSearch.toLowerCase()));
            if (filtered.length === 0) return h('div', {className:'fb-empty'}, 'No matching .ini files');
            const folders = {};
            for (const f of filtered) {
              const key = f.dir || '/';
              if (!folders[key]) folders[key] = [];
              folders[key].push(f);
            }
            const sortedKeys = Object.keys(folders).sort((a, b) => {
              if (a === '/') return -1; if (b === '/') return 1; return a.localeCompare(b);
            });
            return h(React.Fragment, null,
              sortedKeys.map(folder => {
                const isOpen = foldersOpen[folder] !== false;
                return h(React.Fragment, {key:folder},
                  h('div', {className:'fb-group-label',
                    onClick:()=>setFoldersOpen(prev=>({...prev,[folder]:!isOpen}))},
                    h('span', {className:'fb-caret'+(isOpen?' open':'')}, '\u25b6'),
                    (folder === '/' ? 'root' : folder) + ' (' + folders[folder].length + ')',
                  ),
                  isOpen ? folders[folder].map(f => h(FileRow, {key:f.path, f, loadIniFile, confirmDelete, setConfirmDelete, deleteIniFile})) : null,
                );
              }),
            );
          })()),
        ) : null,
        // Plotter content
        plotterActive ? h('div', {className:'plotter-content'},
          h('div', {style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px'}},
            h('h3', null, 'AxiDraw'),
            h('button', {onClick:()=>setShowPlotter(false), style:{background:'none',border:'none',color:'var(--muted)',fontSize:'1.2rem',cursor:'pointer',padding:'4px'}}, '\u00d7'),
        ),

        // Model & Port
        h('div', {className:'pg'},
          h('div', {className:'pg-title'}, 'Device'),
          h('select', {value:pOpts.model, style:{marginBottom:'8px'}, onChange:e=>pSet('model',Number(e.target.value))},
            Object.entries(plotterModels).map(([id, m]) => h('option', {key:id, value:id}, m.label))),
          h('label', null, h('span', null, 'Port'),
            h('input', {type:'text', value:pOpts.port, style:{width:'120px'}, placeholder:'auto',
              onChange:e=>pSet('port',e.target.value)})),
          plotterModels[pOpts.model] ? h('div', {className:'device-info'},
            `Paper: ${plotterModels[pOpts.model].width}" \u00d7 ${plotterModels[pOpts.model].height}"`,
            h('br'),
            `Draw area: ${(plotterModels[pOpts.model].width-2*pOpts.margin).toFixed(1)}" \u00d7 ${(plotterModels[pOpts.model].height-2*pOpts.margin).toFixed(1)}"`,
          ) : null,
        ),

        // Speed & Motion
        h('div', {className:'pg'},
          h('div', {className:'pg-title'}, 'Speed & Motion'),
          h('label', null, h('span', null, 'Drawing speed (%)'), h('input', {type:'number',min:1,max:110,value:pOpts.penDownSpeed, onChange:e=>pSet('penDownSpeed',Number(e.target.value))})),
          h('label', null, h('span', null, 'Travel speed (%)'), h('input', {type:'number',min:1,max:110,value:pOpts.penUpSpeed, onChange:e=>pSet('penUpSpeed',Number(e.target.value))})),
          h('label', null, h('span', null, 'Acceleration'),
            h('select', {value:pOpts.accelFactor, style:{width:'120px'}, onChange:e=>pSet('accelFactor',Number(e.target.value))},
              h('option', {value:100}, 'Maximum'), h('option', {value:75}, 'High'),
              h('option', {value:50}, 'Standard'), h('option', {value:35}, 'Slow'), h('option', {value:10}, 'Very slow'))),
          h('label', null, h('span', null, 'Constant speed'),
            h('input', {type:'checkbox', checked:pOpts.constSpeed, onChange:e=>pSet('constSpeed',e.target.checked)})),
        ),

        // Pen
        h('div', {className:'pg'},
          h('div', {className:'pg-title'}, 'Pen'),
          h('label', null, h('span', null, 'Up height (%)'), h('input', {type:'number',min:0,max:100,value:pOpts.penUpPosition, onChange:e=>pSet('penUpPosition',Number(e.target.value))})),
          h('label', null, h('span', null, 'Down height (%)'), h('input', {type:'number',min:0,max:100,value:pOpts.penDownPosition, onChange:e=>pSet('penDownPosition',Number(e.target.value))})),
          h('label', null, h('span', null, 'Lift speed'),
            h('select', {value:pOpts.penLiftRate, style:{width:'120px'}, onChange:e=>pSet('penLiftRate',Number(e.target.value))},
              h('option', {value:400}, 'Maximum'), h('option', {value:150}, 'Standard'),
              h('option', {value:100}, 'Slow'), h('option', {value:50}, 'Very slow'))),
          h('label', null, h('span', null, 'Lower speed'),
            h('select', {value:pOpts.penLowerRate, style:{width:'120px'}, onChange:e=>pSet('penLowerRate',Number(e.target.value))},
              h('option', {value:400}, 'Maximum'), h('option', {value:150}, 'Standard'),
              h('option', {value:100}, 'Slow'), h('option', {value:50}, 'Very slow'))),
          h('label', null, h('span', null, 'Lift delay (ms)'), h('input', {type:'number',min:-500,max:500,value:pOpts.penLiftDelay, onChange:e=>pSet('penLiftDelay',Number(e.target.value))})),
          h('label', null, h('span', null, 'Lower delay (ms)'), h('input', {type:'number',min:-500,max:500,value:pOpts.penLowerDelay, onChange:e=>pSet('penLowerDelay',Number(e.target.value))})),
        ),

        // Options
        h('div', {className:'pg'},
          h('div', {className:'pg-title'}, 'Options'),
          h('label', null, h('span', null, 'Margin (inches)'), h('input', {type:'number',min:0,max:5,step:0.1,value:pOpts.margin, onChange:e=>pSet('margin',Number(e.target.value))})),
          h('label', null, h('span', null, 'Resolution'),
            h('select', {value:pOpts.resolution, style:{width:'120px'}, onChange:e=>pSet('resolution',Number(e.target.value))},
              h('option', {value:1}, 'High (~2870 DPI)'), h('option', {value:2}, 'Low (~1435 DPI)'))),
          h('label', null, h('span', null, 'Auto-rotate'),
            h('input', {type:'checkbox', checked:pOpts.autoRotate, onChange:e=>pSet('autoRotate',e.target.checked)})),
          h('label', null, h('span', null, 'Copies'), h('input', {type:'number',min:1,max:9999,value:pOpts.copies, onChange:e=>pSet('copies',Number(e.target.value))})),
          pOpts.copies > 1 ? h('label', null, h('span', null, 'Delay between (s)'), h('input', {type:'number',min:0,max:3600,value:pOpts.copyDelay, onChange:e=>pSet('copyDelay',Number(e.target.value))})) : null,
          h('label', null, h('span', null, 'Preview only'),
            h('input', {type:'checkbox', checked:pOpts.preview, onChange:e=>pSet('preview',e.target.checked)})),
        ),

        // Manual Controls
        h('div', {className:'pg'},
          h('div', {className:'pg-title'}, 'Manual Control'),
          h('div', {style:{display:'flex',gap:'8px',flexWrap:'wrap',marginBottom:'10px'}},
            ...[['Pen Up','pen_up'],['Pen Down','pen_down'],['Toggle Pen','toggle_pen'],['Home','home']].map(([label, cmd]) =>
              h('button', {key:cmd, className:'p-btn', onClick: async () => {
                try {
                  setStatus(label + '...');
                  await fetch('/api/plot-manual', {method:'POST', headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({command:cmd, model:pOpts.model, port:pOpts.port, penUpPosition:pOpts.penUpPosition, penDownPosition:pOpts.penDownPosition})});
                  setStatus(label + ' done');
                } catch(e) { setStatus('Error: '+e.message); }
              }}, label)),
          ),
          h('div', {style:{display:'flex',gap:'8px',flexWrap:'wrap',marginBottom:'10px'}},
            ...[['Enable Motors','enable_motors'],['Disable Motors','disable_motors']].map(([label, cmd]) =>
              h('button', {key:cmd, className:'p-btn', onClick: async () => {
                try {
                  setStatus(label + '...');
                  await fetch('/api/plot-manual', {method:'POST', headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({command:cmd, model:pOpts.model, port:pOpts.port, penUpPosition:pOpts.penUpPosition, penDownPosition:pOpts.penDownPosition})});
                  setStatus(label + ' done');
                } catch(e) { setStatus('Error: '+e.message); }
              }}, label)),
          ),
          h('div', {className:'pg-title', style:{marginTop:'4px'}}, 'Walk Carriage'),
          h('div', {style:{display:'flex',gap:'8px',alignItems:'center'}},
            ...[['X+','walk_x',1],['X\u2013','walk_x',-1],['Y+','walk_y',1],['Y\u2013','walk_y',-1]].map(([label, cmd, dir]) =>
              h('button', {key:label, className:'p-btn', onClick: async () => {
                try {
                  setStatus('Walk ' + label + '...');
                  await fetch('/api/plot-manual', {method:'POST', headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({command:cmd, model:pOpts.model, port:pOpts.port, penUpPosition:pOpts.penUpPosition, penDownPosition:pOpts.penDownPosition, walkDistance: dir * 1.0})});
                  setStatus('Walk done');
                } catch(e) { setStatus('Error: '+e.message); }
              }}, label)),
          ),
        ),

        // Plot action
        h('div', {className:'pg', style:{borderBottom:'none'}},
          h('div', {style:{display:'flex',gap:'10px',alignItems:'center'}},
            h('button', {className:'p-btn primary', disabled:totalModules===0 || (plotterStatus && plotterStatus.plotting),
              onClick:plotToAxidraw},
              plotterStatus && plotterStatus.plotting ? 'Plotting...' : 'Plot to AxiDraw'),
            plotterStatus && plotterStatus.plotting ? h('button', {className:'p-btn danger', onClick:plotStop}, 'STOP') : null,
          ),
          plotterStatus && plotterStatus.plotting ? h('div', null,
            h('div', {style:{background:'var(--border)',borderRadius:'3px',height:'4px',overflow:'hidden'}},
              h('div', {style:{width:(plotterStatus.progress*100)+'%',height:'100%',background:'var(--accent)',transition:'width 0.3s'}})),
            h('div', {style:{fontSize:'0.6rem',color:'var(--muted)',marginTop:'2px'}}, plotterStatus.message),
          ) : null,
          plotterStatus && plotterStatus.error ? h('div', {style:{fontSize:'0.6rem',color:'#e74c3c',marginTop:'2px'}}, plotterStatus.error) : null,
        ),
      ) : null, // end plotter-content
      ), // end filebrowser/shared panel div
    ), document.getElementById('right-panel-mount')),

    // ---- Tab bar (portaled) ----
    ReactDOM.createPortal(h(React.Fragment, {key:'tabs'},
      tabs.map(t => h('div', {key:t.id,
        className:'tab-item' + (t.id === activeTabId && !plotterActive ? ' active' : ''),
        onClick:() => switchTab(t.id)},
        t.name,
        tabs.length > 1 ? h('span', {className:'tab-close', onClick:e=>{e.stopPropagation(); closeTab(t.id);}}, '\u00d7') : null,
      )),
      h('div', {className:'tab-add', onClick:addNewTab, title:'New pattern tab'}, '+'),
      h('div', {className:'tab-item tab-plotter' + (plotterActive ? ' active' : ''),
        onClick:switchToPlotter},
        'Plotter', plotterPatterns.length > 0 ? ` (${plotterPatterns.length})` : null,
      ),
    ), document.getElementById('tab-bar')),

    // ---- Toolbar (portaled) ----
    ReactDOM.createPortal(h(React.Fragment, {key:'tb'},
      h('button', {onClick:undo, title:'Undo (Ctrl+Z)', disabled:undoStack.current.length===0,
        style:{background:'none',border:'1px solid var(--border)',color:'var(--muted)',borderRadius:'4px',padding:'2px 8px',cursor:'pointer',fontSize:'0.8rem',opacity:undoStack.current.length?1:0.3}}, '\u21a9'),
      h('button', {onClick:redo, title:'Redo (Ctrl+Shift+Z)', disabled:redoStack.current.length===0,
        style:{background:'none',border:'1px solid var(--border)',color:'var(--muted)',borderRadius:'4px',padding:'2px 8px',cursor:'pointer',fontSize:'0.8rem',opacity:redoStack.current.length?1:0.3}}, '\u21aa'),
      h('div', {className:'spacer'}),
      status ? h('div', {className:'status'}, status) : null,
    ), document.getElementById('toolbar')),

    // ---- Canvas area (portaled) ----
    ReactDOM.createPortal(h(React.Fragment, null,
      generating ? h('div', {className:'spinner-overlay'},
        h('div', {className:'spinner'}),
        h('div', {className:'spinner-label'}, 'Generating pattern...'),
      ) : null,
      (() => {
        const hasTransform = cvOff.x !== 0 || cvOff.y !== 0 || cvRot !== 0 || cvScale !== 1;
        const zBtn = {background:'none',border:'1px solid #666',color:'#ccc',borderRadius:'3px',padding:'1px 7px',fontSize:'0.7rem',cursor:'pointer',fontWeight:600,lineHeight:'1.2'};
        // In plotter tab with selected pattern, zoom targets pattern scale
        const selPPz = plotterActive && selectedPlaced ? plotterPatterns.find(p => p.id === selectedPlaced) : null;
        const scaleVal = selPPz ? selPPz.scale * 100 : cvScale * 100;
        const doScale = (fn) => {
          if (selPPz) updatePlotterPattern(selPPz.id, {scale: fn(selPPz.scale)});
          else setCvScale(fn);
        };
        const infoBar = h('div', {style:{position:'absolute',top:'8px',left:'8px',zIndex:5,display:'flex',gap:'4px',alignItems:'center',
            background:'rgba(0,0,0,0.6)',borderRadius:'4px',padding:'3px 6px',fontSize:'0.65rem',color:'#ccc'}},
          h('button', {onClick:()=>doScale(s=>Math.min(10,s*1.25)), style:zBtn}, '+'),
          h('button', {onClick:()=>doScale(s=>Math.max(0.05,s/1.25)), style:zBtn}, '\u2013'),
          h('input', {type:'text', value: scaleVal.toFixed(1).replace(/\.0$/,''),
            style:{width:'48px',background:'rgba(0,0,0,0.4)',color:'#ccc',border:'1px solid #666',borderRadius:'3px',padding:'1px 4px',fontSize:'0.65rem',textAlign:'right'},
            onChange: e => { const v = parseFloat(e.target.value); if (!isNaN(v) && v > 0) {
              if (selPPz) updatePlotterPattern(selPPz.id, {scale: Math.min(10, Math.max(0.05, v/100))});
              else setCvScale(Math.min(1000, Math.max(1, v/100)));
            }},
            onKeyDown: e => { if (e.key === 'Enter') e.target.blur(); },
          }),
          h('span', {style:{fontSize:'0.6rem',color:'#999'}}, '%'),
          hasTransform && !selPPz ? h('button', {onClick:cvReset, style:zBtn}, 'Reset') : null,
        );
        // In plotter tab with a selected pattern, rotate/scale controls target the selected pattern
        const selPP = plotterActive && selectedPlaced ? plotterPatterns.find(p => p.id === selectedPlaced) : null;
        const rotVal = selPP ? selPP.rotation : cvRot;
        const doRot = (fn) => {
          if (selPP) updatePlotterPattern(selPP.id, {rotation: fn(selPP.rotation)});
          else setCvRot(fn);
        };
        const rotBar = h('div', {style:{position:'absolute',top:'32px',left:'8px',zIndex:5,display:'flex',gap:'4px',alignItems:'center',
            background:'rgba(0,0,0,0.6)',borderRadius:'4px',padding:'3px 6px',fontSize:'0.65rem',color:'#ccc'}},
          h('button', {onClick:()=>doRot(r=>r-15), style:zBtn}, '\u21b6'),
          h('button', {onClick:()=>doRot(r=>r+15), style:zBtn}, '\u21b7'),
          h('input', {type:'text', value: rotVal.toFixed(1).replace(/\.0$/,''),
            style:{width:'48px',background:'rgba(0,0,0,0.4)',color:'#ccc',border:'1px solid #666',borderRadius:'3px',padding:'1px 4px',fontSize:'0.65rem',textAlign:'right'},
            onChange: e => { const v = parseFloat(e.target.value); if (!isNaN(v)) doRot(() => v % 360); },
            onKeyDown: e => { if (e.key === 'Enter') e.target.blur(); },
          }),
          h('span', {style:{fontSize:'0.6rem',color:'#999'}}, '\u00b0'),
          selPP ? h('span', {style:{fontSize:'0.55rem',color:'var(--accent)',marginLeft:'2px'}}, selPP.name) : null,
        );
        const hint = h('div', {style:{position:'absolute',bottom:'8px',left:'8px',zIndex:5,fontSize:'0.58rem',color:'rgba(255,255,255,0.35)',pointerEvents:'none'}},
          'Drag to move \u2022 Shift+drag to rotate');
        return h('div', {ref:cvRef, onMouseDown:cvMouseDown,
          style:{position:'relative',width:'100%',height:'100%',display:'flex',alignItems:'center',justifyContent:'center',cursor:'grab',userSelect:'none'}},
          infoBar, rotBar, hint,
          h('canvas', {ref:canvasRef, style:{borderRadius:'8px', boxShadow:'0 4px 24px rgba(0,0,0,0.4)'}}),
        );
      })(),
      ),
      document.getElementById('canvas-area'),
    ),
  ];
}

ReactDOM.createRoot(document.createElement('div')).render(h(App));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import argparse, uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8890)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port)
