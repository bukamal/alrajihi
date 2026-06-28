# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Iterable

PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE = {
    "phase": 429,
    "owner": "OperationalFullscreenController",
    "shortcut": "F11",
    "exit_shortcut": "Esc",
    "shell_chrome": ("menu_bar", "action_bar", "notification_center", "workspace_tab_bar", "QToolBar"),
    "button_key": "fullscreen",
}

REQUIRED_SOURCES: tuple[str, ...] = (
    "alrajhi_client/ui/operational_fullscreen_controller.py",
    "alrajhi_client/views/main_window.py",
    "alrajhi_client/shell/unified_action_bar.py",
    "alrajhi_client/workspace/registry/ui_manifest.py",
    "alrajhi_client/views/widgets/pos_widget.py",
    "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
    "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8", errors="ignore")


def _ok(key: str, path: str, detail: str) -> dict[str, str]:
    return {"key": key, "path": path, "status": "OK", "detail": detail}


def _fail(key: str, path: str, detail: str) -> dict[str, str]:
    return {"key": key, "path": path, "status": "FAIL", "detail": detail}


def operational_fullscreen_matrix(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    controller = _read(root, "alrajhi_client/ui/operational_fullscreen_controller.py")
    main = _read(root, "alrajhi_client/views/main_window.py")
    action_bar = _read(root, "alrajhi_client/shell/unified_action_bar.py")
    registry = _read(root, "alrajhi_client/workspace/registry/ui_manifest.py")
    pos = _read(root, "alrajhi_client/views/widgets/pos_widget.py")
    restaurant_simple = _read(root, "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    restaurant_pos = _read(root, "alrajhi_client/views/restaurant/restaurant_pos_widget.py")

    checks = [
        ("controller_class", "alrajhi_client/ui/operational_fullscreen_controller.py", "class OperationalFullscreenController" in controller, "central fullscreen controller exists"),
        ("controller_hides_shell", "alrajhi_client/ui/operational_fullscreen_controller.py", all(token in controller for token in ("menu_bar", "action_bar", "notification_center", "tabBar().setVisible(False)", "QToolBar")), "controller hides shell chrome and workspace tab bar"),
        ("controller_exit_overlay", "alrajhi_client/ui/operational_fullscreen_controller.py", "OperationalFullscreenExitButton" in controller and "refresh_overlay_position" in controller, "floating exit button exists and repositions"),
        ("mainwindow_owns_controller", "alrajhi_client/views/main_window.py", "OperationalFullscreenController(self)" in main and "toggle_operational_fullscreen" in main, "MainWindow owns the shared controller"),
        ("esc_exits_first", "alrajhi_client/views/main_window.py", "controller.is_active()" in main and "controller.exit()" in main and "self.switch_page('dashboard')" in main, "Esc exits fullscreen before dashboard navigation"),
        ("f11_global_shortcut", "alrajhi_client/views/main_window.py", "operational_fullscreen_shortcut" in main and "QKeySequence('F11')" in main and "Qt.ApplicationShortcut" in main, "F11 toggles shared operational fullscreen globally"),
        ("action_spec", "alrajhi_client/workspace/registry/ui_manifest.py", '"fullscreen": WorkspaceActionSpec' in registry and '"fullscreen"' in registry, "fullscreen action declared in registry"),
        ("actionbar_button", "alrajhi_client/shell/unified_action_bar.py", "ActionBarUtilityButton_fullscreen" in action_bar and "self.fullscreen_btn" in action_bar, "shared action bar exposes fullscreen button"),
        ("pos_delegates", "alrajhi_client/views/widgets/pos_widget.py", "window.toggle_operational_fullscreen()" in pos and "QKeySequence(\"F11\")" not in pos and "showFullScreen" not in pos, "POS delegates fullscreen to MainWindow and no longer owns F11/fullscreen"),
        ("restaurant_simple_button", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "restaurantSimpleFullscreenButton" in restaurant_simple and "window.toggle_operational_fullscreen()" in restaurant_simple, "simple restaurant surface delegates fullscreen centrally"),
        ("restaurant_order_button", "alrajhi_client/views/restaurant/restaurant_pos_widget.py", "restaurantOrderFullscreenButton" in restaurant_pos and "window.toggle_operational_fullscreen()" in restaurant_pos, "restaurant/cafe order surface delegates fullscreen centrally"),
    ]
    for key, path, passed, detail in checks:
        rows.append(_ok(key, path, detail) if passed else _fail(key, path, detail))

    offenders: list[str] = []
    for rel in REQUIRED_SOURCES:
        if rel == "alrajhi_client/ui/operational_fullscreen_controller.py":
            continue
        text = _read(root, rel)
        if "showFullScreen" in text:
            offenders.append(rel)
    rows.append(_ok("no_local_showfullscreen", "alrajhi_client", "only OperationalFullscreenController calls showFullScreen") if not offenders else _fail("no_local_showfullscreen", ", ".join(offenders), "showFullScreen must not be called by feature pages"))
    return rows


def operational_fullscreen_summary(root: Path) -> dict[str, object]:
    rows = operational_fullscreen_matrix(root)
    failures = [row for row in rows if row["status"] != "OK"]
    return {"ready": not failures, "checks": len(rows), "failures": failures}
