# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.full_runtime_acceptance_contract import (
    ACCEPTANCE_DOMAINS,
    MANUAL_ACCEPTANCE_ITEMS,
    runtime_acceptance_issues,
    runtime_acceptance_rows,
    runtime_acceptance_summary,
)


def test_phase345_acceptance_domains_cover_core_business_surfaces():
    domain_keys = {domain.key for domain in ACCEPTANCE_DOMAINS}
    assert {
        "transactions",
        "pos",
        "restaurant",
        "cafe",
        "apparel",
        "inventory_manufacturing_finance",
        "reports_settings_quality",
    }.issubset(domain_keys)
    assert any("sales_invoice_full_cycle" in domain.scenario_keys for domain in ACCEPTANCE_DOMAINS)
    assert any("restaurant_table_order_checkout" in domain.scenario_keys for domain in ACCEPTANCE_DOMAINS)
    assert any("apparel.variant_labels" in domain.barcode_profiles for domain in ACCEPTANCE_DOMAINS)


def test_phase345_runtime_acceptance_matrix_has_no_required_automated_issues():
    rows = runtime_acceptance_rows(ROOT, include_manual=True)
    assert rows
    assert runtime_acceptance_issues(rows) == {}
    status_counts = {row.status for row in rows}
    assert "pass" in status_counts
    assert "manual_required" in status_counts
    assert all(row.status != "fail" for row in rows if row.required)


def test_phase345_manual_acceptance_items_are_explicit_not_hidden_failures():
    assert len(MANUAL_ACCEPTANCE_ITEMS) >= 5
    assert all(row.status == "manual_required" for row in MANUAL_ACCEPTANCE_ITEMS)
    assert all(row.required is False for row in MANUAL_ACCEPTANCE_ITEMS)
    keys = {row.key for row in MANUAL_ACCEPTANCE_ITEMS}
    assert "manual_windows_exe_launch" in keys
    assert "manual_barcode_printer" in keys
    assert "manual_remote_api_multi_user" in keys
    assert "manual_backup_restore_upgrade" in keys


def test_phase345_summary_separates_automated_from_manual_checks():
    summary = runtime_acceptance_summary(ROOT)
    assert summary["phase"] == 345
    assert summary["automated_checks"] > 0
    assert summary["manual_checks"] == len(MANUAL_ACCEPTANCE_ITEMS)
    assert summary["issue_groups"] == 0
    assert summary["ready_for_manual_hardware_pass"] is True


def test_phase345_guard_and_release_registration_exist():
    guard = ROOT / "tools/phase345_full_runtime_acceptance_packaging_smoke.py"
    doc = ROOT / "PHASE345_FULL_RUNTIME_ACCEPTANCE_PACKAGING_SMOKE.md"
    release_gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert guard.exists()
    assert doc.exists()
    assert "full_runtime_acceptance_packaging_smoke" in release_gate
    assert "FULL_RUNTIME_ACCEPTANCE_PACKAGING_SMOKE" in release_gate
