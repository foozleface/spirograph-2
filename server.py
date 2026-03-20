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
            "cycles":     {"type": "float", "default": 1.0,  "min": 1,  "max": 50, "step": 1, "desc": "Repetitions"},
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
    "surface": {
        "category": "generator",
        "label": "Surface",
        "desc": "3D parametric surfaces (torus, Mobius, sphere, Klein bottle, etc.)",
        "params": {
            "surface":      {"type": "str", "default": "torus", "desc": "Type: torus, mobius, ribbon, sphere, klein, helix_ribbon, figure8"},
            "major_radius": {"type": "float", "default": 100.0, "min": 10, "max": 300, "desc": "Major radius"},
            "minor_radius": {"type": "float", "default": 40.0,  "min": 5,  "max": 150, "desc": "Minor radius"},
            "width":        {"type": "float", "default": 60.0,  "min": 5,  "max": 200, "desc": "Width (ribbon/mobius)"},
            "twists":       {"type": "float", "default": 0.0,   "min": 0,  "max": 8, "step": 0.5, "desc": "Half-twists"},
            "v_lines":      {"type": "int",   "default": 40,    "min": 5,  "max": 200, "desc": "Line density"},
            "view_angle_x": {"type": "float", "default": 20.0,  "min": -90, "max": 90, "desc": "View tilt X"},
            "view_angle_y": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Y"},
            "view_angle_z": {"type": "float", "default": 0.0,   "min": -90, "max": 90, "desc": "View tilt Z"},
            "scale":        {"type": "float", "default": 1.0,   "min": 0.1, "max": 5, "step": 0.1, "desc": "Scale"},
            "cycles":       {"type": "float", "default": 1.0,   "min": 1,  "max": 10, "step": 1, "desc": "Cycles"},
        },
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
            "cycles":       {"type": "float", "default": 1.0,  "min": 1,  "max": 50, "step": 1, "desc": "Cycles"},
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
    moire: dict[str, Any] = {}


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
    moire: dict[str, Any] = {}


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
        symmetry=req.symmetry, moire=req.moire,
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


def _emit_mod(lines, section_name, mod_params):
    """Emit a single module's INI section."""
    lines.append(f"[{section_name}]")
    for k, v in mod_params.items():
        if isinstance(v, bool):
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


def _run_pipeline(ini_text: str) -> str:
    """Run the spirograph pipeline from INI text and return SVG."""
    import importlib
    # Re-import main fresh to avoid stale state
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

    normalized = normalize_all_for_svg(all_path_arrays, width, height, margin)

    svg = generate_svg(
        normalized[0], width, height, stroke_width, stroke_color, bg_color,
        close_path=close_path,
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
.param-row .drift-toggle { background:none; border:none; color:var(--muted); cursor:pointer; font-size:0.6rem;
                            padding:0 2px; transition:transform 0.15s, color 0.15s; flex-shrink:0; width:14px; text-align:center; }
.param-row .drift-toggle:hover { color:var(--accent); }
.param-row .drift-toggle.open { color:var(--accent); transform:rotate(90deg); }
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
#filebrowser-mount { display:flex; position:relative; flex-shrink:0; }
#toolbar { display:flex; gap:8px; padding:6px 16px; border-bottom:1px solid var(--border); align-items:center; }
#toolbar .spacer { flex:1; }
#toolbar .status { font-size:0.72rem; color:var(--muted); }

#canvas-area { flex:1; display:flex; align-items:center; justify-content:center; padding:20px; overflow:auto; position:relative; min-width:0; }
#canvas-area svg, #canvas-area img { max-width:100%; max-height:100%; border-radius:8px;
                                      box-shadow:0 4px 24px rgba(0,0,0,0.4); }
#canvas-area .placeholder { color:var(--muted); font-size:0.9rem; text-align:center; }
#canvas-area .spinner-overlay { position:absolute; inset:0; display:flex; flex-direction:column;
  align-items:center; justify-content:center; background:rgba(15,15,23,0.75); z-index:10; border-radius:8px; }
.spinner { width:48px; height:48px; border:3px solid var(--border); border-top-color:var(--accent);
           border-radius:50%; animation:spin 0.8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.spinner-label { margin-top:12px; font-size:0.8rem; color:var(--muted); }


/* File browser panel — collapsible right edge */
.fb-tab { position:absolute; right:0; top:50%; transform:translateY(-50%); z-index:20;
          writing-mode:vertical-rl; text-orientation:mixed;
          background:var(--card); border:1px solid var(--border); border-right:none;
          border-radius:6px 0 0 6px; padding:12px 6px; cursor:pointer;
          font-size:0.72rem; font-weight:600; color:var(--muted); letter-spacing:0.04em;
          display:flex; align-items:center; gap:6px; transition:all 0.15s; }
.fb-tab:hover { color:var(--text); background:var(--sidebar); }
.fb-tab .caret { font-size:0.6rem; transition:transform 0.2s; }
.fb-tab.open .caret { transform:rotate(180deg); }
.filebrowser { width:340px; min-width:340px; background:var(--sidebar);
               border-left:1px solid var(--border); display:flex; flex-direction:column;
               transition:width 0.2s, min-width 0.2s; overflow:hidden; }
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
</style>
</head>
<body>
<div id="sidebar"></div>
<div id="main">
  <div id="toolbar"></div>
  <div id="content-area">
    <div id="canvas-area"></div>
    <div id="filebrowser-mount"></div>
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
  const [steps, setSteps] = useState([]);
  const [sel, setSel] = useState(null); // {step, branch?, sub?}
  const [output, setOutput] = useState({ stroke_width: 0.3, stroke_color: '#000000', background_color: '#ffffff' });
  const [symmetry, setSymmetry] = useState({ n_fold: 1, mirror: false });
  const [sampling, setSampling] = useState({ scroll_repeats: 1.0, initial_samples: 80000, output_samples: 12000 });
  const [moire, setMoire] = useState({ enabled: false, module_idx: 0, param: '', copies: 5, range: 2.0 });
  const [svgHtml, setSvgHtml] = useState('');
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState('');
  const idCounter = useRef(0);
  const [showFileBrowser, setShowFileBrowser] = useState(false);
  const [iniFiles, setIniFiles] = useState([]);
  const [iniSearch, setIniSearch] = useState('');
  const [loadedFile, setLoadedFile] = useState('');
  const [saveName, setSaveName] = useState('');
  const [showSave, setShowSave] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [foldersOpen, setFoldersOpen] = useState({'/': true});
  const regenFlag = useRef(false);
  const [driftOpen, setDriftOpen] = useState({});

  const totalModules = steps.reduce((n, s) => s.kind === 'group' ? n + s.branches.reduce((m, b) => m + b.length, 0) : n + (s.mod ? 1 : 0), 0);

  useEffect(() => { fetch('/api/modules').then(r=>r.json()).then(setModules); }, []);
  useEffect(() => {
    if (regenFlag.current && totalModules > 0) { regenFlag.current = false; generate(); }
  }, [steps]);

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

  // Unified drag system: reorder steps OR drag new modules from palette
  const [dragSrc, setDragSrc] = useState(null);  // {type:'reorder',idx} or {type:'new',modType}
  const [dropTarget, setDropTarget] = useState(null);  // {stepIdx, mode:'before'|'on'|'after'}

  const onStepDragStart = (idx) => setDragSrc({ type: 'reorder', idx });
  const onPaletteDragStart = (modType) => setDragSrc({ type: 'new', modType });

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
          const srcMods = src.kind === 'single' ? [src.mod] : src.mods;
          const tgtMods = tgt.kind === 'single' ? [tgt.mod] : tgt.mods;
          next[stepIdx] = { kind: 'group', mods: [...tgtMods, ...srcMods] };
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
        moire: moire.enabled ? { module_idx: moire.module_idx, param: moire.param, copies: moire.copies, range: moire.range } : {},
      };
      const res = await fetch('/api/generate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Generation failed'); }
      const svg = await res.text();
      setSvgHtml(svg);

      setStatus(`Done in ${((Date.now()-t0)/1000).toFixed(1)}s`);
    } catch (e) {
      setStatus('Error: ' + e.message);
    } finally {
      setGenerating(false);
    }
  };


  const saveConfig = async () => {
    if (!saveName.trim()) return;
    try {
      const stepsData = steps
        .filter(s => s.kind === 'single' ? s.mod !== null : s.branches.some(b => b.some(m => m !== null)))
        .map(s => {
          if (s.kind === 'single') return { kind: 'single', params: s.mod.params };
          return { kind: 'group', branches: s.branches.map(b => b.filter(m => m !== null).map(m => m.params)).filter(b => b.length > 0) };
        });
      const res = await fetch('/api/save', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: saveName, steps: stepsData, output, sampling,
          symmetry: symmetry.n_fold > 1 || symmetry.mirror ? symmetry : {},
          moire: moire.enabled ? { module_idx: moire.module_idx, param: moire.param, copies: moire.copies, range: moire.range } : {},
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
    }
  };

  const randomize = () => {
    if (!modules) return;
    const generators = Object.entries(modules).filter(([_,v]) => v.category === 'generator');
    const transforms = Object.entries(modules).filter(([_,v]) => v.category === 'transform');
    const [gType, gDef] = generators[Math.floor(Math.random() * generators.length)];
    const newPipeline = [];
    const id1 = ++idCounter.current;
    const gParams = { type: gType };
    for (const [k, v] of Object.entries(gDef.params)) {
      if (v.type === 'bool') { gParams[k] = Math.random() > 0.5; continue; }
      const lo = v.min ?? 0; const hi = v.max ?? 100;
      let val = lo + Math.random() * (hi - lo);
      if (v.type === 'int') val = Math.round(val);
      else val = Math.round(val * 100) / 100;
      gParams[k] = val;
    }
    newPipeline.push({ id: id1, type: gType, params: gParams });

    // Maybe add a transform
    if (Math.random() > 0.3 && transforms.length > 0) {
      const [tType, tDef] = transforms[Math.floor(Math.random() * transforms.length)];
      const id2 = ++idCounter.current;
      const tParams = { type: tType };
      for (const [k, v] of Object.entries(tDef.params)) {
        if (v.type === 'bool') { tParams[k] = v.default; continue; }
        const lo = v.min ?? 0; const hi = v.max ?? 100;
        let val = lo + Math.random() * (hi - lo);
        if (v.type === 'int') val = Math.round(val);
        else val = Math.round(val * 100) / 100;
        tParams[k] = val;
      }
      newPipeline.push({ id: id2, type: tType, params: tParams });
    }
    setSteps(newPipeline.map(m => ({ kind: 'single', mod: m })));
    setSel({ step: 0 });
    setSymmetry({ n_fold: Math.random() > 0.6 ? Math.floor(Math.random()*6)+2 : 1, mirror: Math.random() > 0.7 });
    setSampling({ scroll_repeats: Math.random() > 0.5 ? Math.floor(Math.random()*8)+2 : 1 });
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
      setMoire({ enabled: false, module_idx: 0, param: '', copies: 5, range: 2.0 });

      setLoadedFile(filePath);
      setStatus(`Loaded ${filePath}`);
      regenFlag.current = true;
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
        h('p', null, 'Modular pattern generator'),
      ),

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
                      h('div', {key:`b-${bi}`, className:'tree-node'},
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
              // Base param row — with optional drift toggle
              rows.push(h('div', {key, className:'param-row'},
                hasDrift ? h('button', {className:'drift-toggle' + (driftOpen[key] ? ' open' : ''),
                  title:'Drift: animate this value over the draw',
                  onClick:()=>setDriftOpen(prev=>({...prev,[key]:!prev[key]}))}, '\u25b6') : null,
                h('label', null, spec.desc),
                h('input', {type:'range', min:spec.min, max:Math.max(spec.max, val), step, value:val,
                  onChange:e=>updateParam(sel.step, sel.branch, sel.sub, key, parse(e.target.value))}),
                h('input', {type:'number', step, value:val,
                  onChange:e=>{ const v = parse(e.target.value); if (!isNaN(v)) updateParam(sel.step, sel.branch, sel.sub, key, v); }}),
              ));
              // Drift row (if expanded)
              if (hasDrift && driftOpen[key]) {
                const dk = driftMap[key];
                const ds = params[dk];
                const dv = activeMod.params[dk];
                const dstep = ds.step || (ds.type==='int' ? 1 : 0.1);
                const dparse = v => ds.type==='int' ? parseInt(v) : parseFloat(v);
                rows.push(h('div', {key:dk, className:'drift-row'},
                  h('label', {title:'Click to reset (no drift)',
                    onClick:()=>{updateParam(sel.step, sel.branch, sel.sub, dk, activeMod.params[key]); setDriftOpen(prev=>({...prev,[key]:false}));}},
                    '\u2192 end \u00d7'),
                  h('input', {type:'range', min:ds.min, max:Math.max(ds.max, dv), step:dstep, value:dv,
                    onChange:e=>updateParam(sel.step, sel.branch, sel.sub, dk, dparse(e.target.value))}),
                  h('input', {type:'number', step:dstep, value:dv,
                    onChange:e=>{ const v = dparse(e.target.value); if (!isNaN(v)) updateParam(sel.step, sel.branch, sel.sub, dk, v); }}),
                ));
              }
            }
            return rows;
          })(),
        ),
      ) : null,

      // Moire — parameter drift
      (() => {
        // Build flat list of single-step modules for moire targeting
        const flatMods = steps.filter(s => s.kind === 'single' && s.mod).map(s => s.mod);
        const ss = {flex:1,background:'var(--bg)',border:'1px solid var(--border)',color:'var(--text)',borderRadius:'4px',padding:'3px 6px',fontSize:'0.78rem'};
        return h('div', {className:'section'},
          h('div', {style:{display:'flex',alignItems:'center',justifyContent:'space-between'}},
            h('div', {className:'section-title', style:{marginBottom:0}}, 'Moire \u2014 Parameter Drift'),
            h('input', {type:'checkbox', checked:moire.enabled, style:{accentColor:'var(--accent)'},
              onChange:e=>setMoire({...moire, enabled:e.target.checked})}),
          ),
          moire.enabled && flatMods.length > 0 ? h('div', {style:{marginTop:8}},
            h('div', {className:'output-row'},
              h('label', null, 'Module'),
              h('select', {value:moire.module_idx, style:ss,
                onChange:e=>{const idx=parseInt(e.target.value); setMoire({...moire, module_idx:idx, param:''});}},
                flatMods.map((m, i) => h('option', {key:i, value:i}, `${i+1}. ${modules[m.type]?.label || m.type}`)),
              ),
            ),
            h('div', {className:'output-row'},
              h('label', null, 'Parameter'),
              h('select', {value:moire.param, style:ss,
                onChange:e=>setMoire({...moire, param:e.target.value})},
                h('option', {value:''}, '-- select --'),
                (() => {
                  const mod = flatMods[moire.module_idx];
                  if (!mod || !modules[mod.type]) return null;
                  return Object.entries(modules[mod.type].params)
                    .filter(([_, spec]) => spec.type !== 'bool')
                    .map(([key, spec]) => h('option', {key, value:key}, `${spec.desc} (${key})`));
                })(),
              ),
            ),
            h('div', {className:'output-row'},
              h('label', null, 'Copies'),
              h('input', {type:'number', value:moire.copies, min:2, max:30, step:1,
                onChange:e=>setMoire({...moire, copies:parseInt(e.target.value)})}),
              h('label', null, 'Range \u00b1'),
              h('input', {type:'number', value:moire.range, min:0.001, max:100, step:0.1,
                onChange:e=>setMoire({...moire, range:parseFloat(e.target.value)})}),
            ),
            moire.param && flatMods[moire.module_idx] ? h('div', {style:{fontSize:'0.68rem',color:'var(--muted)',marginTop:4}},
              `${moire.copies} copies, varying ${moire.param} \u00b1${moire.range}`
            ) : null,
          ) : moire.enabled ? h('div', {style:{fontSize:'0.72rem',color:'var(--muted)',marginTop:6}}, 'Add steps to pipeline first') : null,
        );
      })(),

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
        h('button', {className:'btn btn-secondary', disabled:!svgHtml, onClick:() => {
          const blob = new Blob([svgHtml], {type:'image/svg+xml'});
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = (loadedFile || 'spirograph').replace('.ini','') + '.svg';
          a.click(); URL.revokeObjectURL(url);
        }}, 'Export SVG'),
        h('button', {className:'btn btn-secondary', onClick:randomize}, 'Random'),
      ),
      showSave ? h('div', {style:{padding:'4px 16px 8px',display:'flex',gap:'6px',alignItems:'center'}},
        h('input', {type:'text', value:saveName, placeholder:'filename',
          style:{flex:1,background:'var(--bg)',border:'1px solid var(--border)',color:'var(--text)',
                 borderRadius:'4px',padding:'5px 8px',fontSize:'0.78rem',outline:'none'},
          onChange:e=>setSaveName(e.target.value),
          onKeyDown:e=>{ if (e.key==='Enter') saveConfig(); if (e.key==='Escape') setShowSave(false); },
          autoFocus:true}),
        h('span', {style:{color:'var(--muted)',fontSize:'0.72rem'}}, '.ini'),
        h('button', {style:{background:'var(--accent)',color:'#fff',border:'none',borderRadius:'4px',
                            padding:'5px 10px',fontSize:'0.75rem',fontWeight:600,cursor:'pointer'},
          onClick:saveConfig}, 'Save'),
      ) : null,
      loadedFile ? h('div', {style:{padding:'0 16px 8px',fontSize:'0.7rem',color:'var(--muted)'}},
        'Loaded: ', loadedFile) : null,
    ), document.getElementById('sidebar')),

    // ---- File Browser (right edge panel) ----
    ReactDOM.createPortal(h(React.Fragment, null,
      h('div', {className:'fb-tab' + (showFileBrowser ? ' open' : ''),
        onClick:() => { const opening = !showFileBrowser; setShowFileBrowser(opening); if (opening) refreshIniFiles(); }},
        h('span', {className:'caret'}, showFileBrowser ? '\u25b6' : '\u25c0'),
        'Files',
      ),
      h('div', {className:'filebrowser' + (showFileBrowser ? '' : ' collapsed')},
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
          // Group by folder
          const folders = {};
          for (const f of filtered) {
            const key = f.dir || '/';
            if (!folders[key]) folders[key] = [];
            folders[key].push(f);
          }
          // Sort: root first, then alphabetical
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
      ),
    ), document.getElementById('filebrowser-mount')),

    // ---- Toolbar (portaled) ----
    ReactDOM.createPortal(h(React.Fragment, {key:'tb'},
      h('div', {className:'spacer'}),
      status ? h('div', {className:'status'}, status) : null,
    ), document.getElementById('toolbar')),

    // ---- Canvas area (portaled) ----
    ReactDOM.createPortal(h(React.Fragment, null,
      generating ? h('div', {className:'spinner-overlay'},
        h('div', {className:'spinner'}),
        h('div', {className:'spinner-label'}, 'Generating pattern...'),
      ) : null,
      svgHtml
        ? h('div', {dangerouslySetInnerHTML:{__html:svgHtml}, style:{display:'flex',alignItems:'center',justifyContent:'center',width:'100%',height:'100%'}})
        : null,
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
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8890)
