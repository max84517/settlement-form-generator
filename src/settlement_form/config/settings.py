"""
Single-file config: all users and their settings in one config.json.

Structure:
{
  "users": ["Alice", "Bob"],
  "last_user": "Alice",
  "configs": {
    "Alice": { "input_excel_path": "...", ... },
    "Bob":   { "input_excel_path": "...", ... }
  }
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from settlement_form.utils.paths import get_app_root

_DEFAULTS: dict[str, Any] = {
    "input_excel_path": "",
    "sub_category_selection": [],
    "status_filter_mode": "2nd_ver",
    "status_selection": [],
    "select_all": True,
    "turn_status_flag": False,
    "template_folder": "",
    "settlement_info_path": "",
    "output_folder": "",
}


def _config_path() -> Path:
    return get_app_root() / "config.json"


def _load_all() -> dict:
    p = _config_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_all(data: dict) -> None:
    _config_path().write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── User list ────────────────────────────────────────────────────────────────

def load_users() -> list[str]:
    return _load_all().get("users", [])


def save_users(users: list[str]) -> None:
    data = _load_all()
    data["users"] = users
    _save_all(data)


def get_last_user() -> str:
    return _load_all().get("last_user", "")


def set_last_user(username: str) -> None:
    data = _load_all()
    data["last_user"] = username
    _save_all(data)


def delete_user(username: str) -> None:
    data = _load_all()
    if username in data.get("users", []):
        data["users"].remove(username)
    data.get("configs", {}).pop(username, None)
    if data.get("last_user") == username:
        data["last_user"] = ""
    _save_all(data)


# ── Per-user config ──────────────────────────────────────────────────────────

def load(username: str = "") -> dict[str, Any]:
    data = _load_all()
    user_cfg = data.get("configs", {}).get(username, {})
    return {**_DEFAULTS, **user_cfg}


def save(cfg: dict[str, Any], username: str = "") -> None:
    data = _load_all()
    if "configs" not in data:
        data["configs"] = {}
    data["configs"][username] = cfg
    _save_all(data)
