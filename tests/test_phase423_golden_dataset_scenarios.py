# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase423_contract_summary_ready():
    module = load_module("alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py", "phase423_contract")
    summary = module.contract_summary()
    assert summary["phase"] == 423
    assert summary["currency"] == "SYP"
    assert summary["scenario_group_count"] >= 12
    assert summary["critical_invariant_count"] >= 8


def test_phase423_operations_cover_all_business_surfaces():
    from workspace.quality.golden_dataset_scenarios import build_golden_operations
    from workspace.quality.golden_dataset_scenarios_contract import required_scenario_groups

    operations = build_golden_operations()
    assert len(operations) == 14
    groups = {op.group for op in operations}
    assert set(required_scenario_groups()).issubset(groups)
    assert len({op.operation_id for op in operations}) == len(operations)
    assert all(op.operation_id.startswith("GD-") for op in operations)
    assert all(op.branch_id for op in operations)


def test_phase423_expected_balances_are_stable():
    from workspace.quality.golden_dataset_scenarios import calculate_golden_expected, build_golden_operations

    expected = calculate_golden_expected(build_golden_operations())
    assert expected["currency"] == "SYP"
    assert expected["stock_by_item_warehouse"] == {
        "MAT-FINISHED@WH-MAIN": "1.0000",
        "MAT-RAW@WH-MAIN": "10.0000",
        "MAT-RETAIL@WH-BR2": "1.0000",
        "MAT-RETAIL@WH-MAIN": "3.0000",
    }
    assert expected["cashbox_balances"] == {
        "CASH-MAIN": "850.00",
        "CASH-POS": "183.75",
        "CASH-REST": "252.00",
    }
    assert expected["totals"]["gross_profit"] == "465.00"
    assert expected["totals"]["vat_payable"] == "-20.75"
    assert expected["totals"]["stock_movement_count"] == "13"


def test_phase423_invariants_pass_without_runtime_database():
    from workspace.quality.golden_dataset_scenarios import build_invariant_rows, failures, scenario_summary

    rows = build_invariant_rows()
    assert len(rows) >= 30
    assert not failures(rows)
    summary = scenario_summary()
    assert summary["failures"] == 0
    assert summary["gross_profit"] == "465.00"


def test_phase423_guard_generates_matrix_and_release_gate_registered():
    result = subprocess.run([sys.executable, "tools/phase423_golden_dataset_scenarios_guard.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/golden_dataset_scenarios_matrix.csv"
    expected = ROOT / "tools/audit_outputs/golden_dataset_expected_balances.json"
    operations = ROOT / "tools/audit_outputs/golden_dataset_operations.json"
    assert matrix.exists()
    assert expected.exists()
    assert operations.exists()
    with matrix.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 40
    assert all(row["status"] == "OK" for row in rows)
    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert "PHASE423_GOLDEN_DATASET_ACCOUNTING_INVENTORY_SCENARIO_PACK" in gate
    assert "tools/phase423_golden_dataset_scenarios_guard.py" in gate
    assert "tests/test_phase423_golden_dataset_scenarios.py" in gate
