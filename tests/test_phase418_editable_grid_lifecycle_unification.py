# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "editable_grid_lifecycle_unification_contract.py"
    spec = importlib.util.spec_from_file_location("phase418_editable_grid_lifecycle_unification_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase418_contract_summary_ready():
    module = _load_contract()
    contract = module.EDITABLE_GRID_LIFECYCLE_UNIFICATION_CONTRACT
    assert contract["phase"] == 418
    assert contract["name"] == "editable_grid_lifecycle_unification"
    assert "features.inventory.grids.InventoryTransferLinesModel" in contract["scope"]
    assert any("ensure_single_trailing_empty_line" in item for item in contract["requirements"])
    assert module.editable_grid_lifecycle_unification_summary(ROOT)["ready"] is True


def test_phase418_sources_parse():
    for rel in (
        "alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py",
        "alrajhi_client/features/manufacturing/grids/bom_components_model.py",
        "alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py",
        "alrajhi_client/workspace/quality/editable_grid_lifecycle_unification_contract.py",
        "tools/phase418_editable_grid_lifecycle_unification_guard.py",
    ):
        ast.parse(read(rel))


def test_phase418_qt_free_policy_covers_all_operational_routes():
    spec = importlib.util.spec_from_file_location(
        "unified_grid_navigation_policy_phase418",
        ROOT / "alrajhi_client" / "features" / "transactions" / "grids" / "unified_grid_navigation_policy.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    assert module.semantic_route_for("inventory_transfer") == ("item", "unit", "qty", "notes")
    assert module.semantic_route_for("warehouse_transfer") == ("item", "unit", "qty", "notes")
    assert module.semantic_route_for("bom_components") == ("item", "unit", "qty", "waste_percent", "unit_cost", "total", "notes")
    assert module.semantic_route_for("material_units") == ("unit_name", "conversion_factor", "barcode", "price")

    assert module.visible_semantic_route("inventory_transfer", ("row", "barcode", "item", "unit", "qty", "base_qty", "notes")) == ("item", "unit", "qty", "notes")
    assert module.visible_semantic_route("bom_components", ("item", "unit", "qty", "waste_percent", "unit_cost", "total_cost", "notes")) == ("item", "unit", "qty", "waste_percent", "unit_cost", "total", "notes")
    assert module.route_index_for_key("inventory_transfer", "qty", ("item", "unit", "qty", "notes")) == "notes"
    assert module.route_index_for_key("bom_components", "unit_cost", ("item", "unit", "qty", "waste_percent", "unit_cost", "total_cost", "notes")) == "total"


def test_phase418_inventory_transfer_model_lifecycle_is_idempotent_by_contract():
    source = read("alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py")
    assert "def is_empty_line" in source
    assert "def trim_extra_trailing_empty_lines" in source
    assert "def ensure_single_trailing_empty_line" in source
    assert "def add_empty_line" in source
    assert "return self.ensure_single_trailing_empty_line()" in source
    assert "'qty': Decimal('0')" in source
    assert "'base_qty': Decimal('0')" in source
    assert "not self.is_empty_line(len(self.lines) - 1)" in source


def test_phase418_bom_model_lifecycle_is_idempotent_by_contract():
    source = read("alrajhi_client/features/manufacturing/grids/bom_components_model.py")
    assert "def is_empty_line" in source
    assert "def trim_extra_trailing_empty_lines" in source
    assert "def ensure_single_trailing_empty_line" in source
    assert "def add_empty_line" in source
    assert "return self.ensure_single_trailing_empty_line()" in source
    assert "not self.is_empty_line(len(self.lines) - 1)" in source


def test_phase418_keyboard_policy_routes_inventory_and_bom():
    source = read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "BOM/manufacturing component documents" in source
    assert "Inventory transfers" in source
    assert "waste_percent" in source
    assert "unit_cost" in source
    assert "base_qty" in source
    assert "available" in source
    assert "ensure_callback = getattr(target, \"ensure_single_trailing_empty_line\", None)" in source


def test_phase418_material_units_remain_explicit_user_created_rows():
    source = read("alrajhi_client/features/items/item_editor_tab.py")
    assert "self.add_unit_btn.clicked.connect(self.add_unit_row)" in source
    assert "def add_unit_row" in source
    assert "returnPressed.connect(self.add_unit_row)" not in source
    assert "cellChanged.connect(self.add_unit_row)" not in source


def test_phase418_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase418_editable_grid_lifecycle_unification_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "editable_grid_lifecycle_unification_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase418_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION" in gate
    assert "tests/test_phase418_editable_grid_lifecycle_unification.py" in gate
    assert "tools/phase418_editable_grid_lifecycle_unification_guard.py" in gate
    assert "editable_grid_lifecycle_unification" in gate
    assert "phase=418" in gate
