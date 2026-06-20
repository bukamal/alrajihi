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


def test_runtime_smoke_hooks_cover_all_guarded_scenarios_without_warnings():
    _prepare_client_import_path()
    from workspace.scenarios.scenario_guard_contract import scenario_coverage_summary
    from workspace.scenarios.scenario_runtime_smoke import (
        all_smoke_plans,
        smoke_coverage_summary,
        validate_runtime_smoke_hooks,
    )

    warnings = validate_runtime_smoke_hooks()
    assert warnings == []

    guard_summary = scenario_coverage_summary()
    smoke_summary = smoke_coverage_summary()
    assert smoke_summary["scenario_count"] == guard_summary["scenario_count"]
    assert smoke_summary["check_count"] >= guard_summary["step_count"] * 2
    assert smoke_summary["destructive_count"] == 0
    assert "print_hook" in smoke_summary["check_types"]
    assert "offline_hook" in smoke_summary["check_types"]
    assert "render_print_html" in smoke_summary["callback_names"]

    for plan in all_smoke_plans():
        assert plan.safe_for_ci is True
        assert plan.destructive is False
        assert plan.checks


def test_runtime_smoke_payload_shapes_are_safe_and_business_aware():
    _prepare_client_import_path()
    from workspace.scenarios.scenario_guard_contract import scenario_descriptor_for
    from workspace.scenarios.scenario_runtime_smoke import sample_payload_for_step, smoke_plan_for_scenario

    sales = scenario_descriptor_for("sales_invoice_full_cycle")
    assert sales is not None
    sales_plan = smoke_plan_for_scenario(sales)
    assert any(c.check_key == "route_intent" and c.expected == "/api/invoices" for c in sales_plan.checks)
    payloads = [sample_payload_for_step(step) for step in sales.steps]
    assert any(p.get("currency") == "SYP" for p in payloads)
    assert any("branch_id" in p for p in payloads)

    pos = scenario_descriptor_for("pos_fast_sale_receipt")
    assert pos is not None
    checkout_step = pos.step_for("pos.checkout")
    assert checkout_step is not None
    payload = sample_payload_for_step(checkout_step)
    assert payload["dry_run"] is True
    assert payload["currency"] == "SYP"
    assert payload["branch_id"] == 1


def test_runtime_smoke_dry_runner_passes_static_checks_and_skips_unprovided_callbacks():
    _prepare_client_import_path()
    from workspace.scenarios.scenario_runtime_smoke import run_dry_smoke

    results = run_dry_smoke(scenario_keys=["purchase_return_edit_print", "bom_cost_print", "pos_fast_sale_receipt"])
    assert results
    statuses = {r.status for r in results}
    assert "failed" not in statuses
    assert "passed" in statuses
    assert "skipped" in statuses  # Callback-mode hooks are explicit, not silently passed.
    assert any(r.callback_name == "render_print_html" for r in results if r.status == "skipped")


def test_runtime_smoke_audit_tool_runs_and_writes_csv():
    tool = ROOT / "tools" / "scenario_runtime_smoke_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr

    matrix = ROOT / "tools" / "audit_outputs" / "scenario_runtime_smoke_matrix.csv"
    dry = ROOT / "tools" / "audit_outputs" / "scenario_runtime_smoke_dry_run_results.csv"
    assert matrix.exists()
    assert dry.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "pos_fast_sale_receipt" in content
    assert "bom_cost_print" in content
    assert "render_print_html" in content
    assert "route_intent" in content


def test_phase272_files_are_packaging_safe_and_pyqt_free():
    source = _read("alrajhi_client/workspace/scenarios/scenario_runtime_smoke.py")
    assert "PyQt" not in source
    assert "QWidget" not in source
    assert "ScenarioSmokePlan" in source
    assert "run_dry_smoke" in source
    assert "Idempotency" not in source  # Replay safety remains in Phase 270, not duplicated here.
