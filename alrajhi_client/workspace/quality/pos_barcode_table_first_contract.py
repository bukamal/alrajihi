# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT = {
    "phase": 430,
    "name": "POS Barcode Table First Layout",
    "owner": "POSWidget",
    "pos_surface": "barcode_table_first",
    "restaurant_surface": "item_card_grid",
}

REQUIRED_SOURCES = (
    "alrajhi_client/views/widgets/pos_widget.py",
    "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
    "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
    "alrajhi_client/ui/operational_item_card_grid.py",
    "alrajhi_client/theme/qss.py",
)


def _read(root: Path, rel: str) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def pos_barcode_table_first_matrix(root: Path | str | None = None) -> list[dict[str, object]]:
    base = Path(root or Path(__file__).resolve().parents[3])
    pos = _read(base, "alrajhi_client/views/widgets/pos_widget.py")
    restaurant = _read(base, "alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    simple = _read(base, "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    qss = _read(base, "alrajhi_client/theme/qss.py")
    component = _read(base, "alrajhi_client/ui/operational_item_card_grid.py")

    scan_idx = pos.find("layout.addLayout(scan_row)")
    table_idx = pos.find("self.table = POSLineGrid")
    card_idx = pos.find("posOperationalItemCardGrid")

    checks = [
        ("pos_no_operational_card_import", "alrajhi_client/views/widgets/pos_widget.py", "from ui.operational_item_card_grid import OperationalItemCardGrid" not in pos),
        ("pos_no_card_instance", "alrajhi_client/views/widgets/pos_widget.py", "posOperationalItemCardGrid" not in pos and "self.item_card_grid" not in pos),
        ("pos_no_catalog_card_loading", "alrajhi_client/views/widgets/pos_widget.py", "catalog_service.items" not in pos and "_load_pos_item_cards" not in pos),
        ("pos_keeps_scan_row", "alrajhi_client/views/widgets/pos_widget.py", "self.barcode_input = QLineEdit()" in pos and "scan_entered_barcode" in pos),
        ("pos_table_directly_after_scan", "alrajhi_client/views/widgets/pos_widget.py", scan_idx >= 0 and table_idx > scan_idx and (card_idx < 0 or not (scan_idx < card_idx < table_idx))),
        ("pos_global_filter_scan_only", "alrajhi_client/views/widgets/pos_widget.py", "def set_global_filter" in pos and "self.barcode_input.setText(text or '')" in pos and "_load_pos_item_cards" not in pos),
        ("restaurant_card_grid_preserved", "alrajhi_client/views/restaurant/restaurant_pos_widget.py", "OperationalItemCardGrid" in restaurant and "restaurantMenuOperationalItemCardGrid" in restaurant),
        ("simple_restaurant_card_grid_preserved", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "OperationalItemCardGrid" in simple and "restaurantSimpleItemCardGrid" in simple),
        ("component_still_exists", "alrajhi_client/ui/operational_item_card_grid.py", "class OperationalItemCardGrid" in component and "default_columns: int = 3" in component),
        ("qss_no_pos_card_selector", "alrajhi_client/theme/qss.py", "posOperationalItemCardGrid" not in qss and "Phase428/430" in qss),
    ]
    return [
        {"key": key, "path": path, "status": "OK" if ok else "FAIL", "detail": "Phase430 POS barcode/table-first layout contract"}
        for key, path, ok in checks
    ]


def pos_barcode_table_first_summary(root: Path | str | None = None) -> dict[str, object]:
    rows = pos_barcode_table_first_matrix(root)
    failures = [row for row in rows if row["status"] != "OK"]
    return {"ready": not failures, "rows": rows, "failures": failures}
