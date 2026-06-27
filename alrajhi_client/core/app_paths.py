# -*- coding: utf-8 -*-
"""Writable runtime paths for the desktop application.

Never write user data, databases, templates, logs, or license files inside the
installation directory (for example Program Files or PyInstaller _internal).
Those locations are read-only for normal Windows users.  All mutable data goes
under the current user's application-data directory.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_FOLDER_NAME = "AlrajhiAccounting"
LEGACY_FOLDER_NAME = "Alrajhi"


def _windows_base() -> Path:
    return Path(
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or (Path.home() / "AppData" / "Local")
    )


def user_data_dir() -> Path:
    """Return a writable per-user directory for all runtime data."""
    explicit = os.environ.get("ALRAJHI_DATA_DIR")
    if explicit:
        path = Path(explicit).expanduser()
    elif os.name == "nt":
        path = _windows_base() / APP_FOLDER_NAME
    else:
        path = Path.home() / ".alrajhi"
    path.mkdir(parents=True, exist_ok=True)
    return path


def legacy_user_data_dir() -> Path:
    """Old path used by earlier builds; useful for DB compatibility."""
    if os.name == "nt":
        return Path(os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Roaming")) / LEGACY_FOLDER_NAME
    return Path.home() / ".alrajhi"


def ensure_dir(name: str) -> Path:
    path = user_data_dir() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    return ensure_dir("data")


def logs_dir() -> Path:
    return ensure_dir("logs")


def backups_dir() -> Path:
    return ensure_dir("backups")


def printing_dir() -> Path:
    return ensure_dir("printing")


def barcode_templates_dir() -> Path:
    path = printing_dir() / "barcode_templates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def license_file() -> Path:
    return user_data_dir() / "license.dat"


def network_license_file() -> Path:
    return user_data_dir() / "network_license.dat"


def feature_license_file(feature: str) -> Path:
    """Return the per-device activation file for an optional paid feature.

    Network keeps its historical filename for backward compatibility.  Other
    vertical modules use the same writable data folder and the same encrypted
    payload format as the network license.
    """
    safe = ''.join(ch for ch in str(feature or '').strip().lower() if ch.isalnum() or ch in {'_', '-'})
    if safe == 'network':
        return network_license_file()
    if not safe:
        safe = 'feature'
    return user_data_dir() / f"{safe}_license.dat"


def runtime_resource_path(*parts: str) -> Path:
    """Read-only bundled resource path, safe for PyInstaller onefile/onedir."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base.joinpath(*parts)


def local_db_path() -> Path:
    """Keep DB compatible with older/server code, but never under Program Files."""
    explicit = os.environ.get("ALRAJHI_DB_PATH")
    if explicit:
        p = Path(explicit).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # Existing installations used %APPDATA%/Alrajhi/alrajhi_data.db.  Keep using
    # it if it exists so an update does not look like an empty fresh install.
    legacy = legacy_user_data_dir() / "alrajhi_data.db"
    if legacy.exists():
        legacy.parent.mkdir(parents=True, exist_ok=True)
        return legacy

    p = user_data_dir() / "alrajhi_data.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
