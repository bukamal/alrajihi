# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "restaurant_item_card_surface_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/restaurant_item_card_surface_contract.py", "RESTAURANT_ITEM_CARD_SURFACE_CONTRACT"),
    ("item_surface_property", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "restaurant_same_card_surface"),
    ("item_single_column_grid", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "self.items_grid.addWidget(button, index, 0)"),
    ("item_category_like_height", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "button.setMinimumHeight(58)"),
    ("item_category_like_size_policy", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "QSizePolicy.Expanding, QSizePolicy.Fixed"),
    ("item_row_stretch", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "self.items_grid.setRowStretch(len(self.menu_items), 1)"),
    ("no_responsive_item_columns", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "columns = 3 if self.width() >= 1200 else 2", "absent"),
    ("no_multicolumn_item_add", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "index // columns, index % columns", "absent"),
]


def main() -> int:
    rows = []
    issues = []
    for entry in CHECKS:
        name, rel, needle = entry[:3]
        mode = entry[3] if len(entry) > 3 else "present"
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        found = needle in text
        ok = found if mode == "present" else not found
        rows.append({
            "check": name,
            "path": rel,
            "needle": needle,
            "mode": mode,
            "status": "OK" if ok else "FAIL",
        })
        if not ok:
            expectation = "missing" if mode == "present" else "unexpected"
            issues.append(f"{name}: {expectation} {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "mode", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase396 restaurant item card surface guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase396 restaurant item card surface guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
