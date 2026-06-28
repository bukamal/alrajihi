# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "legacy_transaction_quarantine_contract.py"
    spec = importlib.util.spec_from_file_location("phase417_legacy_transaction_quarantine_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase417_contract_declares_quarantined_legacy_transaction_modules():
    module = _load_contract()
    contract = module.LEGACY_TRANSACTION_QUARANTINE_CONTRACT
    assert contract["phase"] == 417
    assert contract["name"] == "legacy_transaction_quarantine"
    assert "features.invoices.invoice_editor_tab" in contract["quarantined_modules"]
    assert "features.returns.return_editor_tabs" in contract["quarantined_modules"]
    assert "ALRAJHI_FORENSIC_ALLOW_LEGACY_TRANSACTION_IMPORT" == contract["forensic_only_env"]


def test_legacy_quarantine_module_is_pyqt_free_and_explicit():
    src = read("alrajhi_client/workspace/quality/legacy_transaction_quarantine.py")
    assert "class LegacyTransactionQuarantineError" in src
    assert "QUARANTINED_TRANSACTION_MODULES" in src
    assert "assert_not_quarantined_transaction_module" in src
    assert "scan_text_for_forbidden_legacy_imports" in src
    assert "PyQt5" not in src


def test_legacy_adapters_fail_before_loading_old_dialog_code():
    invoice = read("alrajhi_client/features/invoices/invoice_editor_tab.py")
    returns = read("alrajhi_client/features/returns/return_editor_tabs.py")
    assert "QUARANTINED_LEGACY_TRANSACTION_MODULE = True" in invoice
    assert invoice.index("assert_not_quarantined_transaction_module(__name__)") < invoice.index("from views.dialogs.invoice_dialog import InvoiceDialog")
    assert "QUARANTINED_LEGACY_TRANSACTION_MODULE = True" in returns
    assert returns.index("assert_not_quarantined_transaction_module(__name__)") < returns.index("from PyQt5.QtCore import")


def test_main_window_has_no_legacy_transaction_fallback_imports():
    src = read("alrajhi_client/views/main_window.py")
    assert "from features.invoices import InvoiceEditorTab" not in src
    assert "from features.invoices.invoice_editor_tab import" not in src
    assert "from features.returns import SalesReturnEditorTab" not in src
    assert "from features.returns import PurchaseReturnEditorTab" not in src
    assert "from features.returns.return_editor_tabs import" not in src
    assert "allow_legacy_transaction_documents," not in src
    assert "legacy_allowed = allow_legacy_transaction_documents" not in src
    assert "Legacy invoice dialog is disabled by Phase414 and quarantined by Phase417" in src
    assert "Legacy return dialog is disabled by Phase414 and quarantined by Phase417" in src


def test_legacy_flag_remains_hard_false_but_not_a_navigation_fallback():
    flags = read("alrajhi_client/features/transactions/feature_flags.py")
    assert "LEGACY_TRANSACTION_DOCUMENTS_DISABLED = True" in flags
    assert "def allow_legacy_transaction_documents" in flags
    assert "return False" in flags
    assert "Phase417 also quarantines direct imports" in flags


def test_phase417_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase417_legacy_transaction_quarantine_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "legacy_transaction_quarantine_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase417_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE417_LEGACY_TRANSACTION_QUARANTINE" in gate
    assert "tests/test_phase417_legacy_transaction_quarantine.py" in gate
    assert "tools/phase417_legacy_transaction_quarantine_guard.py" in gate
    assert "legacy_transaction_quarantine" in gate
    assert "phase=417" in gate
