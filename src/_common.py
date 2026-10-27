"""Shared plumbing for the numbered modules.

The guide's module names start with digits, which are not importable identifiers,
so every module loads its siblings through here rather than with `import`.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load(stem: str) -> ModuleType:
    """Load a numbered sibling module by file stem, e.g. load('00_design_freeze')."""
    key = f"_mmf_{stem}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, SRC / f"{stem}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def banner(module: str, inputs: list[str], outputs: list[str]) -> None:
    print(f"\n=== {module}")
    print(f"    in : {', '.join(inputs)}")
    print(f"    out: {', '.join(outputs)}")
