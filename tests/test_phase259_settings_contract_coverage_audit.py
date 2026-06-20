# -*- coding: utf-8 -*-
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _prepare_client_import_path():
    client = ROOT / "alrajhi_client"
    if str(client) not in sys.path:
        sys.path.insert(0, str(client))
    existing = sys.modules.get("workspace")
    if existing is not None and not hasattr(existing, "__path__"):
        sys.modules.pop("workspace", None)


def test_settings_contract_covers_all_shell_scopes():
    _prepare_client_import_path()

    from workspace.settings.settings_contract import (
        collect_shell_settings_scopes,
        settings_descriptor_for,
        uncovered_settings_scopes,
        validate_settings_scope_descriptors,
    )

    scopes = set(collect_shell_settings_scopes())
    assert {"transactions.sales_invoice", "materials", "reports", "pos", "restaurant"}.issubset(scopes)
    assert uncovered_settings_scopes(scopes) == ()
    assert validate_settings_scope_descriptors() == {}
    assert settings_descriptor_for("transactions.sales_return.list").scope == "transactions"
    assert settings_descriptor_for("finance.vouchers").service_getter == "get_finance_settings"


def test_settings_contract_declares_network_language_currency_and_printing():
    _prepare_client_import_path()

    from workspace.settings.settings_contract import settings_descriptor_for

    transactions = settings_descriptor_for("transactions.purchase_invoice")
    assert transactions.api_resource == "/api/settings/<path:key>"
    assert transactions.network_mode == "remote_available"
    assert "language/print" in transactions.language_keys
    assert "display_currency" in transactions.currency_keys
    assert "printing/invoice_template" in transactions.print_keys

    reports = settings_descriptor_for("reports")
    assert reports.service_getter == "get_report_settings"
    assert "reports/operations" in reports.operation_key_prefixes
    assert "language/report" in reports.required_keys

    pos = settings_descriptor_for("pos")
    assert "pos" in pos.ui_sections
    assert "pos/operations" in pos.operation_key_prefixes


def test_settings_tabs_include_contract_sections():
    text = (ROOT / "alrajhi_client/features/settings/settings_document_tabs.py").read_text(encoding="utf-8")
    for section in (
        "transactions",
        "materials",
        "parties",
        "finance",
        "branches",
        "manufacturing",
        "reports",
        "pos",
        "restaurant",
        "users",
    ):
        assert f"'{section}':" in text
    assert "language/report" in text
    assert "pos/operations/allow_checkout" in text
    assert "materials/barcode/default_symbology" in text


def test_settings_contract_audit_tool_runs_and_writes_matrix():
    tool = ROOT / "tools" / "settings_contract_coverage_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools" / "audit_outputs" / "settings_contract_coverage_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "transactions.sales_invoice" in content
    assert "reports" in content
    assert "restaurant" in content


def test_settings_service_exposes_contract_coverage_source():
    text = (ROOT / "alrajhi_client/core/services/settings_service.py").read_text(encoding="utf-8")
    assert "def settings_contract_coverage" in text
    assert "settings_coverage_matrix" in text
    assert "uncovered_settings_scopes" in text
