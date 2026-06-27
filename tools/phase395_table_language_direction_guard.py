# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "table_language_direction_matrix.csv"

CHECKS = [
    ("policy_exists", "alrajhi_client/ui/table_direction_policy.py", "def apply_table_direction"),
    ("tree_policy_exists", "alrajhi_client/ui/table_direction_policy.py", "def apply_table_direction_tree"),
    ("custom_table_uses_policy", "alrajhi_client/views/custom_table_view.py", "apply_table_direction(self)"),
    ("custom_table_no_hardcoded_rtl", "alrajhi_client/views/custom_table_view.py", "self.setLayoutDirection(Qt.RightToLeft)", False),
    ("editable_grid_uses_policy", "alrajhi_client/ui/editable_smart_grid.py", "apply_table_direction(self)"),
    ("runtime_polish_uses_tree", "alrajhi_client/ui/runtime_visual_polish.py", "apply_table_direction_tree(root)"),
    ("runtime_polish_applies_table", "alrajhi_client/ui/runtime_visual_polish.py", "apply_table_direction(table)"),
    ("settings_switch_applies_tree", "alrajhi_client/views/widgets/settings_widget.py", "apply_table_direction_tree(main_window, lang)"),
    ("settings_pages_apply_tree", "alrajhi_client/views/widgets/settings_widget.py", "apply_table_direction_tree(page, lang)"),
    ("modern_widget_language_direction", "alrajhi_client/views/widgets/modern_ui.py", "widget.setLayoutDirection(qt_layout_direction())"),
    ("modern_tables_apply_policy", "alrajhi_client/views/widgets/modern_ui.py", "apply_table_direction(child)"),
    ("restaurant_invoice_table_policy", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "apply_table_direction(self.invoice_table)"),
    ("legacy_invoice_dialog_not_hardcoded_rtl", "alrajhi_client/views/dialogs/invoice_dialog.py", "self.setLayoutDirection(qt_layout_direction())"),
    ("modern_walk_no_tuple_findchildren", "alrajhi_client/views/widgets/modern_ui.py", "for cls in (QTableView, QTableWidget"),
    ("quality_contract", "alrajhi_client/workspace/quality/table_language_direction_contract.py", "TABLE_LANGUAGE_DIRECTION_CONTRACT"),
]


def main() -> int:
    rows = []
    issues = []
    for item in CHECKS:
        name, rel, needle = item[:3]
        positive = bool(item[3]) if len(item) > 3 else True
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        found = needle in text
        ok = found if positive else not found
        rows.append({"check": name, "path": rel, "needle": needle, "expected": "present" if positive else "absent", "status": "OK" if ok else "FAIL"})
        if not ok:
            expectation = "missing" if positive else "unexpected"
            issues.append(f"{name}: {expectation} {needle} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "expected", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase395 table language direction guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase395 table language direction guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
