"""
Per-user config persistence.

Each user gets their own  config_<name>.json  at the app root.
A shared  users.json  stores the user list and remembers the last login.
"""
from __future__ import annotations

import json
import re
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

# ── User list ────────────────────────────────────────────────────────────────

def _users_path() -> Path:
    return get_app_root() / "users.json"


def load_users() -> list[str]:
    p = _users_path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("users", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_users(users: list[str]) -> None:
    existing = _load_users_raw()
    existing["users"] = users
    _users_path().write_text(json.dumps(existing, indent=2, ensure_ascii=False),
                             encoding="utf-8")


def get_last_user() -> str:
    p = _users_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("last_user", "")
        except (json.JSONDecodeError, OSError):
            pass
    return ""


def set_last_user(username: str) -> None:
    data = _load_users_raw()
    data["last_user"] = username
    _users_path().write_text(json.dumps(data, indent=2, ensure_ascii=False),
                             encoding="utf-8")


def _load_users_raw() -> dict:
    p = _users_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ── Per-user config ──────────────────────────────────────────────────────────

def _safe_name(username: str) -> str:
    """Strip characters that are invalid in filenames."""
    return re.sub(r'[\\/:*?"<>|]', "_", username.strip())


def _config_path(username: str) -> Path:
    return get_app_root() / f"config_{_safe_name(username)}.json"


def load(username: str = "") -> dict[str, Any]:
    path = _config_path(username) if username else get_app_root() / "config.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(data: dict[str, Any], username: str = "") -> None:
    path = _config_path(username) if username else get_app_root() / "config.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_user(username: str) -> None:
    """Remove a user's config file and entry from the user list."""
    cfg = _config_path(username)
    if cfg.exists():
        cfg.unlink()
    users = load_users()
    if username in users:
        users.remove(username)
        save_users(users)
    # Clear last_user if it was this user
    if get_last_user() == username:
        set_last_user("")
