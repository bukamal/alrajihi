# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "restaurant_simple_pos_matrix.csv"

CHECKS = [
    ("simple_widget_exists", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "class RestaurantSimplePOSWidget"),
    ("three_section_splitter", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "restaurantSimpleThreeSectionSplitter"),
    ("category_section", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "restaurantSimpleCategoryButton"),
    ("item_section", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "restaurantSimpleItemButton"),
    ("invoice_columns", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "item_name"),
    ("no_exposed_kitchen_buttons", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "checkout_simple_pos_session"),
    ("main_window_uses_simple", "alrajhi_client/views/main_window.py", "'restaurant': RestaurantSimplePOSWidget"),
    ("manifest_uses_simple", "alrajhi_client/workspace/registry/ui_manifest.py", 'factory_name="RestaurantSimplePOSWidget"'),
    ("service_categories", "alrajhi_client/core/services/restaurant_service.py", "def list_menu_categories"),
    ("service_checkout", "alrajhi_client/core/services/restaurant_service.py", "def checkout_simple_pos_session"),
    ("gateway_update_line", "alrajhi_client/gateways/local/restaurant_gateway.py", "def update_order_line"),
    ("gateway_served", "alrajhi_client/gateways/local/restaurant_gateway.py", "def mark_session_lines_served"),
    ("translations_ar", "alrajhi_client/i18n/translator.py", "restaurant.simple_pos_title"),
    ("quality_contract", "alrajhi_client/workspace/quality/restaurant_simple_pos_contract.py", "RESTAURANT_SIMPLE_POS_CONTRACT"),
]

def main() -> int:
    rows = []
    issues = []
    for name, rel, needle in CHECKS:
        path = ROOT / rel
        ok = path.exists() and needle in path.read_text(encoding="utf-8", errors="ignore")
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            issues.append(f"{name}: missing {needle} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase394 restaurant simple POS guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase394 restaurant simple POS guard OK ({len(rows)} checks)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
