#!/usr/bin/env python3
"""Guard for Phase 45 notification center rollout.

The shell must use a reusable NotificationCenter instead of adding more
one-off alert menus, and the component must remain UI-only.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CENTER = ROOT / "alrajhi_client" / "shell" / "notification_center.py"
MAIN = ROOT / "alrajhi_client" / "views" / "main_window.py"
INIT = ROOT / "alrajhi_client" / "shell" / "__init__.py"


def main() -> int:
    failures: list[str] = []
    for path in (CENTER, MAIN, INIT):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)} parse error: {exc}")
    center_source = CENTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    init_source = INIT.read_text(encoding="utf-8")

    for token in ("class NotificationCenter", "class NotificationCard", "NotificationItem", "show_temporary"):
        if token not in center_source:
            failures.append(f"notification center missing {token}")
    for forbidden in ("DatabaseConnection", "sqlite3", ".execute(", ".query(", "printing_service"):
        if forbidden in center_source:
            failures.append(f"notification center must not contain {forbidden}")
    for token in ("NotificationCenter", "notification_center", "refresh_notification_center", "notify_user"):
        if token not in main_source:
            failures.append(f"main window missing {token}")
    if "menu.exec_(self.top_bar.alert_btn" in main_source:
        failures.append("alerts must open NotificationCenter, not a transient QMenu")
    if "NotificationCenter" not in init_source or "NotificationItem" not in init_source:
        failures.append("shell package must export NotificationCenter and NotificationItem")
    if failures:
        print("Notification center guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("Notification center guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
