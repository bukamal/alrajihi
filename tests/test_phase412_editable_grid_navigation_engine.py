# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "editable_grid_navigation_engine_contract.py"
    spec = importlib.util.spec_from_file_location("phase412_editable_grid_navigation_engine_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _function_body(src: str, name: str) -> str:
    match = re.search(rf"def {re.escape(name)}\(.*?\n    def ", src, flags=re.S)
    assert match, name
    return match.group(0)


def test_phase412_contract_documents_navigation_engine():
    module = _load_contract()
    contract = module.EDITABLE_GRID_NAVIGATION_ENGINE_CONTRACT
    assert contract["phase"] == 412
    assert contract["name"] == "editable_grid_navigation_engine"
    assert "TransactionLineGrid" in contract["scope"]
    assert any("trailing empty line" in item or "exactly one row" in item for item in contract["requirements"])
    assert "tools/audit_outputs/editable_grid_navigation_engine_matrix.csv" in contract["required_outputs"]
    assert module.editable_grid_navigation_engine_summary(ROOT)["ready"] is True


def test_phase412_sources_parse_and_core_engine_markers_exist():
    files = [
        "alrajhi_client/ui/table_keyboard_policy.py",
        "alrajhi_client/views/dialogs/invoice_dialog.py",
        "alrajhi_client/views/dialogs/invoice_delegates.py",
        "alrajhi_client/features/transactions/grids/transaction_item_delegate.py",
        "tools/phase412_editable_grid_navigation_engine_guard.py",
    ]
    for rel in files:
        ast.parse(read(rel))
    policy = read("alrajhi_client/ui/table_keyboard_policy.py")
    for marker in (
        "def _standard_ensure_single_trailing_empty_line",
        "def _standard_row_is_empty_for_append",
        "def _standard_trim_extra_trailing_empty_lines",
        "_standard_enter_navigation_active",
        "_standard_enter_append_guard",
    ):
        assert marker in policy


def test_phase412_all_enter_append_sites_use_idempotent_gate():
    policy = read("alrajhi_client/ui/table_keyboard_policy.py")
    route = _function_body(policy, "_standard_next_business_route_index")
    generic = _function_body(policy, "_standard_next_index")
    assert "_standard_ensure_single_trailing_empty_line()" in route
    assert "_standard_ensure_single_trailing_empty_line()" in generic
    # Older direct append remains only as a compatibility wrapper, not in route bodies.
    assert "_standard_append_empty_line_if_supported()" not in route
    assert "_standard_append_empty_line_if_supported()" not in generic


def test_phase412_semantic_routes_cover_returns_inventory_and_bom():
    policy = read("alrajhi_client/ui/table_keyboard_policy.py")
    route_body = _function_body(policy, "_standard_business_route_slots")
    assert "Return documents: material -> unit -> returned qty" in route_body
    assert "Inventory transfers: material -> unit -> qty -> notes" in route_body
    assert "BOM/manufacturing component documents" in route_body
    assert '("reason",)' in route_body
    assert '("restock",)' in route_body
    assert '("waste_percent",)' in route_body
    assert '("unit_cost", "cost")' in route_body
    assert 'return [item_slot, unit_slot, qty_slot, ("notes",)]' in route_body


def test_phase412_legacy_invoice_eventfilter_defers_enter_to_grid_engine():
    invoice = read("alrajhi_client/views/dialogs/invoice_dialog.py")
    event_body = invoice[invoice.index("def eventFilter") : invoice.index("def _move_to_next_invoice_cell")]
    assert "_move_to_next_invoice_cell()" not in event_body
    assert "Phase412: Enter traversal is owned by TransactionLineGrid" in event_body
    assert "key in (Qt.Key_Return, Qt.Key_Enter)" in event_body
    assert "return False" in event_body
    # Keep the legacy helper only for compatibility; it must no longer be called by Enter filter.
    assert "def _move_to_next_invoice_cell" in invoice


def test_phase412_delegates_do_not_clear_or_commit_during_loading():
    item_delegate = read("alrajhi_client/features/transactions/grids/transaction_item_delegate.py")
    assert "_transaction_item_user_edited" in item_delegate
    assert "Enter navigation must never wipe an existing item" in item_delegate
    assert "if not user_edited and previous not in (None, \"\")" in item_delegate

    delegates = read("alrajhi_client/views/dialogs/invoice_delegates.py")
    assert "currentIndexChanged.connect(lambda: self.commitData.emit(combo))" not in delegates
    assert "combo.activated.connect" in delegates


def test_phase412_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase412_editable_grid_navigation_engine_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "editable_grid_navigation_engine_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase412_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE412_EDITABLE_GRID_NAVIGATION_ENGINE" in gate
    assert "tests/test_phase412_editable_grid_navigation_engine.py" in gate
    assert "tools/phase412_editable_grid_navigation_engine_guard.py" in gate
    assert "editable_grid_navigation_engine" in gate
    assert "phase=412" in gate
