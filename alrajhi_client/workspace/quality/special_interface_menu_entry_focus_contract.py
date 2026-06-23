# -*- coding: utf-8 -*-
"""Phase 374 contract: specialized interfaces menu and material-column entry focus."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 374


def _read(rel: str, root: Path | None = None) -> str:
    return ((root or ROOT) / rel).read_text(encoding="utf-8")


def special_interface_menu_entry_focus_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    manifest = _read("alrajhi_client/workspace/registry/ui_manifest.py", base)
    translator = _read("alrajhi_client/i18n/translator.py", base)
    keyboard = _read("alrajhi_client/ui/table_keyboard_policy.py", base)
    schema = _read("alrajhi_client/features/transactions/grids/transaction_column_schema.py", base)
    rows: List[Dict[str, object]] = []

    def add(key: str, category: str, description: str, ok: bool, detail: str = "") -> None:
        rows.append({
            "key": key,
            "category": category,
            "description": description,
            "status": "pass" if ok else "fail",
            "detail": detail,
        })

    add("quick_menu_renamed", "navigation", "Quick menu button is renamed to fit specialized interfaces", '"quick",\n        "nav_special_interfaces"' in manifest, "nav_special_interfaces")
    add("quick_menu_icon", "navigation", "Specialized interfaces menu uses a grouped interface icon", '"layer-group"' in manifest, "layer-group")
    for key, label, page in (
        ("restaurant", "restaurant.interface_title", "restaurant"),
        ("cafe", "cafe.interface_title", "cafe"),
        ("apparel", "apparel.interface_title", "apparel"),
    ):
        marker = f'_entry("{key}", "{label}",'
        add(f"quick_entry_{key}", "navigation", f"{key} interface is exposed from the specialized interfaces menu", marker in manifest and f'page_id="{page}"' in manifest, marker)

    quick_block = manifest.split('WorkspaceMenuSpec(\n        "quick",', 1)[1].split('\n    ),\n)', 1)[0] if 'WorkspaceMenuSpec(\n        "quick",' in manifest else ""
    add("quick_only_vertical_pages", "navigation", "Specialized interface menu contains restaurant, cafe and apparel only", all(token in quick_block for token in ("restaurant.interface_title", "cafe.interface_title", "apparel.interface_title")) and "new_sales_invoice" not in quick_block and "open_quick_open" not in quick_block, "vertical pages only")
    add("no_top_restaurant_menu", "navigation", "Restaurant no longer appears as its own top-level menu button", 'WorkspaceMenuSpec(\n        "restaurant",' not in manifest, "restaurant top menu removed")
    add("no_top_cafe_menu", "navigation", "Cafe no longer appears as its own top-level menu button", 'WorkspaceMenuSpec(\n        "cafe",' not in manifest, "cafe top menu removed")
    add("home_verticals_removed", "navigation", "Home menu no longer duplicates restaurant/cafe/apparel entries", all(token not in manifest.split('WorkspaceMenuSpec(\n        "home",', 1)[1].split('WorkspaceMenuSpec(', 1)[0] for token in ("restaurant.interface_title", "restaurant.dashboard", "restaurant.cafe_workspace_title", "apparel.workspace_title")), "home simplified")
    add("inventory_apparel_removed", "navigation", "Inventory menu no longer duplicates apparel entry", 'WorkspaceMenuSpec(\n        "inventory",' in manifest and 'apparel.interface_title' not in manifest.split('WorkspaceMenuSpec(\n        "inventory",', 1)[1].split('WorkspaceMenuSpec(', 1)[0] and 'apparel.workspace_title' not in manifest.split('WorkspaceMenuSpec(\n        "inventory",', 1)[1].split('WorkspaceMenuSpec(', 1)[0], "inventory simplified")

    for key, ar, en, de in (
        ("nav_special_interfaces", "واجهات النشاط", "Industry interfaces", "Branchenoberflächen"),
        ("restaurant.interface_title", "واجهة المطعم", "Restaurant interface", "Restaurant-Oberfläche"),
        ("cafe.interface_title", "واجهة المقهى", "Cafe interface", "Café-Oberfläche"),
        ("apparel.interface_title", "واجهة الألبسة", "Apparel interface", "Bekleidungsoberfläche"),
    ):
        add(f"translation_{key}", "i18n", f"{key} is translated in Arabic, English and German", key in translator and ar in translator and en in translator and de in translator, key)

    add("entry_priority_method", "editable_grid", "Keyboard policy sorts preferred columns by semantic priority", "def _standard_entry_priority" in keyboard and "material/item beats barcode" in keyboard, "_standard_entry_priority")
    add("entry_columns_sorted", "editable_grid", "Preferred entry columns are sorted so item/material wins over barcode", "return sorted(preferred, key=lambda c: (self._standard_entry_priority(c), c))" in keyboard, "sorted preferred")
    add("preferred_order", "editable_grid", "Preferred entry keys keep item/material/product before barcode", '_standard_preferred_entry_keys = ("item", "material", "product", "barcode")' in keyboard, "item before barcode")
    add("sales_row_noneditable", "editable_grid", "Sales invoice row number column is not editable", 'TransactionColumn("row", "#", True, True, True, 44, editable=False)' in schema, "sales row")
    add("purchase_row_noneditable", "editable_grid", "Purchase invoice row number column is not editable", schema.count('TransactionColumn("row", "#", True, True, True, 44, editable=False)') >= 2, "purchase row")

    return rows


def special_interface_menu_entry_focus_summary(root: Path | None = None) -> Dict[str, object]:
    rows = special_interface_menu_entry_focus_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    return {
        "phase": PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "ready": not issues,
    }


__all__ = [
    "PHASE",
    "special_interface_menu_entry_focus_matrix",
    "special_interface_menu_entry_focus_summary",
]
