"""
Frozen-aware application root path.

PyInstaller onedir mode:
  sys.frozen = True
  sys.executable = <app_root>/SettlementFormGenerator.exe
  → app_root  = Path(sys.executable).parent
  → data/     = <app_root>/data/
  → config    = <app_root>/config.json

Running from source:
  → app_root  = project root (3 levels up from this file)
               src/settlement_form/utils/paths.py → parents[3]
"""
from __future__ import annotations

import sys
from pathlib import Path


def get_app_root() -> Path:
    """Return the directory that contains config.json and the data/ folder."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[3]
