# -*- coding: utf-8 -*-
"""Phase 413 contract: persistent user UI preferences."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any


USER_PREFERENCES_PERSISTENCE_CONTRACT: Dict[str, Any] = {
    "phase": 413,
    "name": "user_preferences_persistence",
    "scope": [
        "core.services.user_preferences_service",
        "DashboardWidget cash privacy toggle",
        "DashboardWidget cash movement mode toggle",
    ],
    "requirements": [
        "Runtime UI privacy choices must be stored as user/workstation preferences, not transient widget state.",
        "Dashboard cash balance hiding must restore after closing and reopening the client.",
        "Dashboard cash movement mode must restore after closing and reopening the client.",
        "Preference keys must be namespaced per current user and optionally per branch to avoid cross-user leakage.",
        "Writes must sync immediately so a crash or direct application close does not lose the last UI choice.",
    ],
    "required_outputs": [
        "tools/audit_outputs/user_preferences_persistence_matrix.csv",
    ],
}


def user_preferences_persistence_summary(root: Path | str | None = None) -> Dict[str, Any]:
    base = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    required = [
        base / "alrajhi_client/core/services/user_preferences_service.py",
        base / "PHASE413_USER_PREFERENCES_PERSISTENCE.md",
        base / "tools/phase413_user_preferences_persistence_guard.py",
        base / "tests/test_phase413_user_preferences_persistence.py",
    ]
    return {
        "phase": 413,
        "ready": all(path.exists() for path in required),
        "required_files": [str(path.relative_to(base)) for path in required],
    }
