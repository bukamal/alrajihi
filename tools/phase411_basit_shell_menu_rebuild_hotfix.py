#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_CSV = OUT_DIR / "basit_shell_menu_rebuild_matrix.csv"

CHECKS = [
    ("phase_doc", "doc", "PHASE411_BASIT_SHELL_MENU_REBUILD_HOTFIX.md", "Phase 411"),
    ("contract", "contract", "alrajhi_client/workspace/quality/basit_shell_menu_rebuild_contract.py", "BASIT_SHELL_MENU_REBUILD_CONTRACT"),
    ("styled_background", "main_window", "alrajhi_client/views/main_window.py", "self.setAttribute(Qt.WA_StyledBackground, True)"),
    ("vertical_margin_metric", "main_window", "alrajhi_client/views/main_window.py", "NAV_VERTICAL_MARGIN"),
    ("layout_margin_token", "main_window", "alrajhi_client/views/main_window.py", "self._layout.setContentsMargins(12, NAV_VERTICAL_MARGIN, 12, NAV_VERTICAL_MARGIN)"),
    ("manual_popup_helper", "main_window", "alrajhi_client/views/main_window.py", "def _popup_menu_for_button"),
    ("manual_popup_connect", "main_window", "alrajhi_client/views/main_window.py", "self._popup_menu_for_button(b, m)"),
    ("finish_rebuild", "main_window", "alrajhi_client/views/main_window.py", "def finish_rebuild"),
    ("setup_menus_finish_rebuild", "main_window", "alrajhi_client/views/main_window.py", "self.menu_bar.finish_rebuild()"),
    ("menu_indicator_inline", "main_window_qss", "alrajhi_client/views/main_window.py", "QToolButton#MainNavToolButton::menu-indicator"),
    ("menu_button_inline", "main_window_qss", "alrajhi_client/views/main_window.py", "QToolButton#MainNavToolButton::menu-button"),
    ("menu_arrow_inline", "main_window_qss", "alrajhi_client/views/main_window.py", "QToolButton#MainNavToolButton::menu-arrow"),
    ("menu_button_global", "global_qss", "alrajhi_client/theme/qss.py", "QToolButton#MainNavToolButton::menu-button"),
    ("menu_arrow_global", "global_qss", "alrajhi_client/theme/qss.py", "QToolButton#MainNavToolButton::menu-arrow"),
    ("brand_margin_metric", "brand", "alrajhi_client/theme/brand.py", "basit_shell_nav_vertical_margin"),
]


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _addmenu_body(src: str) -> str:
    match = re.search(r"def addMenu\(self, icon, title\):(.*?)(?:\nclass MainWindow|\n    def [A-Za-z_])", src, flags=re.S)
    return match.group(1) if match else ""


def _margin_sane(src: str) -> tuple[bool, str]:
    ns: dict[str, object] = {}
    # Parse only the metric lines, not importing PyQt.
    values = {}
    for name in ("NAV_BAR_HEIGHT", "NAV_BUTTON_HEIGHT", "NAV_VERTICAL_MARGIN"):
        m = re.search(rf"^{name}\s*=\s*int\(BRAND\.get\('([^']+)'", src, flags=re.M)
        if not m:
            return False, f"missing {name} metric line"
    brand = read("alrajhi_client/theme/brand.py")
    def brand_int(key: str, fallback: int) -> int:
        m = re.search(rf"'{re.escape(key)}'\s*:\s*([0-9]+)", brand)
        return int(m.group(1)) if m else fallback
    nav = brand_int("basit_shell_nav_height", 70)
    btn = brand_int("basit_shell_nav_button_height", 64)
    margin = brand_int("basit_shell_nav_vertical_margin", max(0, (nav - btn) // 2))
    ok = nav >= btn + (margin * 2)
    return ok, f"nav={nav}, button={btn}, vertical_margin={margin}, required={btn + margin * 2}"


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

    main_window = read("alrajhi_client/views/main_window.py")
    addmenu = _addmenu_body(main_window)
    direct_menu = "btn.setMenu(menu)" in addmenu or "btn.setPopupMode(QToolButton.InstantPopup)" in addmenu
    rows.append({
        "check": "no_direct_qtoolbutton_menu",
        "category": "main_window",
        "path": "alrajhi_client/views/main_window.py",
        "needle": "addMenu body does not attach native QMenu subcontrol",
        "status": "FAIL" if direct_menu else "OK",
        "detail": "direct setMenu/InstantPopup found in addMenu body" if direct_menu else "manual popup only",
    })
    sane, detail = _margin_sane(main_window)
    rows.append({
        "check": "nav_height_margin_equation",
        "category": "metrics",
        "path": "alrajhi_client/theme/brand.py",
        "needle": "NAV_BAR_HEIGHT >= NAV_BUTTON_HEIGHT + 2*NAV_VERTICAL_MARGIN",
        "status": "OK" if sane else "FAIL",
        "detail": detail,
    })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "category", "path", "needle", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase411 Basit shell menu rebuild hotfix failed:")
        for row in failures:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase411 Basit shell menu rebuild hotfix OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
