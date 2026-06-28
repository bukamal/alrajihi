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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "unified_sales_invoice_grid_runtime_contract.py"
    spec = importlib.util.spec_from_file_location("phase415_unified_sales_invoice_grid_runtime_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase415_contract_documents_clean_runtime_scope():
    module = _load_contract()
    contract = module.UNIFIED_SALES_INVOICE_GRID_RUNTIME_CONTRACT
    assert contract["phase"] == 415
    assert contract["name"] == "unified_sales_invoice_grid_runtime"
    assert "features.transactions.grids.TransactionLineGrid" in contract["scope"]
    assert any("AnyKeyPressed" in item for item in contract["requirements"])
    assert module.unified_sales_invoice_grid_runtime_summary(ROOT)["ready"] is True


def test_phase415_sources_parse():
    for rel in (
        "alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py",
        "alrajhi_client/features/transactions/grids/transaction_line_grid.py",
        "alrajhi_client/features/transactions/grids/transaction_line_model.py",
        "alrajhi_client/ui/table_keyboard_policy.py",
        "tools/phase415_unified_sales_invoice_grid_runtime_guard.py",
    ):
        ast.parse(read(rel))


def test_phase415_qt_free_policy_route_and_tail_lifecycle():
    spec = importlib.util.spec_from_file_location(
        "unified_grid_navigation_policy",
        ROOT / "alrajhi_client" / "features" / "transactions" / "grids" / "unified_grid_navigation_policy.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    SALES_INVOICE_ROUTE = module.SALES_INVOICE_ROUTE
    visible_semantic_route = module.visible_semantic_route
    route_index_for_key = module.route_index_for_key
    is_empty_transaction_line = module.is_empty_transaction_line
    ensure_single_trailing_empty_line = module.ensure_single_trailing_empty_line
    trailing_empty_line_count = module.trailing_empty_line_count

    assert SALES_INVOICE_ROUTE == ("item", "unit", "qty", "price", "discount", "tax", "total", "notes")
    visible = ("row", "barcode", "item", "unit", "qty", "price", "total", "notes")
    assert visible_semantic_route("sales_invoice", visible) == ("item", "unit", "qty", "price", "total", "notes")
    assert route_index_for_key("sales_invoice", "item", visible) == "unit"
    assert route_index_for_key("sales_invoice", "barcode", visible) == "unit"
    assert route_index_for_key("sales_invoice", "qty", visible) == "price"
    assert route_index_for_key("sales_invoice", "unit", visible, forward=False) == "item"

    blank = {"item_id": None, "item": "", "barcode": "", "qty": "0", "price": "0.00", "total": "0"}
    real = {"item_id": 7, "item": "Tea", "barcode": "T-1", "qty": "1"}
    assert is_empty_transaction_line(blank) is True
    assert is_empty_transaction_line(real) is False

    lines = [real.copy(), blank.copy(), blank.copy()]
    idx = ensure_single_trailing_empty_line(lines, lambda: blank.copy())
    assert idx == 1
    assert len(lines) == 2
    assert trailing_empty_line_count(lines) == 1
    idx2 = ensure_single_trailing_empty_line(lines, lambda: blank.copy())
    assert idx2 == 1
    assert len(lines) == 2


def test_phase415_grid_edit_hook_installs_enter_filter_for_real_editor_paths():
    grid = read("alrajhi_client/features/transactions/grids/transaction_line_grid.py")
    assert "def edit(self, index, trigger=None, event=None)" in grid
    assert "AnyKeyPressed" in grid
    assert "double click" in grid
    assert "programmatic" in grid
    assert "_standard_prepare_active_editor" in grid
    assert "QTimer.singleShot(0" in grid


def test_phase415_model_owns_idempotent_row_lifecycle():
    model = read("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    assert "document_type: str = \"sales_invoice\"" in model
    assert "def is_empty_line" in model
    assert "def trim_extra_trailing_empty_lines" in model
    assert "def ensure_single_trailing_empty_line" in model
    assert "def add_empty_line" in model
    assert "return self.ensure_single_trailing_empty_line()" in model
    assert model.count("self.ensure_single_trailing_empty_line()") >= 4


def test_phase415_keyboard_delegates_append_to_model_gate():
    keyboard = read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "ensure_callback = getattr(target, \"ensure_single_trailing_empty_line\", None)" in keyboard
    assert "trim_callback = getattr(target, \"trim_extra_trailing_empty_lines\", None)" in keyboard
    assert "_standard_enter_append_guard" in keyboard


def test_phase415_transaction_tab_passes_document_type_to_model():
    tab = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert "TransactionLineModel(self.columns, self, document_type=self.context.document_type)" in tab


def test_phase415_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase415_unified_sales_invoice_grid_runtime_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "unified_sales_invoice_grid_runtime_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase415_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE415_UNIFIED_SALES_INVOICE_GRID_RUNTIME" in gate
    assert "tests/test_phase415_unified_sales_invoice_grid_runtime.py" in gate
    assert "tools/phase415_unified_sales_invoice_grid_runtime_guard.py" in gate
    assert "unified_sales_invoice_grid_runtime" in gate
    assert "phase=415" in gate
