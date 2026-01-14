#!/usr/bin/env python3
"""
Modular Spirograph System
=========================
A pipeline-based system for generating complex spirograph patterns.

Each module transforms complex coordinates z = x + iy based on time parameter t ∈ [0, 1].
Modules can be generators (ignore input z) or transformers (modify input z).

Output is SVG with optional arc-length reparameterization for uniform point density.
"""

import configparser
import importlib
import numpy as np
from abc import ABC, abstractmethod
from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import List, Tuple, Optional
import sys


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
    
    @abstractmethod
    def _load_config(self):
        """Load module-specific configuration. Override in subclasses."""
        pass
    
    @abstractmethod
    def transform(self, z: complex, t: float) -> complex:
        """
        Transform a point based on time.
        
        Args:
            z: Input position as complex number (x + iy)
            t: Normalized time parameter in [0, 1]
            
        Returns:
            Transformed position as complex number
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


def run_pipeline(modules: List[TransformModule], t: float, start: complex = 0j) -> complex:
    """
    Run a single time step through the module pipeline.
    
    Args:
        modules: List of transformation modules
        t: Time parameter in [0, 1]
        start: Initial starting point
        
    Returns:
        Final transformed position as complex number
    """
    z = start
    for module in modules:
        z = module.transform(z, t)
    return z


def dense_sample(modules: List[TransformModule], num_samples: int, 
                 period: Fraction = Fraction(1, 1), start: complex = 0j) -> np.ndarray:
    """
    Generate dense samples from the pipeline.
    
    Args:
        modules: List of transformation modules
        num_samples: Number of samples to generate
        period: Overall period of the pattern (samples t from 0 to period)
        start: Initial starting point
        
    Returns:
        Complex array of sampled points
    """
    t_max = float(period)
    t_values = np.linspace(0, t_max, num_samples, endpoint=False)
    points = np.array([run_pipeline(modules, t, start) for t in t_values])
    return points


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


def resample_by_arc_length(points: np.ndarray, num_output: int) -> np.ndarray:
    """
    Resample points at uniform arc length intervals.
    
    Args:
        points: Complex array of densely sampled points
        num_output: Number of output points desired
        
    Returns:
        Complex array of uniformly-spaced (by arc length) points
    """
    arc_lengths = compute_arc_lengths(points)
    total_length = arc_lengths[-1]
    
    # Target arc lengths for output points
    target_lengths = np.linspace(0, total_length, num_output, endpoint=False)
    
    # Interpolate to find points at target arc lengths
    # We interpolate real and imaginary parts separately
    output_real = np.interp(target_lengths, arc_lengths, points.real)
    output_imag = np.interp(target_lengths, arc_lengths, points.imag)
    
    return output_real + 1j * output_imag


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


def generate_svg(points: np.ndarray, width: float, height: float,
                 stroke_width: float, stroke_color: str, 
                 background_color: str) -> str:
    """
    Generate SVG string from points.
    
    Args:
        points: Complex array of normalized points
        width: SVG width
        height: SVG height
        stroke_width: Stroke width for path
        stroke_color: Stroke color (hex)
        background_color: Background color (hex)
        
    Returns:
        SVG document as string
    """
    # Build path data
    path_parts = []
    for i, p in enumerate(points):
        x, y = p.real, p.imag
        if i == 0:
            path_parts.append(f"M {x:.4f} {y:.4f}")
        else:
            path_parts.append(f"L {x:.4f} {y:.4f}")
    
    # Don't close the path - leave it as an open line segment
    path_data = " ".join(path_parts)
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}" 
     viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{background_color}"/>
  <path d="{path_data}" 
        fill="none" 
        stroke="{stroke_color}" 
        stroke-width="{stroke_width}"
        stroke-linecap="round"
        stroke-linejoin="round"/>
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


def main(config_path: str = "config.ini"):
    """
    Main entry point for the spirograph generator.
    
    Args:
        config_path: Path to INI configuration file
    """
    # Load configuration
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Parse pipeline
    module_names = [m.strip() for m in config.get('pipeline', 'modules').split(',')]
    print(f"Pipeline: {' -> '.join(module_names)}")
    
    # Load modules
    modules = [load_module(name, config) for name in module_names]
    
    # Compute overall period
    period = compute_pipeline_period(modules)
    print(f"Combined period: {period} (pattern closes after {float(period):.4f} t-cycles)")
    
    # Inform modules of the combined period
    for module in modules:
        module.set_pipeline_period(period)
    
    # Get sampling parameters
    initial_samples = config.getint('sampling', 'initial_samples', fallback=100000)
    output_samples = config.getint('sampling', 'output_samples', fallback=10000)
    use_arc_length = config.getboolean('sampling', 'use_arc_length', fallback=True)
    
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
    
    # Generate dense samples
    print(f"Generating {initial_samples:,} dense samples over {float(period):.2f} t-cycles...")
    points = dense_sample(modules, initial_samples, period, start_point)
    
    # Arc length reparameterization
    if use_arc_length:
        print(f"Reparameterizing to {output_samples:,} arc-length samples...")
        points = resample_by_arc_length(points, output_samples)
    else:
        # Just subsample uniformly in t
        indices = np.linspace(0, len(points) - 1, output_samples, dtype=int)
        points = points[indices]
    
    # Compute arc length for info
    arc_lengths = compute_arc_lengths(points)
    total_length = arc_lengths[-1]
    print(f"Total path length: {total_length:.2f} units")
    
    # Normalize for SVG
    print("Normalizing for SVG output...")
    normalized = normalize_for_svg(points, width, height, margin)
    
    # Generate SVG
    print(f"Generating SVG...")
    svg = generate_svg(normalized, width, height, stroke_width, 
                       stroke_color, background_color)
    
    # Write output
    output_path = Path(output_filename)
    output_path.write_text(svg)
    print(f"Written to: {output_path.absolute()}")
    
    # Stats
    print(f"\nStatistics:")
    print(f"  Bounding box: {points.real.min():.2f} to {points.real.max():.2f} (x)")
    print(f"                {points.imag.min():.2f} to {points.imag.max():.2f} (y)")
    print(f"  Output points: {len(normalized):,}")


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
