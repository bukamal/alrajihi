#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_visual_system_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/basit_visual_system_contract.py", "BASIT_VISUAL_SYSTEM_CONTRACT"),
    ("palette_blue", "alrajhi_client/theme/brand.py", "BASIT_BLUE"),
    ("palette_yellow", "alrajhi_client/theme/brand.py", "BASIT_YELLOW"),
    ("palette_red", "alrajhi_client/theme/brand.py", "BASIT_RED"),
    ("light_tokens", "alrajhi_client/theme/brand.py", "'basit_blue': BASIT_BLUE"),
    ("dark_tokens", "alrajhi_client/theme/brand.py", "'basit_blue': '#2B8CE6'"),
    ("metrics", "alrajhi_client/theme/brand.py", "'basit_pos_card_height': 64"),
    ("qss_phase", "alrajhi_client/theme/qss.py", "Phase401: Basit inspired operational skin"),
    ("qss_cards", "alrajhi_client/theme/qss.py", "QPushButton#restaurantSimpleItemButton"),
    ("qss_total", "alrajhi_client/theme/qss.py", "QLabel#restaurantSimpleTotal"),
    ("qss_dashboard", "alrajhi_client/theme/qss.py", "QPushButton[visualRole=\"dashboard_shortcut\"]"),
    ("restaurant_root_property", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "self.setProperty(\"basitInspired\", True)"),
    ("restaurant_card_property", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "button.setProperty(\"basitCard\", True)"),
    ("restaurant_table_property", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "self.invoice_table.setProperty(\"basitTable\", True)"),
    ("restaurant_total_property", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "self.total_label.setProperty(\"basitTotal\", True)"),
    ("restaurant_splitter_size", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "self.splitter.setSizes([270, 360, 720])"),
]


def main() -> int:
    rows = []
    issues = []
    for name, rel, needle in CHECKS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        ok = needle in text
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            issues.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase401 Basit visual system guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase401 Basit visual system guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
