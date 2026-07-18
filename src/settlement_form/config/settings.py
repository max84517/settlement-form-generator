"""
Persist user UI preferences to config.json so the app restores
its last state on every launch.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config.json"

_DEFAULTS: dict[str, Any] = {
    "input_excel_path": "",
    "sub_category_selection": [],      # [] means "all selected"
    "status_filter_mode": "2nd_ver",   # "2nd_ver" | "custom"
    "status_selection": [],            # [] means "all selected" (used in custom mode)
    "select_all": True,
    "turn_status_flag": False,
    "template_folder": "",
    "settlement_info_path": "",
    "output_folder": "",
}


def load() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            # Fill in any missing keys with defaults
            return {**_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(data: dict[str, Any]) -> None:
    _CONFIG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
