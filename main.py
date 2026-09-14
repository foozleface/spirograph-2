#!/usr/bin/env python3
"""
Modular Spirograph System
=========================
A pipeline-based system for generating complex spirograph patterns.

Each module transforms complex coordinates z = x + iy based on time parameter t ∈ [0, 1].
Modules can be generators (ignore input z) or transformers (modify input z).

``transform(z, t)`` is called with NumPy arrays — every sample of the draw at
once — and must be written with array-safe operations (``np.sin`` rather than
``math.sin``, ``np.where`` rather than ``if`` on a value that varies with t).
Parameters that do not vary with t may still be tested with plain ``if``. A
module written that way also works on a scalar, which is what the scrubber in
the window uses to ask "where is the pen at this moment?".

Output is SVG with optional arc-length reparameterization for uniform point density.
"""

import configparser
import importlib
import numpy as np
from abc import ABC, abstractmethod
from fractions import Fraction
from math import gcd, sin, cos, pi
from pathlib import Path
from typing import List, Tuple, Optional
import sys


# ---------------------------------------------------------------------------
# Easing utilities
# ---------------------------------------------------------------------------

def apply_easing(t: float, mode: str = 'linear') -> float:
    """
    Apply an easing function to a normalized time value.

    Args:
        t: Progress 0.0 to 1.0
        mode: 'linear', 'ease_in', 'ease_out', 'ease_in_out', 'sine'

    Returns:
        Eased time value
    """
    if mode == 'ease_in':
        return t * t
    elif mode == 'ease_out':
        return 1 - (1 - t) * (1 - t)
    elif mode == 'ease_in_out':
        return t * t * (3 - 2 * t)
    elif mode == 'sine':
        return 0.5 - 0.5 * np.cos(np.pi * t)
    return t


EASING_MODES = ('linear', 'ease_in', 'ease_out', 'ease_in_out', 'sine')


class TransformModule(ABC):
    """
    Base class for all spirograph transformation modules.
    
    Each module:
    - Loads its configuration from an INI section
    - Implements transform(z, t) -> z'
    - Reports its natural period for closure calculation
    """
    
    def __init__(self, config: configparser.ConfigParser, section: str):
        """
        Initialize module from config file.
        
        Args:
            config: Parsed INI configuration
            section: Section name for this module's parameters
        """
        self.config = config
        self.section = section
        self._pipeline_period = Fraction(1, 1)
        self._load_config()
        # Load easing after subclass config (available to all modules)
        self._easing = self._get('easing', 'linear')
        # What a transform acts on: 'all' (everything drawn so far) or an
        # integer k, the last k arms. See run_pipeline.
        self.scope = parse_scope(self._get('scope', 'all'))
    
    def set_pipeline_period(self, period: Fraction):
        """Set the combined pipeline period (called by main after computing period)."""
        self._pipeline_period = period
    
    def _get(self, key: str, fallback=None):
        """Get string value from config."""
        return self.config.get(self.section, key, fallback=fallback)
    
    def _getfloat(self, key: str, fallback: float = 0.0) -> float:
        """Get float value from config."""
        return self.config.getfloat(self.section, key, fallback=fallback)
    
    def _getint(self, key: str, fallback: int = 0) -> int:
        """Get integer value from config."""
        return self.config.getint(self.section, key, fallback=fallback)
    
    def _getboolean(self, key: str, fallback: bool = False) -> bool:
        """Get boolean value from config."""
        return self.config.getboolean(self.section, key, fallback=fallback)

    def _normalize_t(self, t: float) -> float:
        """
        Normalize t to [0,1] using pipeline period and apply easing.

        Modules with a 'normalize' config option respect it; others always normalize.
        Easing is applied via the 'easing' config option (default: linear).
        """
        normalize = getattr(self, 'normalize', True)
        if normalize:
            period = float(self._pipeline_period)
            t_use = t / period if period > 0 else t
        else:
            t_use = t
        return apply_easing(t_use, self._easing)

    def _interpolate(self, start: float, end: float, t_norm: float, param_name: str = '') -> float:
        """Interpolate a parameter value, supporting linear drift or oscillation.

        If an oscillation config exists for this param (osc_<param_name> in INI),
        oscillate between start and end instead of linear drift.

        Oscillation uses multi-sine for organic motion:
          base = sin(t * 2π * speed)
          perturb = sin(t * 2π * speed * φ)  (φ = golden ratio)
          value = mid + clamp(mix, -1, 1) * amplitude
        """
        if not param_name:
            return start + (end - start) * t_norm

        osc_key = f'osc_{param_name}'
        osc_val = self._get(osc_key, '')
        if not osc_val:
            return start + (end - start) * t_norm

        # Parse "speed,irregularity" e.g. "3,0.3"
        parts = [float(x.strip()) for x in osc_val.split(',')]
        speed = parts[0] if len(parts) > 0 else 3.0
        irreg = parts[1] if len(parts) > 1 else 0.3

        # Map to [0, 1] range: starts at 0 (=start), peaks at 1 (=end), returns to 0
        # Uses raised cosine: 0.5 - 0.5*cos(2π*speed*t) so t=0 → 0, mid-cycle → 1, end → 0
        phi = 1.618033988749895  # golden ratio
        sqrt2 = 1.4142135623730951
        tau = 2 * pi * speed * t_norm
        base = 0.5 - 0.5 * np.cos(tau)
        p1 = 0.5 - 0.5 * np.cos(tau * phi)
        p2 = 0.5 - 0.5 * np.cos(tau * sqrt2)
        # Mix: base always present, perturbations add organic variation
        mix = base * (1.0 - irreg * 0.4) + p1 * irreg * 0.25 + p2 * irreg * 0.15
        # Normalize to [0, 1]
        max_amp = 1.0  # raised cosines are already in [0,1], mix stays bounded
        if irreg > 0:
            max_amp = (1.0 - irreg * 0.4) + irreg * 0.25 + irreg * 0.15
        mix = np.clip(mix / max_amp, 0.0, 1.0)
        return start + (end - start) * mix

    @abstractmethod
    def _load_config(self):
        """Load module-specific configuration. Override in subclasses."""
        pass
    
    @abstractmethod
    def transform(self, z, t):
        """
        Transform every sample point of the draw at once.

        Args:
            z: Input positions, a complex array (or one complex number)
            t: Time parameter per point, a float array (or one float),
               in [0, period)

        Returns:
            Transformed positions, the same shape as z
        """
        pass
    
    @property
    @abstractmethod
    def natural_period(self) -> Fraction:
        """
        The natural period of this module's contribution.
        
        Returns a Fraction representing how many t-cycles until this
        module's pattern closes. Used for LCM calculation.
        
        Returns:
            Fraction representing the period (e.g., Fraction(1, 3) means
            the pattern repeats 3 times per t-cycle)
        """
        pass
    
    @property
    def is_generator(self) -> bool:
        """
        Whether this module generates coordinates (vs transforming them).
        
        Generators ignore the input z and produce coordinates purely from t.
        Transformers modify the input z based on t.
        
        Returns:
            True if this is a generator module
        """
        return False


def parse_scope(text):
    """'all' or a non-negative integer, from an INI value."""
    text = str(text).strip().lower()
    if text in ('', 'all'):
        return 'all'
    if text == 'last':
        return 1
    value = int(text)
    if value < 0:
        raise ValueError("scope must be 'all' or a count of arms, not %r" % text)
    return value


def lcm(a: int, b: int) -> int:
    """Compute least common multiple."""
    return abs(a * b) // gcd(a, b)


def compute_pipeline_period(modules: List[TransformModule]) -> Fraction:
    """
    Compute the overall period of a module pipeline.
    
    Args:
        modules: List of transformation modules
        
    Returns:
        Fraction representing when the combined pattern closes
    """
    if not modules:
        return Fraction(1, 1)
    
    # Start with the first module's period
    result = modules[0].natural_period
    
    # Compute LCM of all periods
    for module in modules[1:]:
        period = module.natural_period
        # LCM of fractions: lcm(a/b, c/d) = lcm(a,c) / gcd(b,d)
        num = lcm(result.numerator, period.numerator)
        den = gcd(result.denominator, period.denominator)
        result = Fraction(num, den)
    
    return result


def run_pipeline(modules: List[TransformModule], t, start=0j, stages=None):
    """
    Fold the pipeline over every sample at once.

    A generator (or a path — arc, translation, the things that slide) is an
    *arm*: it adds a vector to where the pen is. Before each arm is added the
    pen's position is remembered, so a transform can act on "the last k
    arms" rather than on everything drawn so far:

        scope = all   z' = T(z)                      everything so far
        scope = k     z' = base_k + T(z - base_k)    the last k arms only,
                                                     where base_k is where
                                                     the pen was before them
        scope = 0     z' = z + T(0)                  nothing — what a lone
                                                     rotation contributes to
                                                     a group branch

    A transform of everything also carries the remembered positions with it,
    so "the last two arms" still means the last two arms afterwards.

    This is exactly what a `group` of branches computed, written flat: a
    branch's transform acts on the arms of its own branch, which are the last
    k arms at that point. Old files with groups still run through group.py.

    Args:
        modules: List of transformation modules
        t: Time parameter — a float array covering the whole draw, or one float
        start: Initial position (a complex number, or an array like t)
        stages: If a list is given, the positions after each module are
                appended to it — the drawing as it stands after step k, which
                is what the window's stage thumbnails and the linkage
                scrubber are built from

    Returns:
        Final positions, the same shape as t
    """
    t = np.asarray(t, dtype=float)
    z = np.broadcast_to(np.asarray(start, dtype=complex), t.shape).copy() \
        if t.ndim else complex(start)
    bases = []                     # where the pen was before each arm
    for module in modules:
        scope = getattr(module, 'scope', 'all')
        if getattr(module, 'is_clock', False):
            # A clock changes the time every later module sees; the pen
            # stays where it is.
            t = module.retime(t)
        elif module.is_generator:
            bases.append(z)
            z = module.transform(z, t)
        elif scope == 'all':
            z = module.transform(z, t)
            bases = [module.transform(b, t) for b in bases]
        else:
            k = min(int(scope), len(bases))
            base = bases[-k] if k > 0 else z
            z = base + module.transform(z - base, t)
            if k > 1:
                bases[-k + 1:] = [base + module.transform(b - base, t)
                                  for b in bases[-k + 1:]]
        if stages is not None:
            stages.append(np.array(z, dtype=complex, copy=True))
    return z


def dense_sample(modules: List[TransformModule], num_samples: int,
                 period: Fraction = Fraction(1, 1), start: complex = 0j,
                 scroll_repeats: float = 1.0, stages=None) -> np.ndarray:
    """
    Generate dense samples from the pipeline, in one vectorised pass.

    Args:
        modules: List of transformation modules
        num_samples: Number of samples to generate
        period: Overall period of the pattern (samples t from 0 to period)
        start: Initial starting point
        scroll_repeats: Number of full periods to draw (>1 for scroll mode)
        stages: see run_pipeline

    Returns:
        Complex array of sampled points
    """
    t_max = float(period) * scroll_repeats
    t_values = np.linspace(0, t_max, num_samples, endpoint=False)
    return np.asarray(run_pipeline(modules, t_values, start, stages), dtype=complex)


def compute_arc_lengths(points: np.ndarray) -> np.ndarray:
    """
    Compute cumulative arc length at each point.
    
    Args:
        points: Complex array of points
        
    Returns:
        Array of cumulative arc lengths
    """
    # Compute segment lengths
    segments = np.abs(np.diff(points))
    
    # Cumulative sum with 0 at start
    arc_lengths = np.zeros(len(points))
    arc_lengths[1:] = np.cumsum(segments)
    
    return arc_lengths


def resample_by_arc_length(points: np.ndarray, num_output: int,
                           companions=()) -> np.ndarray:
    """
    Resample points at uniform arc length intervals.

    Args:
        points: Complex array of densely sampled points
        num_output: Number of output points desired
        companions: Other arrays sampled at the same t as ``points`` (the
            stages, the t values themselves) to resample at the same places,
            so companion[i] still describes output point i

    Returns:
        Complex array of uniformly-spaced (by arc length) points — and, when
        companions were given, a list of them resampled alongside
    """
    arc_lengths = compute_arc_lengths(points)
    total_length = arc_lengths[-1]
    
    # Target arc lengths for output points
    target_lengths = np.linspace(0, total_length, num_output, endpoint=False)
    
    # Interpolate to find points at target arc lengths
    # We interpolate real and imaginary parts separately
    output_real = np.interp(target_lengths, arc_lengths, points.real)
    output_imag = np.interp(target_lengths, arc_lengths, points.imag)
    out = output_real + 1j * output_imag
    if not companions:
        return out
    resampled = []
    for arr in companions:
        arr = np.asarray(arr)
        if np.iscomplexobj(arr):
            resampled.append(np.interp(target_lengths, arc_lengths, arr.real)
                             + 1j * np.interp(target_lengths, arc_lengths, arr.imag))
        else:
            resampled.append(np.interp(target_lengths, arc_lengths, arr))
    return out, resampled


def normalize_for_svg(points: np.ndarray, width: float, height: float, 
                      margin: float = 0.1) -> np.ndarray:
    """
    Normalize points to fit within SVG canvas with margin.
    
    Args:
        points: Complex array of points
        width: SVG canvas width
        height: SVG canvas height
        margin: Margin as fraction of canvas size
        
    Returns:
        Normalized complex array
    """
    # Find bounding box
    min_x, max_x = points.real.min(), points.real.max()
    min_y, max_y = points.imag.min(), points.imag.max()
    
    # Compute scale to fit with margin
    data_width = max_x - min_x
    data_height = max_y - min_y
    
    if data_width == 0:
        data_width = 1
    if data_height == 0:
        data_height = 1
    
    available_width = width * (1 - 2 * margin)
    available_height = height * (1 - 2 * margin)
    
    scale = min(available_width / data_width, available_height / data_height)
    
    # Center the data
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # Transform: center, scale, then translate to canvas center
    normalized = (points - complex(center_x, center_y)) * scale
    normalized = normalized + complex(width / 2, height / 2)
    
    # Flip Y axis for SVG coordinate system
    normalized = normalized.real - 1j * normalized.imag + complex(0, height)
    
    return normalized


def normalize_all_for_svg(point_arrays: List[np.ndarray], width: float,
                          height: float, margin: float = 0.1) -> List[np.ndarray]:
    """
    Normalize multiple point arrays using a shared bounding box.

    All arrays are scaled and translated identically so their spatial
    relationships are preserved (needed for symmetry copies).

    Args:
        point_arrays: List of complex point arrays
        width, height: SVG canvas dimensions
        margin: Margin as fraction of canvas size

    Returns:
        List of normalized complex arrays
    """
    combined = np.concatenate(point_arrays)

    min_x, max_x = combined.real.min(), combined.real.max()
    min_y, max_y = combined.imag.min(), combined.imag.max()

    data_width = max_x - min_x if max_x != min_x else 1
    data_height = max_y - min_y if max_y != min_y else 1
    data_ar = data_width / data_height

    # Adapt canvas to data aspect ratio: keep the smaller dimension,
    # expand the other so the pattern fills without squishing
    canvas_ar = width / height
    if data_ar > canvas_ar:
        actual_w = height * data_ar
        actual_h = height
    else:
        actual_w = width
        actual_h = width / data_ar

    available_width = actual_w * (1 - 2 * margin)
    available_height = actual_h * (1 - 2 * margin)
    scale = min(available_width / data_width, available_height / data_height)

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    result = []
    for pts in point_arrays:
        normalized = (pts - complex(center_x, center_y)) * scale
        normalized = normalized + complex(actual_w / 2, actual_h / 2)
        normalized = normalized.real - 1j * normalized.imag + complex(0, actual_h)
        result.append(normalized)

    return result, actual_w, actual_h


def _build_path_data(points: np.ndarray) -> str:
    """Build SVG path data string from complex point array."""
    parts = []
    for i, p in enumerate(points):
        x, y = p.real, p.imag
        if i == 0:
            parts.append(f"M {x:.4f} {y:.4f}")
        else:
            parts.append(f"L {x:.4f} {y:.4f}")
    return " ".join(parts)


def split_path_for_plotter(points: np.ndarray,
                           dash_on: float, dash_off: float) -> List[np.ndarray]:
    """
    Split a point array into sub-paths based on arc-length dash pattern.

    For physical pen plotters: creates actual path breaks (pen lifts) instead
    of visual-only SVG stroke-dasharray which plotters ignore.

    Args:
        points: Complex array of points
        dash_on: Arc length to draw before lifting
        dash_off: Arc length to skip (pen up)

    Returns:
        List of point sub-arrays, each a continuous drawn segment
    """
    arc_lengths = compute_arc_lengths(points)
    total_length = arc_lengths[-1]
    cycle = dash_on + dash_off

    segments = []
    current_segment = []

    for i, (pt, arc_len) in enumerate(zip(points, arc_lengths)):
        # Position within the dash cycle
        pos_in_cycle = arc_len % cycle
        is_drawing = pos_in_cycle < dash_on

        if is_drawing:
            current_segment.append(pt)
        else:
            if current_segment:
                segments.append(np.array(current_segment))
                current_segment = []

    # Don't forget the last segment
    if current_segment:
        segments.append(np.array(current_segment))

    return segments


def generate_svg(points: np.ndarray, width: float, height: float,
                 stroke_width: float, stroke_color: str,
                 background_color: str,
                 close_path: bool = False,
                 extra_paths: List[np.ndarray] = None,
                 config_text: str = None) -> str:
    """
    Generate SVG string from points.

    Args:
        points: Complex array of normalized points
        width, height: SVG dimensions
        stroke_width: Stroke width
        stroke_color: Stroke color hex
        background_color: Background color hex
        close_path: If True, close the path with SVG Z command
        extra_paths: Additional point arrays (e.g. from symmetry)
        config_text: INI config text to embed as XML comment

    Returns:
        SVG document as string
    """
    path_elements = []

    # Primary path
    path_data = _build_path_data(points)
    if close_path:
        path_data += " Z"
    path_elements.append(
        f'  <path d="{path_data}"\n'
        f'        fill="none"\n'
        f'        stroke="{stroke_color}"\n'
        f'        stroke-width="{stroke_width}"\n'
        f'        stroke-linecap="round"\n'
        f'        stroke-linejoin="round"/>'
    )

    # Extra paths (from symmetry, multi-layer, etc.)
    if extra_paths:
        for extra_pts in extra_paths:
            path_data = _build_path_data(extra_pts)
            if close_path:
                path_data += " Z"
            path_elements.append(
                f'  <path d="{path_data}"\n'
                f'        fill="none"\n'
                f'        stroke="{stroke_color}"\n'
                f'        stroke-width="{stroke_width}"\n'
                f'        stroke-linecap="round"\n'
                f'        stroke-linejoin="round"/>'
            )

    paths_str = '\n'.join(path_elements)

    config_comment = ''
    if config_text:
        # Sanitize for XML comment (no -- allowed inside comments)
        safe_config = config_text.replace('--', '- -')
        config_comment = f'\n<!-- Configuration:\n{safe_config}\n-->\n'

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
{config_comment}<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{background_color}"/>
{paths_str}
</svg>'''

    return svg


def load_module(module_spec: str, config: configparser.ConfigParser) -> TransformModule:
    """
    Dynamically load a transformation module.
    
    Supports two formats:
    
    1. Named sections with 'type' parameter (recommended):
        [my_rotation]
        type = rotation
        total_degrees = 45
        
        Pipeline: modules = my_rotation
        
    2. Legacy format (module name = section name):
        [rotation]
        total_degrees = 45
        
        Pipeline: modules = rotation
        
    3. Legacy suffix format:
        [rotation.slow]
        total_degrees = 45
        
        Pipeline: modules = rotation.slow
    
    Args:
        module_spec: Section name from pipeline (e.g., 'my_gear' or 'rotation')
        config: Configuration parser
        
    Returns:
        Instantiated TransformModule
    """
    config_section = module_spec
    
    # Check if the section exists
    if not config.has_section(config_section):
        # Try legacy suffix format: 'rotation.1' -> section 'rotation'
        if '.' in module_spec:
            base_name = module_spec.rsplit('.', 1)[0]
            if config.has_section(base_name):
                config_section = base_name
            else:
                print(f"Error: No config section found for '{module_spec}' or '{base_name}'")
                sys.exit(1)
        else:
            print(f"Error: No config section found for '{module_spec}'")
            sys.exit(1)
    
    # Check for 'type' parameter to determine which module to load
    if config.has_option(config_section, 'type'):
        module_type = config.get(config_section, 'type').strip()
    else:
        # Legacy mode: section name (or base name) is the module type
        if '.' in module_spec:
            module_type = module_spec.rsplit('.', 1)[0]
        else:
            module_type = module_spec
    
    try:
        # Import the module
        mod = importlib.import_module(module_type)
        
        # Get the module's main class (convention: ModuleNameModule)
        # e.g., spirograph_gear -> SpirographGearModule
        class_name = ''.join(word.capitalize() for word in module_type.split('_')) + 'Module'
        
        module_class = getattr(mod, class_name)
        
        return module_class(config, config_section)
        
    except ImportError as e:
        print(f"Error: Could not import module '{module_type}': {e}")
        sys.exit(1)
    except AttributeError as e:
        print(f"Error: Module '{module_type}' does not have class '{class_name}': {e}")
        sys.exit(1)


def run_single_pipeline(config: configparser.ConfigParser,
                        module_names: List[str],
                        initial_samples: int = 100000,
                        output_samples: int = 10000,
                        use_arc_length: bool = True,
                        start_point: complex = 0j,
                        label: str = "",
                        scroll_repeats: float = 1.0,
                        want_stages: bool = False):
    """
    Run a single pipeline and return resampled points.

    Args:
        config: Parsed INI configuration
        module_names: List of module section names
        initial_samples: Dense sample count
        output_samples: Output sample count
        use_arc_length: Whether to reparameterize by arc length
        start_point: Starting point for the pipeline
        label: Label for log messages
        scroll_repeats: Number of full periods to draw (>1 for scroll mode)
        want_stages: Also return, per output point, the t it was drawn at and
            the position after every module — see run_pipeline

    Returns:
        Resampled complex point array; with want_stages, the tuple
        ``(points, t_values, stages)`` where stages[k][i] is output point i
        as it stood after module k
    """
    prefix = f"[{label}] " if label else ""

    # Load modules
    modules = [load_module(name, config) for name in module_names]

    # Compute overall period
    period = compute_pipeline_period(modules)
    print(f"{prefix}Pipeline: {' -> '.join(module_names)}")
    print(f"{prefix}Period: {period} ({float(period):.4f} t-cycles)")
    if scroll_repeats != 1.0:
        print(f"{prefix}Scroll mode: {scroll_repeats}x repeats")

    # Inform modules of the combined period
    for module in modules:
        module.set_pipeline_period(period)

    # Generate dense samples
    print(f"{prefix}Generating {initial_samples:,} dense samples...")
    stages = [] if want_stages else None
    points = dense_sample(modules, initial_samples, period, start_point,
                          scroll_repeats=scroll_repeats, stages=stages)
    t_values = np.linspace(0, float(period) * scroll_repeats, initial_samples,
                           endpoint=False)

    # Arc length reparameterization
    if use_arc_length:
        print(f"{prefix}Reparameterizing to {output_samples:,} arc-length samples...")
        if want_stages:
            points, extra = resample_by_arc_length(points, output_samples,
                                                   companions=[t_values] + stages)
            t_values, stages = extra[0], extra[1:]
        else:
            points = resample_by_arc_length(points, output_samples)
    else:
        indices = np.linspace(0, len(points) - 1, output_samples, dtype=int)
        points = points[indices]
        if want_stages:
            t_values = t_values[indices]
            stages = [s[indices] for s in stages]

    arc_lengths = compute_arc_lengths(points)
    print(f"{prefix}Path length: {arc_lengths[-1]:.2f} units")

    if want_stages:
        return points, t_values, stages
    return points


def apply_finishing(path_arrays: List[np.ndarray],
                    config: configparser.ConfigParser) -> List[np.ndarray]:
    """
    The passes that act on finished curves, in their one fixed order:

        pen lift   -> break the line into strokes
        symmetry   -> rotate and mirror copies about a centre
        tile       -> repeat the whole thing in a grid
        clip       -> cut everything to a circle or a rectangle

    Each is an INI section of the same name and each is optional. This is
    the only place the order is decided: the command line and the app both
    call it, so a file finishes the same way wherever it is rendered.
    """
    arrays = list(path_arrays)

    if config.has_section('pen_lift'):
        from pen_lift import apply_pen_lift
        lifted = []
        for pts in arrays:
            lifted.extend(apply_pen_lift(pts, config))
        arrays = lifted
        print(f"Pen lift ({config.get('pen_lift', 'mode', fallback='periodic')}): {len(arrays)} segments")

    n_fold = config.getint('symmetry', 'n_fold', fallback=1)
    mirror = config.getboolean('symmetry', 'mirror', fallback=False)
    if n_fold > 1 or mirror:
        from symmetry import apply_symmetry
        cx = config.getfloat('symmetry', 'center_x', fallback=0.0)
        cy = config.getfloat('symmetry', 'center_y', fallback=0.0)
        expanded = []
        for pts in arrays:
            expanded.extend(apply_symmetry(pts, n_fold, mirror, cx, cy))
        arrays = expanded
        print(f"Applied {n_fold}-fold symmetry{' with mirror' if mirror else ''}: {len(arrays)} paths")

    if config.has_section('tile'):
        from tile import apply_tile
        tiled = []
        for pts in arrays:
            tiled.extend(apply_tile(
                pts, rows=config.getint('tile', 'rows', fallback=1),
                cols=config.getint('tile', 'cols', fallback=1),
                dx=config.getfloat('tile', 'dx', fallback=0.0),
                dy=config.getfloat('tile', 'dy', fallback=0.0),
                stagger=config.getboolean('tile', 'stagger', fallback=False)))
        arrays = tiled
        print(f"Tiled: {len(arrays)} paths")

    if config.has_section('clip'):
        from clip import apply_clip
        clipped = []
        for pts in arrays:
            clipped.extend(apply_clip(
                pts, shape=config.get('clip', 'shape', fallback='circle'),
                radius=config.getfloat('clip', 'radius', fallback=100.0),
                width=config.getfloat('clip', 'width', fallback=200.0),
                height=config.getfloat('clip', 'height', fallback=200.0),
                center_x=config.getfloat('clip', 'center_x', fallback=0.0),
                center_y=config.getfloat('clip', 'center_y', fallback=0.0),
                invert=config.getboolean('clip', 'invert', fallback=False)))
        arrays = clipped
        print(f"Clipped: {len(arrays)} strokes")
        if not arrays:
            raise ValueError("clip: nothing of the drawing is inside the shape")

    return arrays


def expand_moire_config(config: configparser.ConfigParser):
    """
    Expand [moire] section into auto-generated [layer.*] sections.

    Creates N near-copies of a pipeline with one parameter varied across
    a range, producing overlapping interference patterns (moire effect).

    The [moire] section specifies:
        copies: Number of overlapping passes (default 5)
        modules: Pipeline modules to use for each layer
        vary_param: Which parameter to vary, as "section.key"
        vary_range: Spread of variation (+/- from base value, default 0.05)
    """
    if not config.has_section('moire'):
        return

    n_copies = config.getint('moire', 'copies', fallback=5)
    base_modules = config.get('moire', 'modules')
    vary_param = config.get('moire', 'vary_param')
    vary_range = config.getfloat('moire', 'vary_range', fallback=0.05)

    # Parse "section.key" format
    section, key = vary_param.rsplit('.', 1)
    base_value = config.getfloat(section, key)

    print(f"Moire: expanding {n_copies} copies, varying {vary_param} "
          f"from {base_value - vary_range:.4f} to {base_value + vary_range:.4f}")

    # Parse the module list to find which modules need cloned sections
    module_names = [m.strip() for m in base_modules.split(',')]

    for i in range(n_copies):
        # Compute varied value: spread evenly from -vary_range to +vary_range
        if n_copies > 1:
            offset = vary_range * (2 * i / (n_copies - 1) - 1)
        else:
            offset = 0.0
        varied_value = base_value + offset

        layer_name = f"layer.moire_{i}"
        config.add_section(layer_name)

        # Build module list for this layer — clone the varied section
        if section in module_names:
            # The varied section is directly in the module list
            cloned_section = f"{section}_moire_{i}"
            # Clone all keys from the original section
            config.add_section(cloned_section)
            for k, v in config.items(section):
                config.set(cloned_section, k, v)
            # Override the varied parameter
            config.set(cloned_section, key, str(varied_value))

            # Replace section name in module list
            layer_modules = [cloned_section if m == section else m for m in module_names]
            config.set(layer_name, 'modules', ', '.join(layer_modules))
        else:
            # The varied section is a config section referenced by a module
            # Just set the modules as-is; we'll need a different approach
            config.set(layer_name, 'modules', base_modules)

    # Remove the moire section so it doesn't interfere
    config.remove_section('moire')


def main(config_path: str = "config.ini"):
    """
    Main entry point for the spirograph generator.

    Supports two modes:
    - Single pipeline: [pipeline] section with modules list
    - Multi-layer: [layer.NAME] sections, each with its own modules list

    Args:
        config_path: Path to INI configuration file
    """
    # Load configuration
    config = configparser.ConfigParser()
    config.read(config_path)

    # Expand moire auto-composition (generates layer sections)
    expand_moire_config(config)

    # Get output parameters
    width = config.getfloat('output', 'width', fallback=800)
    height = config.getfloat('output', 'height', fallback=800)
    margin = config.getfloat('output', 'margin', fallback=0.1)
    stroke_width = config.getfloat('output', 'stroke_width', fallback=0.5)
    stroke_color = config.get('output', 'stroke_color', fallback='#000000')
    background_color = config.get('output', 'background_color', fallback='#ffffff')
    output_filename = config.get('output', 'filename', fallback='output.svg')
    start_x = config.getfloat('output', 'start_x', fallback=0.0)
    start_y = config.getfloat('output', 'start_y', fallback=0.0)
    start_point = start_x + 1j * start_y
    close_path = config.getboolean('output', 'close_path', fallback=False)
    plotter_dash_on = config.getfloat('output', 'plotter_dash_on', fallback=0.0)
    plotter_dash_off = config.getfloat('output', 'plotter_dash_off', fallback=0.0)

    # Default sampling parameters
    initial_samples = config.getint('sampling', 'initial_samples', fallback=100000)
    output_samples = config.getint('sampling', 'output_samples', fallback=10000)
    use_arc_length = config.getboolean('sampling', 'use_arc_length', fallback=True)
    scroll_repeats = config.getfloat('sampling', 'scroll_repeats', fallback=1.0)

    # Symmetry options
    n_fold = config.getint('symmetry', 'n_fold', fallback=1) if config.has_section('symmetry') else 1
    mirror = config.getboolean('symmetry', 'mirror', fallback=False) if config.has_section('symmetry') else False
    sym_center_x = config.getfloat('symmetry', 'center_x', fallback=0.0) if config.has_section('symmetry') else 0.0
    sym_center_y = config.getfloat('symmetry', 'center_y', fallback=0.0) if config.has_section('symmetry') else 0.0

    # Detect multi-layer mode
    layer_sections = [s for s in config.sections() if s.startswith('layer.')]

    if layer_sections:
        # Multi-layer mode
        print(f"Multi-layer mode: {len(layer_sections)} layers")
        all_path_arrays = []

        for section in layer_sections:
            layer_name = section.split('.', 1)[1]
            module_names = [m.strip() for m in config.get(section, 'modules').split(',')]

            # Per-layer sampling overrides
            layer_initial = config.getint(section, 'initial_samples', fallback=initial_samples)
            layer_output = config.getint(section, 'output_samples', fallback=output_samples)
            layer_arc = config.getboolean(section, 'use_arc_length', fallback=use_arc_length)
            layer_scroll = config.getfloat(section, 'scroll_repeats', fallback=scroll_repeats)

            points = run_single_pipeline(config, module_names,
                                         layer_initial, layer_output,
                                         layer_arc, start_point,
                                         label=layer_name,
                                         scroll_repeats=layer_scroll)
            all_path_arrays.append(points)

    else:
        # Single pipeline mode
        module_names = [m.strip() for m in config.get('pipeline', 'modules').split(',')]
        points = run_single_pipeline(config, module_names,
                                     initial_samples, output_samples,
                                     use_arc_length, start_point,
                                     scroll_repeats=scroll_repeats)
        all_path_arrays = [points]

    # Pen lift, symmetry, tile, clip — the one finishing chain
    all_path_arrays = apply_finishing(all_path_arrays, config)

    # Apply plotter dash splitting (before normalization, uses raw arc lengths)
    if plotter_dash_on > 0 and plotter_dash_off > 0:
        split_arrays = []
        for pts in all_path_arrays:
            split_arrays.extend(split_path_for_plotter(pts, plotter_dash_on, plotter_dash_off))
        all_path_arrays = split_arrays
        print(f"Plotter dash: {len(all_path_arrays)} segments (on={plotter_dash_on}, off={plotter_dash_off})")

    # Normalize for SVG (shared bounding box across all paths)
    print("Normalizing for SVG output...")
    normalized_arrays, actual_w, actual_h = normalize_all_for_svg(all_path_arrays, width, height, margin)

    # Generate SVG
    print(f"Generating SVG...")
    config_text = Path(config_path).read_text()
    svg = generate_svg(normalized_arrays[0], actual_w, actual_h, stroke_width,
                       stroke_color, background_color,
                       close_path=close_path,
                       extra_paths=normalized_arrays[1:] if len(normalized_arrays) > 1 else None,
                       config_text=config_text)

    # Write output
    output_path = Path(output_filename)
    output_path.write_text(svg)
    print(f"Written to: {output_path.absolute()}")

    # Stats
    total_points = sum(len(a) for a in normalized_arrays)
    print(f"\nStatistics:")
    print(f"  Output points: {total_points:,}")
    print(f"  Total paths: {len(normalized_arrays)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Modular Spirograph Generator')
    parser.add_argument('config', help='Configuration INI file')
    parser.add_argument('--svg', metavar='FILE', 
                        help='Output SVG file (overrides config filename)')
    parser.add_argument('--png', metavar='FILE',
                        help='Output PNG file (requires cairosvg)')
    parser.add_argument('--png-width', type=int, default=800,
                        help='PNG output width in pixels (default: 800)')
    parser.add_argument('--png-height', type=int, default=None,
                        help='PNG output height in pixels (default: same as width)')
    parser.add_argument('--no-preview', action='store_true', 
                        help='Disable preview window (default: show preview on Mac)')
    parser.add_argument('--preview', action='store_true',
                        help='Force preview window')
    parser.add_argument('--viewer', default='Safari',
                        help='App to open SVG (default: Safari). Use "default" for system default.')
    
    args = parser.parse_args()
    
    # If --svg specified, temporarily modify config before running
    config = configparser.ConfigParser()
    config.read(args.config)
    
    # Override output filename if --svg specified
    if args.svg:
        if not config.has_section('output'):
            config.add_section('output')
        config.set('output', 'filename', args.svg)
        # Write to temp file and use that
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as tmp:
            config.write(tmp)
            tmp_path = tmp.name
        main(tmp_path)
        import os
        os.unlink(tmp_path)
        svg_filename = args.svg
    else:
        main(args.config)
        svg_filename = config.get('output', 'filename', fallback='output.svg')
    
    # Generate PNG if requested
    if args.png:
        try:
            import cairosvg
            png_height = args.png_height if args.png_height else args.png_width
            cairosvg.svg2png(
                url=svg_filename, 
                write_to=args.png,
                output_width=args.png_width,
                output_height=png_height
            )
            print(f"PNG written to: {args.png}")
        except ImportError:
            print("Error: cairosvg not installed. Run: pip install cairosvg")
            sys.exit(1)
        except Exception as e:
            print(f"Error generating PNG: {e}")
            sys.exit(1)
    
    # Preview on Mac if not disabled
    import platform
    show_preview = args.preview or (platform.system() == 'Darwin' and not args.no_preview)
    
    if show_preview:
        try:
            import subprocess
            if args.viewer.lower() == 'default':
                subprocess.run(['open', svg_filename], check=False)
            else:
                subprocess.run(['open', '-a', args.viewer, svg_filename], check=False)
        except Exception as e:
            print(f"Could not open preview: {e}")
