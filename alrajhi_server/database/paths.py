# -*- coding: utf-8 -*-
"""Central writable database path for the server.

The desktop client and the embedded/API server must use the same physical
SQLite file on the machine that works as the server.  Older builds used
``alrajhi_server/data/alrajhi_server.db`` for the API and ``~/.alrajhi`` (or
APPDATA) for the desktop UI, which created a split-brain situation: the server
was alive, but the tabs in the desktop showed a different/local database.
"""
from __future__ import annotations

import os
from pathlib import Path


def _client_compatible_data_dir() -> Path:
    if os.name == 'nt':
        # Do not write to Program Files/_internal.  Prefer the new writable app
        # data folder, but keep using the legacy DB when it already exists.
        legacy_base = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Roaming')
        legacy = Path(legacy_base) / 'Alrajhi'
        if (legacy / 'alrajhi_data.db').exists():
            return legacy
        base = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or str(Path.home() / 'AppData' / 'Local')
        return Path(base) / 'AlrajhiAccounting'
    return Path.home() / '.alrajhi'


def get_server_db_path() -> str:
    # Explicit override for deployments or tests.
    explicit = os.environ.get('ALRAJHI_SERVER_DB_PATH')
    if explicit:
        return str(Path(explicit).expanduser())
    return str(_client_compatible_data_dir() / 'alrajhi_data.db')


def ensure_data_dir() -> str:
    db_path = Path(get_server_db_path())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path.parent)
