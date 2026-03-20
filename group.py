#!/usr/bin/env python3
"""
Group Module
============
Parallel composition: multiple branches run independently from z=0,
each branch is its own serial sub-pipeline, and the branch outputs
are summed. Like independent drawing arms on a spirograph machine.

Supports two formats:

1. Branched (new): branches separated by '|' in the modules list
    [arm]
    type = group
    modules = gear1, slow_spin | gear2, fast_spin

    Branch 1: gear1 -> slow_spin (serial chain from 0j)
    Branch 2: gear2 -> fast_spin (serial chain from 0j)
    Result: branch1_output + branch2_output

2. Flat (legacy): all modules as independent parallel siblings
    [arm]
    type = group
    modules = gear1, gear2

    Each runs from 0j independently, outputs summed.
"""

import configparser
from fractions import Fraction
from math import gcd
from main import TransformModule, load_module, compute_pipeline_period, run_pipeline


def lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


class GroupModule(TransformModule):
    """
    Parallel branches: each branch runs its own serial sub-pipeline
    from z=0, and branch outputs are summed.

    Configuration:
        modules: Module names, branches separated by '|'
                 e.g., "gear1, rotation | gear2, scale"
    """

    def _load_config(self):
        modules_str = self._get('modules', '')

        # Parse branches: split on '|', then each branch is comma-separated
        branch_strs = modules_str.split('|')
        self._branches = []
        all_modules = []
        for branch_str in branch_strs:
            names = [m.strip() for m in branch_str.split(',') if m.strip()]
            mods = [load_module(name, self.config) for name in names]
            self._branches.append(mods)
            all_modules.extend(mods)

        self._sub_period = compute_pipeline_period(all_modules) if all_modules else Fraction(1, 1)

    def set_pipeline_period(self, period: Fraction):
        """Propagate period to all sub-modules in all branches."""
        super().set_pipeline_period(period)
        for branch in self._branches:
            for mod in branch:
                mod.set_pipeline_period(period)

    def transform(self, z: complex, t: float) -> complex:
        """Run each branch as a serial pipeline from 0j, sum results."""
        result = 0j
        for branch in self._branches:
            result += run_pipeline(branch, t, start=0j)
        return z + result

    @property
    def natural_period(self) -> Fraction:
        return self._sub_period

    def __repr__(self):
        branch_info = [f"[{len(b)} mods]" for b in self._branches]
        return f"GroupModule(branches={' | '.join(branch_info)})"
