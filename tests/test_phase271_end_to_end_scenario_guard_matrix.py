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


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_end_to_end_scenario_contract_has_core_business_paths_and_no_warnings():
    _prepare_client_import_path()
    from workspace.scenarios.scenario_guard_contract import (
        all_scenario_descriptors,
        scenario_coverage_summary,
        scenario_descriptor_for,
        validate_scenario_descriptors,
    )

    warnings = validate_scenario_descriptors()
    assert warnings == []

    keys = {s.scenario_key for s in all_scenario_descriptors()}
    assert {
        "sales_invoice_full_cycle",
        "purchase_invoice_full_cycle",
        "sales_return_edit_print",
        "purchase_return_edit_print",
        "pos_fast_sale_receipt",
        "restaurant_table_order_checkout",
        "bom_cost_print",
        "production_order_lifecycle",
        "inventory_transfer_print",
        "voucher_cash_bank_flow",
        "material_barcode_lookup_label",
        "report_income_statement_print_export",
    }.issubset(keys)

    summary = scenario_coverage_summary()
    assert summary["scenario_count"] >= 12
    assert summary["step_count"] >= 30
    assert "document" in summary["surfaces"]
    assert "list" in summary["surfaces"]
    assert "report" in summary["surfaces"]
    assert "operational" in summary["surfaces"]

    pos = scenario_descriptor_for("pos_fast_sale_receipt")
    assert pos is not None
    assert pos.currency_sensitive is True
    assert pos.print_sensitive is True
    assert pos.offline_sensitive is True


def test_scenario_steps_are_linked_to_rbac_audit_offline_and_settings_contracts():
    _prepare_client_import_path()
    from workspace.audit.audit_contract import audit_event_descriptor_for
    from workspace.scenarios.scenario_guard_contract import (
        EXPECT_AUDIT,
        EXPECT_OFFLINE,
        EXPECT_RBAC,
        EXPECT_SETTINGS,
        all_scenario_descriptors,
    )
    from workspace.security.rbac_contract import permission_descriptor_map
    from workspace.settings.settings_contract import settings_descriptor_for
    from workspace.sync.offline_sync_contract import offline_descriptor_for

    rbac = permission_descriptor_map()
    for scenario in all_scenario_descriptors():
        assert settings_descriptor_for(scenario.settings_scope) is not None, scenario.scenario_key
        for step in scenario.steps:
            if EXPECT_RBAC in step.expects:
                assert step.permission_key in rbac, (scenario.scenario_key, step.key, step.permission_key)
            if EXPECT_AUDIT in step.expects:
                assert audit_event_descriptor_for(step.audit_event_key) is not None, (scenario.scenario_key, step.key, step.audit_event_key)
            if EXPECT_OFFLINE in step.expects:
                assert offline_descriptor_for(step.offline_surface_key) is not None, (scenario.scenario_key, step.key, step.offline_surface_key)
            if EXPECT_SETTINGS in step.expects:
                assert step.api_resource or step.surface == "report"


def test_scenario_guard_audit_tool_runs_and_writes_csv():
    tool = ROOT / "tools" / "end_to_end_scenario_guard_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr

    matrix = ROOT / "tools" / "audit_outputs" / "end_to_end_scenario_guard_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "sales_invoice_full_cycle" in content
    assert "purchase_return_edit_print" in content
    assert "pos_fast_sale_receipt" in content
    assert "bom_cost_print" in content
    assert "EXPECT" not in content  # CSV should contain concrete expectation names without Python symbols.


def test_phase271_files_are_packaging_safe_and_pyqt_free():
    source = _read("alrajhi_client/workspace/scenarios/scenario_guard_contract.py")
    assert "PyQt" not in source
    assert "from workspace.documents.document_contract" in source
    assert "from workspace.sync.offline_sync_contract" in source
    assert "SCENARIO_GUARD_DESCRIPTORS" in source
