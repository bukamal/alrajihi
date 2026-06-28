#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_CSV = OUT_DIR / "user_preferences_persistence_matrix.csv"

CHECKS = [
    ("phase_doc", "doc", "PHASE413_USER_PREFERENCES_PERSISTENCE.md", "Phase 413"),
    ("contract", "contract", "alrajhi_client/workspace/quality/user_preferences_persistence_contract.py", "USER_PREFERENCES_PERSISTENCE_CONTRACT"),
    ("service_file", "service", "alrajhi_client/core/services/user_preferences_service.py", "class UserPreferencesService"),
    ("qsettings_backend", "service", "alrajhi_client/core/services/user_preferences_service.py", "QSettings"),
    ("user_namespace", "service", "alrajhi_client/core/services/user_preferences_service.py", "def _current_user_key"),
    ("branch_namespace", "service", "alrajhi_client/core/services/user_preferences_service.py", "def _current_branch_key"),
    ("immediate_sync", "service", "alrajhi_client/core/services/user_preferences_service.py", "self._settings.sync()"),
    ("dashboard_cash_hidden_key", "service", "alrajhi_client/core/services/user_preferences_service.py", "DASHBOARD_CASH_HIDDEN"),
    ("dashboard_cash_mode_key", "service", "alrajhi_client/core/services/user_preferences_service.py", "DASHBOARD_CASH_VIEW_MODE"),
    ("dashboard_import", "dashboard", "alrajhi_client/views/widgets/dashboard_widget.py", "from core.services.user_preferences_service import user_preferences_service"),
    ("dashboard_load_hidden", "dashboard", "alrajhi_client/views/widgets/dashboard_widget.py", "user_preferences_service.dashboard_cash_balances_hidden()"),
    ("dashboard_load_mode", "dashboard", "alrajhi_client/views/widgets/dashboard_widget.py", "user_preferences_service.dashboard_cash_view_mode()"),
    ("dashboard_save_hidden", "dashboard", "alrajhi_client/views/widgets/dashboard_widget.py", "user_preferences_service.set_dashboard_cash_balances_hidden"),
    ("dashboard_save_mode", "dashboard", "alrajhi_client/views/widgets/dashboard_widget.py", "user_preferences_service.set_dashboard_cash_view_mode"),
]


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def main() -> int:
    rows: list[dict[str, str]] = []
    for check, category, rel, needle in CHECKS:
        content = read(rel)
        ok = bool(content) and needle in content
        rows.append({
            "check": check,
            "category": category,
            "path": rel,
            "needle": needle,
            "status": "OK" if ok else "FAIL",
            "detail": "" if ok else f"missing {needle!r}",
        })

    service = read("alrajhi_client/core/services/user_preferences_service.py")
    dashboard = read("alrajhi_client/views/widgets/dashboard_widget.py")
    extra_checks = [
        ("dashboard_hidden_default_false", "service", "dashboard_cash_balances_hidden(self) -> bool", "False" in service),
        ("dashboard_mode_validated", "service", "mode in {'today', 'general'}", "mode in {\"today\", \"general\"}" in service),
        ("dashboard_not_transient_false", "dashboard", "no transient _cash_balances_hidden = False", "self._cash_balances_hidden = False" not in dashboard),
        ("dashboard_initial_icon_restored", "dashboard", "eye-slash if restored hidden", "'fa5s.eye-slash' if self._cash_balances_hidden else 'fa5s.eye'" in dashboard),
    ]
    for check, category, needle, ok in extra_checks:
        rows.append({
            "check": check,
            "category": category,
            "path": "derived",
            "needle": needle,
            "status": "OK" if ok else "FAIL",
            "detail": "" if ok else "derived check failed",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "category", "path", "needle", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase413 user preferences persistence failed:")
        for row in failures:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase413 user preferences persistence OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
