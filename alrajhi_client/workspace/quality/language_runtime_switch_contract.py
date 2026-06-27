# -*- coding: utf-8 -*-
"""Phase 393 language runtime switch safety contract.

The UI language switch must not re-enter settings slots, rebuild shell menus
synchronously from a combo-box signal, or recursively wrap sys.excepthook.
This module is intentionally static/no-PyQt so CI and release gates can run it
without a display server.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def language_runtime_switch_matrix(root: Path) -> List[Dict[str, object]]:
    checks: List[Dict[str, object]] = []

    settings = _read(root, "alrajhi_client/views/widgets/settings_widget.py")
    login = _read(root, "alrajhi_client/views/dialogs/login_dialog.py")
    hook = _read(root, "alrajhi_client/offline_read.py")
    translator = _read(root, "alrajhi_client/i18n/translator.py")

    checks.append({
        "check": "settings_reentrant_guard",
        "passed": "_language_change_in_progress" in settings and "_apply_runtime_language_change" in settings,
        "detail": "Settings language changes are guarded against recursive re-entry.",
    })
    checks.append({
        "check": "settings_deferred_shell_refresh",
        "passed": "QTimer.singleShot(0, _refresh_shell)" in settings,
        "detail": "Shell menu/topbar refresh is deferred outside the combo-box signal stack.",
    })
    checks.append({
        "check": "main_window_language_state_updated",
        "passed": "main_window._current_language = lang" in settings,
        "detail": "MainWindow language state is updated before menu rebuild.",
    })
    checks.append({
        "check": "login_reentrant_guard",
        "passed": "_language_change_in_progress" in login and "finally:" in login,
        "detail": "Login language combo changes are guarded as well.",
    })
    checks.append({
        "check": "offline_hook_idempotent",
        "passed": "_alrajhi_offline_hook" in hook and "return current_hook" in hook,
        "detail": "Global exception hook installation is idempotent.",
    })
    checks.append({
        "check": "offline_hook_recursion_bypass",
        "passed": "RecursionError" in hook and "sys.__excepthook__" in hook and "in_hook" in hook,
        "detail": "RecursionError is routed to Python's original hook without wrapper recursion.",
    })
    checks.append({
        "check": "translator_load_reentry_guard",
        "passed": "_phase392_load_in_progress" in translator and "language_settings_saved" in translator,
        "detail": "French translation reload has a re-entry guard and runtime save labels.",
    })
    return checks


def language_runtime_switch_summary(root: Path) -> Dict[str, object]:
    rows = language_runtime_switch_matrix(root)
    failed = [row for row in rows if not row["passed"]]
    return {
        "checks": len(rows),
        "passed": not failed,
        "failed_checks": failed,
    }
