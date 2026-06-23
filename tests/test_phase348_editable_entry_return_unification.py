# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.editable_entry_return_unification_contract import phase348_checks, phase348_issues


def test_phase348_contract_has_no_issues():
    issues = phase348_issues(ROOT)
    assert not issues, [issue.code for issue in issues]


def test_phase348_keyboard_policy_focuses_item_and_prepares_editor_text():
    text = (ROOT / "alrajhi_client/ui/table_keyboard_policy.py").read_text(encoding="utf-8")
    assert "focus_entry_column" in text
    assert "_standard_preferred_entry_keys" in text
    assert "_standard_prepare_active_editor" in text
    assert "editor.clear()" in text


def test_phase348_returns_are_editable_like_transactions():
    doc = (ROOT / "alrajhi_client/features/transactions/transaction_document_tab.py").read_text(encoding="utf-8")
    schema = (ROOT / "alrajhi_client/features/transactions/grids/transaction_column_schema.py").read_text(encoding="utf-8")
    assert "self.search_input.setEnabled(True)" in doc
    assert "manual_return" in doc
    assert '("transaction_add_line_insert", self._add_empty_line_from_ui)' in doc
    assert schema.count('TransactionColumn("item", "transaction_column_item", True, True, True, 260, True)') >= 3


def test_phase348_local_gateways_support_manual_returns():
    sales = (ROOT / "alrajhi_client/gateways/local/sales_return_gateway.py").read_text(encoding="utf-8")
    purchase = (ROOT / "alrajhi_client/gateways/local/purchase_return_gateway.py").read_text(encoding="utf-8")
    assert "_create_manual_return" in sales
    assert "_ensure_manual_return_schema" in sales
    assert "_create_manual_return" in purchase
    assert "_ensure_manual_return_schema" in purchase


def test_phase348_guard_script_runs():
    result = subprocess.run(
        [sys.executable, "tools/phase348_editable_entry_return_unification_guard.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_phase348_release_registration_exists():
    release = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert '(348, "EDITABLE_ENTRY_RETURN_UNIFICATION")' in release
    assert '(348, "editable_entry_return_unification")' in release
    assert "phase348_editable_entry_return_unification_guard.py" in release
