# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.editable_grid_invoice_enter_route_contract import (  # noqa: E402
    FILES,
    FORBIDDEN_MARKERS,
    PURCHASE_ROUTE,
    REQUIRED_MARKERS,
    SALES_ROUTE,
    editable_grid_invoice_enter_route_summary,
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase386_sources_parse_and_markers_hold():
    for key, path in FILES.items():
        source = read(path)
        ast.parse(source)
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker in source, (key, marker)
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker not in source, (key, marker)


def test_phase386_purchase_and_sales_routes_are_semantic_not_physical():
    source = read("alrajhi_client/ui/table_keyboard_policy.py")
    assert PURCHASE_ROUTE in source
    assert SALES_ROUTE in source
    assert source.index("ordered_wanted") < source.index("if self._standard_is_traversable(index):\n                    return col")
    # The purchase route explicitly skips batch/expiry during Enter traversal.
    assert '("cost", "price"), ("discount",), ("tax",), ("total",), ("notes",)' in source


def test_phase386_purchase_cost_header_is_visible_price_label():
    schema = read("alrajhi_client/features/transactions/grids/transaction_column_schema.py")
    assert 'TransactionColumn("cost", "transaction_column_price", False, True, True, 110, numeric=True)' in schema
    registry = read("alrajhi_client/workspace/tables/table_column_registry.py")
    assert '_transaction_column("cost", "transaction_column_price", width=110, numeric=True)' in registry


def test_phase386_guard_summary_ready():
    summary = editable_grid_invoice_enter_route_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 30
