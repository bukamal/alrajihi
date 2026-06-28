# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION = {
    "phase": 428,
    "name": "Operational Item Card Grid Unification",
    "owner": "OperationalItemCardGrid",
    "default_columns": 3,
    "surfaces": ("restaurant", "restaurant_simple", "cafe"),
    "pos_surface": "barcode_table_first",
}

REQUIRED_SOURCES = (
    "alrajhi_client/ui/operational_item_card_grid.py",
    "alrajhi_client/views/widgets/pos_widget.py",
    "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
    "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
    "alrajhi_client/theme/qss.py",
)


def _read(root: Path, rel: str) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def operational_item_card_grid_matrix(root: Path | str | None = None) -> list[dict[str, object]]:
    base = Path(root or Path(__file__).resolve().parents[3])
    component = _read(base, "alrajhi_client/ui/operational_item_card_grid.py")
    pos = _read(base, "alrajhi_client/views/widgets/pos_widget.py")
    restaurant = _read(base, "alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    simple = _read(base, "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    qss = _read(base, "alrajhi_client/theme/qss.py")
    checks = [
        ("component_exists", "alrajhi_client/ui/operational_item_card_grid.py", "class OperationalItemCardGrid" in component),
        ("component_signal", "alrajhi_client/ui/operational_item_card_grid.py", "itemActivated = pyqtSignal(object)" in component),
        ("component_default_three_columns", "alrajhi_client/ui/operational_item_card_grid.py", "default_columns: int = 3" in component and "return self.default_columns" in component),
        ("pos_barcode_table_first", "alrajhi_client/views/widgets/pos_widget.py", "POSLineGrid" in pos and "barcode_input" in pos and "posOperationalItemCardGrid" not in pos),
        ("pos_no_material_card_surface", "alrajhi_client/views/widgets/pos_widget.py", "OperationalItemCardGrid" not in pos and "catalog_service.items" not in pos and "restaurantMenuItemButton" not in pos),
        ("restaurant_uses_component", "alrajhi_client/views/restaurant/restaurant_pos_widget.py", "OperationalItemCardGrid" in restaurant and "restaurantMenuOperationalItemCardGrid" in restaurant),
        ("restaurant_no_local_menu_buttons", "alrajhi_client/views/restaurant/restaurant_pos_widget.py", "button = QPushButton(self._menu_card_label(item))" not in restaurant),
        ("simple_uses_component", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "OperationalItemCardGrid" in simple and "restaurantSimpleItemCardGrid" in simple),
        ("simple_three_column_contract", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "default_columns=3" in simple),
        ("qss_shared_surface", "alrajhi_client/theme/qss.py", "operationalItemCardButton" in qss and "Phase428" in qss),
    ]
    return [
        {"key": key, "path": path, "status": "OK" if ok else "FAIL", "detail": "Phase428/430 operational item-card grid contract"}
        for key, path, ok in checks
    ]


def operational_item_card_grid_summary(root: Path | str | None = None) -> dict[str, object]:
    rows = operational_item_card_grid_matrix(root)
    failures = [row for row in rows if row["status"] != "OK"]
    return {"ready": not failures, "rows": rows, "failures": failures}
