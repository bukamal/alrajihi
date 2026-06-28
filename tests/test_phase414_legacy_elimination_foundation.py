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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "legacy_elimination_contract.py"
    spec = importlib.util.spec_from_file_location("phase414_legacy_elimination_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase414_contract_documents_legacy_elimination_foundation():
    module = _load_contract()
    contract = module.LEGACY_ELIMINATION_CONTRACT
    assert contract["phase"] == 414
    assert contract["name"] == "legacy_elimination_foundation"
    assert "views.main_window shell navigation" in contract["scope"]
    assert any("CleanShellNavigationBar" in item for item in contract["requirements"])


def test_main_window_uses_clean_shell_without_hidden_topbar_widgets():
    src = read("alrajhi_client/views/main_window.py")
    assert "class CleanShellNavigationBar(QFrame)" in src
    assert "self.menu_bar = CleanShellNavigationBar(self)" in src
    assert "self.top_bar = ShellCompatibilityAdapter()" in src
    assert "main_layout.addWidget(self.top_bar)" not in src
    assert "from views.modern_topbar import" not in src
    assert "ModernTopBar(" not in src
    assert "class IconMenuBar" not in src
    assert "self.menu_bar = IconMenuBar" not in src


def test_shell_navigation_has_no_native_menu_subcontrols():
    src = read("alrajhi_client/views/main_window.py")
    qss = read("alrajhi_client/theme/qss.py")
    assert "button = QPushButton(self)" in src
    assert "menu.popup(button.mapToGlobal" in src
    assert "QFrame#CleanShellNavigationBar" in src
    assert "QPushButton#MainNavButton" in src
    assert "QFrame#CleanShellNavigationBar" in qss
    assert "QPushButton#MainNavButton" in qss
    assert "QToolButton#MainNavToolButton" not in src
    assert "QToolButton#MainNavToolButton" not in qss
    assert "btn.setMenu(menu)" not in src
    assert "QToolButton.InstantPopup" not in src


def test_legacy_transaction_routes_are_hard_disabled():
    main = read("alrajhi_client/views/main_window.py")
    flags = read("alrajhi_client/features/transactions/feature_flags.py")
    invoice_pkg = read("alrajhi_client/features/invoices/__init__.py")
    returns_pkg = read("alrajhi_client/features/returns/__init__.py")
    assert "Legacy invoice dialog is disabled by Phase414" in main
    assert "Legacy return dialog is disabled by Phase414" in main
    assert "from features.invoices import InvoiceEditorTab" not in main
    assert "ReturnEditorTab =" not in main
    assert "LEGACY_TRANSACTION_DOCUMENTS_DISABLED = True" in flags
    assert "def allow_legacy_transaction_documents" in flags
    assert "return False" in flags
    assert "__all__: list[str] = []" in invoice_pkg
    assert "__all__: list[str] = []" in returns_pkg
    assert "InvoiceEditorTab" not in invoice_pkg
    assert "SalesReturnEditorTab" not in returns_pkg


def test_phase414_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase414_legacy_elimination_foundation_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "legacy_elimination_foundation_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase414_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE414_LEGACY_ELIMINATION_FOUNDATION" in gate
    assert "tests/test_phase414_legacy_elimination_foundation.py" in gate
    assert "tools/phase414_legacy_elimination_foundation_guard.py" in gate
    assert "legacy_elimination_foundation" in gate
    assert "phase=414" in gate
